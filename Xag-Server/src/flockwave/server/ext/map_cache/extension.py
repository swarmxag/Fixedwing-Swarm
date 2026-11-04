"""Map tile cache for Skybrush Live.

Live checks whether this extension is loaded (under the name ``map_cache``),
and if the operator switched on "Use cached map tiles" in Toolbox -> Offline
maps, it requests every tile from
``<server>/map_cache/{z}/{x}/{y}.png?type=<source>&apiKey=<key>`` (see
SOURCE_URLS) instead of from the map provider directly;
``<server>/map_cache/_?url=<tile URL>`` takes a full provider URL instead. This extension downloads the tile
on first use, keeps a copy on disk, and serves later requests from that copy.
Tiles that were seen once while the server was online therefore still show up
when the server has no internet access.

The endpoint downloads a URL given by the client, so it only talks to a fixed
list of map tile providers; it is not an open proxy.
"""

from __future__ import annotations

import os
from fnmatch import fnmatchcase
from logging import Logger
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from pathlib import Path

import httpx
from quart import Response, request
from trio import sleep_forever, to_thread

from flockwave.server.ext.http_server import HTTPServerExtensionAPI
from flockwave.server.utils.quart import make_blueprint

from .schema import schema as schema  # noqa: F401 (picked up by the loader)
from .store import TileStore

__all__ = ("dependencies", "description", "run", "schema")

dependencies = ("http_server",)
description = "Caches map tiles on the server so that Live can show them offline"

DEFAULT_ALLOWED_HOSTS = (
    "api.mapbox.com",
    "*.tiles.mapbox.com",
    "api.maptiler.com",
    "tile.nextzen.org",
    "tile.skybrush.io",
    "*.tile.skybrush.io",  # the GCS's OSM source, {a-c}.tile.skybrush.io
    "tile.openstreetmap.org",
    "*.tile.openstreetmap.org",
    "tiles.stadiamaps.com",
    "dev.virtualearth.net",
    "*.tiles.virtualearth.net",
    "*.google.com",
    "*.googleapis.com",
)

# Query parameters that carry credentials. They are left out of the cache key
# (so the same tile is a cache hit no matter whose key requested it) and are
# never written to disk or to the log.
SECRET_PARAMS = frozenset({"access_token", "key", "api_key", "apikey", "token"})

MAX_TILE_BYTES = 10 * 1024 * 1024
FETCH_TIMEOUT = 15.0

# Provider tile URLs for the GCS's own request format,
# <route>/{z}/{x}/{y}.png?type=<base layer source>&apiKey=<key>, keyed by the
# GCS source id (GCS-live/src/model/sources.ts). Keep them identical to the
# URLs in GCS-live/src/views/map/layers/base.jsx, so a tile is cached under the
# same key whichever way it is requested.
SOURCE_URLS = {
    "mapbox.static": "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/512/{z}/{x}/{y}@2x?access_token={key}",
    "mapbox.satellite": "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.jpg90?access_token={key}",
    "mapbox.satellite-streets": "https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/256/{z}/{x}/{y}?access_token={key}",
    "maptiler.basic": "https://api.maptiler.com/maps/basic/{z}/{x}/{y}@2x.png?key={key}",
    "maptiler.hybrid": "https://api.maptiler.com/maps/hybrid/{z}/{x}/{y}@2x.jpg?key={key}",
    "maptiler.satellite": "https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key={key}",
    "maptiler.streets": "https://api.maptiler.com/maps/streets/{z}/{x}/{y}@2x.png?key={key}",
    "osm": "https://a.tile.skybrush.io/osm/{z}/{x}/{y}.png",
    "googleMaps.default": "https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
    "googleMaps.satellite": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    "stamen.terrain": "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
    "stamen.toner": "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png",
    "stamen.watercolor": "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg",
}


def source_tile_url(source: str, z: int, x: int, y: int, api_key: str) -> str:
    """Returns the provider URL of a tile requested in the GCS's format;
    raises RejectedURL for an unknown source or a missing key."""
    template = SOURCE_URLS.get(source)
    if template is None:
        raise RejectedURL(f"unsupported map source {source!r}")
    # The GCS sends the literal "undefined" for sources without a key
    key = "" if api_key in ("", "undefined", "null") else api_key
    if "{key}" in template and not key:
        raise RejectedURL(f"map source {source!r} needs an API key")
    return template.format(z=z, x=x, y=y, key=key)


class RejectedURL(ValueError):
    pass


