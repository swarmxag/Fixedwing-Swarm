"""Extension that provides a simple HTTP endpoint for serving map tiles.

This extension allows clients to request map tiles by specifying the zoom level,
x and y coordinates in the URL path. If a tile doesn't exist locally, it will be
downloaded from the configured tile source URL.
"""

from contextlib import ExitStack
from logging import Logger
from quart import abort, send_file, request
from trio import sleep_forever, open_file
from typing import Optional
from pathlib import Path
import httpx
from enum import Enum

from flockwave.server.utils import overridden
from flockwave.server.utils.quart import make_blueprint

app = None
log: Optional[Logger] = None
configuration = None

blueprint = make_blueprint("map_cache", __name__)


class MAPBOX(Enum):
    SATELLITE = "mapbox.satellite"
    STATIC = "mapbox.static"
    VECTOR = "mapbox.vector"


class MAPTILER(Enum):
    BASIC = "maptiler.basic"
    HYBRID = "maptiler.hybrid"
    SATELLITE = "maptiler.satellite"
    STREETS = "maptiler.streets"


reverse_lookup = {
    member.value: member for enum_class in [MAPBOX, MAPTILER] for member in enum_class
}

tile_sources = {
    MAPBOX.STATIC: "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/512/{z}/{x}/{y}@2x?access_token={apikey}",
    MAPBOX.SATELLITE: "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.jpg90?access_token={apikey}",
    MAPBOX.VECTOR: "https://{a-d}.tiles.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=${apikey}",
    MAPTILER.BASIC: "https://api.maptiler.com/maps/basic/{z}/{x}/{y}@2x.png?key={apikey}",
    MAPTILER.HYBRID: "https://api.maptiler.com/maps/hybrid/{z}/{x}/{y}@2x.jpg?key={apikey}",
    MAPTILER.SATELLITE: "https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key={apikey}",
    MAPTILER.STREETS: "https://api.maptiler.com/maps/streets/{z}/{x}/{y}@2x.png?key={apikey}",
}


async def download_tile(url: str, tile_path: Path) -> bool:
    """Downloads a tile from the given URL and saves it to the specified path."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code == 200:
                tile_path.parent.mkdir(parents=True, exist_ok=True)

                async with await open_file(tile_path, "wb") as f:
                    await f.write(response.content)
                return True
            else:
                log.error(
                    f"Failed to download tile from {url}: HTTP {response.status_code}"
                )
                return False
    except Exception as e:
        log.error(f"Error downloading tile from {url}: {str(e)}")
        return False


@blueprint.route("/<int:z>/<int:x>/<int:y>.png")
async def get_tile(z: int, x: int, y: int):
    """Request handler that serves a map tile for the given zoom level and coordinates.
    If the tile doesn't exist locally, it will be downloaded from the configured source URL.

    Parameters:
        z: Zoom level
        x: X coordinate
        y: Y coordinate
    """
    args = request.args
    print(args)
    baseMap = args.get("type")
    Maptype = reverse_lookup.get(baseMap)
    apikey = args.get("apiKey")

    # if not isinstance(Maptype, str):
    #     print("Map")
    #     abort(404)
    if not isinstance(apikey, str):
        print("apikey")
        abort(404)
    global configuration

    tile_dir = configuration.get("tile_dir", "tiles")
    # Get the tile directory from configuration
    tile_path = (
        Path(tile_dir)
        / Path(baseMap.split(".")[0])
        / Path(baseMap.split(".")[1])
        / str(z)
        / str(x)
        / f"{y}.png"
    )

    # If tile doesn't exist locally and we have a source URL, try to download it
    if not tile_path.exists():
        source_url = tile_sources.get(Maptype)
        if source_url:
            # Format the source URL with the tile coordinates
            url = source_url.format(z=z, x=x, y=y, apikey=apikey)
            success = await download_tile(url, tile_path)
            if not success:
                abort(404)  # Not found
        else:
            abort(404)  # Not found

    return await send_file(tile_path, mimetype="image/png")


async def run(app, config, logger):
    """Background task that is active while the extension is loaded."""
    global configuration
    configuration = config
    route = configuration.get("route", "/tile")

    http_server = app.import_api("http_server")
    with ExitStack() as stack:
        stack.enter_context(overridden(globals(), app=app, log=logger))
        stack.enter_context(http_server.mounted(blueprint, path=route))
        await sleep_forever()


dependencies = ("http_server",)
description = "Map tile server extension"
schema = {
    "properties": {
        "route": {
            "type": "string",
            "title": "URL root",
            "description": (
                "URL where the extension is mounted within the HTTP namespace "
                "of the server"
            ),
            "default": "/map_cache",
        },
        "tile_dir": {
            "type": "string",
            "title": "Tile directory",
            "description": "Directory containing the map tiles",
            "default": "tiles",
        },
    }
}