def check_url(url: str, allowed_hosts: tuple[str, ...]):
    """Validates a tile URL requested by a client.

    Returns:
        the parsed URL; raises RejectedURL if it must not be fetched
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise RejectedURL("only http(s) tile URLs are supported")
    if parts.username or parts.password:
        raise RejectedURL("credentials in the URL are not allowed")

    host = parts.hostname.lower()
    if not any(fnmatchcase(host, pattern.lower()) for pattern in allowed_hosts):
        raise RejectedURL(f"host {host!r} is not an allowed tile provider")

    return parts


def cache_key_url(url: str) -> str:
    """Returns the URL with credentials removed and the query sorted, so that
    equivalent requests share one cache entry."""
    parts = urlsplit(url)
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in SECRET_PARAMS
    )
    return urlunsplit(
        (parts.scheme, parts.netloc.lower(), parts.path, urlencode(query), "")
    )


def with_server_token(url: str, token: str) -> str:
    """Replaces the Mapbox access token in the URL with the server's token."""
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if not token or not (host == "api.mapbox.com" or host.endswith(".mapbox.com")):
        return url

    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() != "access_token"
    ]
    query.append(("access_token", token))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


def _tile_response(data: bytes, content_type: str, source: str) -> Response:
    return Response(
        data,
        content_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            # Live loads tiles with a cross-origin <img>, so allow it
            "Access-Control-Allow-Origin": "*",
            "X-Map-Cache": source,
        },
    )


def _error(status: int, message: str) -> Response:
    return Response(
        message,
        status=status,
        content_type="text/plain",
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def run(app, configuration, logger: Logger):
    token = str(
        configuration.get("mapbox_access_token")
        or os.environ.get("MAPBOX_ACCESS_TOKEN", "")
    ).strip()
    max_size_mb = float(configuration.get("max_size_mb", 2048))
    max_age = float(configuration.get("max_age_days", 30)) * 86400
    allowed_hosts = tuple(configuration.get("allowed_hosts") or DEFAULT_ALLOWED_HOSTS)
    # The GCS requests tiles from <server>:5000/map_cache/...
    route = configuration.get("route") or "/map_cache"

    # app.dirs is appdirs.AppDirs here, whose user_cache_dir is a str
    cache_dir = Path(app.dirs.user_cache_dir) / "ext" / "map_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    store = TileStore(cache_dir, max_bytes=int(max_size_mb * 1024 * 1024))

    blueprint = make_blueprint("map_cache", __name__)

    @blueprint.route("/_")
    async def get_tile():
        return await serve_tile(request.args.get("url", ""))

    @blueprint.route("/<int:z>/<int:x>/<int:y>.png")
    async def get_source_tile(z: int, x: int, y: int):
        # The request format the GCS uses (see SOURCE_URLS)
        try:
            url = source_tile_url(
                request.args.get("type", ""), z, x, y, request.args.get("apiKey", "")
            )
        except RejectedURL as ex:
            return _error(400, str(ex))
        return await serve_tile(url)

    async def serve_tile(url: str) -> Response:
        try:
            check_url(url, allowed_hosts)
        except RejectedURL as ex:
            return _error(400, str(ex))

        key = TileStore.key_for(cache_key_url(url))
        cached = await to_thread.run_sync(store.get, key)
        if cached is not None and cached.age() <= max_age:
            return _tile_response(cached.data, cached.content_type, "hit")

        try:
            response = await client.get(with_server_token(url, token))
        except httpx.HTTPError as ex:
            # Offline or provider unreachable: an old tile beats no tile
            if cached is not None:
                return _tile_response(cached.data, cached.content_type, "stale")
            logger.warning(f"Tile download failed: {type(ex).__name__}")
            return _error(502, "could not download the tile")

        if response.status_code != 200 or len(response.content) > MAX_TILE_BYTES:
            if cached is not None:
                return _tile_response(cached.data, cached.content_type, "stale")
            return _error(
                response.status_code if response.status_code >= 400 else 502,
                "the map provider did not return a tile",
            )

        content_type = response.headers.get("content-type", "application/octet-stream")
        await to_thread.run_sync(store.put, key, response.content, content_type)
        return _tile_response(response.content, content_type, "miss")

    @blueprint.route("/stats")
    async def get_stats():
        count, size = await to_thread.run_sync(store.stats)
        return {"tiles": count, "bytes": size}

    @blueprint.route("/clear", methods=["POST"])
    async def clear():
        removed = await to_thread.run_sync(store.clear)
        logger.info(f"Cleared {removed} cached map tiles")
        return {"removed": removed}

    logger.info(
        f"Map tile cache at {route} in {cache_dir}"
        + (" (server-side Mapbox token set)" if token else "")
    )

    # import_api() takes only the extension name in this flockwave-ext version
    http_server: HTTPServerExtensionAPI = app.import_api("http_server")
    async with httpx.AsyncClient(
        timeout=FETCH_TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "SkybrushServerMapCache/1.0"},
    ) as client:
        with http_server.mounted(blueprint, path=route):
            await sleep_forever()
