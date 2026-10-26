import gzip
import shutil
import threading
import urllib.request
from pathlib import Path
import struct
import math

import yaml

from medur_swarm import config, state

# SRTM 1 arc-second (3601 x 3601) and 3 arc-second (1201 x 1201) tile sizes in
# bytes -- the only two sizes terrain_check can read.
_VALID_HGT_BYTES = (3601 * 3601 * 2, 1201 * 1201 * 2)


class TerrainManager:

    BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"

    def __init__(self, terrain_dir="terrain"):
        self.terrain_dir = Path(terrain_dir)
        self.terrain_dir.mkdir(parents=True, exist_ok=True)

    def get_tile_name(self, lat, lon):
        lat = math.floor(lat)
        lon = math.floor(lon)

        lat_name = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"
        lon_name = f"E{lon:03d}" if lon >= 0 else f"W{abs(lon):03d}"

        return f"{lat_name}{lon_name}"

    def download_range(self, latitude, longitude, range_km):
        """
        Download all SRTM tiles covering a square area
        around the given latitude/longitude.

        range_km = distance from center in every direction.
        """

        # Approximate conversion
        lat_delta = range_km / 111.0

        # Longitude degrees vary with latitude
        lon_delta = range_km / (111.0 * math.cos(math.radians(latitude)))

        min_lat = math.floor(latitude - lat_delta)
        max_lat = math.floor(latitude + lat_delta)

        min_lon = math.floor(longitude - lon_delta)
        max_lon = math.floor(longitude + lon_delta)

        print()
        print("Terrain download area:")
        print(f"Center : {latitude}, {longitude}")
        print(f"Range  : {range_km} km")
        print(f"Lat    : {min_lat} -> {max_lat}")
        print(f"Lon    : {min_lon} -> {max_lon}")
        print()

        total = (max_lat - min_lat + 1) * (max_lon - min_lon + 1)

        count = 0

        for lat in range(min_lat, max_lat + 1):

            for lon in range(min_lon, max_lon + 1):

                count += 1

                print(f"[{count}/{total}]")

                self.download_tile(lat, lon)

        print()
        print("[TERRAIN] Range download completed.")

    def download_bbox(self, lat_min, lat_max, lon_min, lon_max):
        """
        Download every SRTM tile that overlaps a lat/lon bounding box.

        Returns {"downloaded": [...], "cached": [...], "failed": [...]} of
        tile names, so the caller can tell whether anything new arrived and
        which tiles are still missing.
        """
        result = {"downloaded": [], "cached": [], "failed": []}

        for lat in range(math.floor(lat_min), math.floor(lat_max) + 1):
            for lon in range(math.floor(lon_min), math.floor(lon_max) + 1):
                tile = self.get_tile_name(lat, lon)
                if self._is_cached(tile):
                    result["cached"].append(tile)
                elif self.download_tile(lat, lon) is not None:
                    result["downloaded"].append(tile)
                elif self._is_cached(tile):
                    # Our download failed, but another process (the server's
                    # terrain extension) delivered the tile meanwhile.
                    result["downloaded"].append(tile)
                else:
                    result["failed"].append(tile)

        return result

    def _is_cached(self, tile):
        """True only for a complete tile. A truncated .hgt (download killed
        mid-write) is not a cache hit -- it would be reused forever and then
        rejected by terrain_check as 'not a square SRTM tile'."""
        hgt_file = self.terrain_dir / f"{tile}.hgt"
        return hgt_file.exists() and hgt_file.stat().st_size in _VALID_HGT_BYTES

    def download_tile(self, lat, lon):

        lat = math.floor(lat)
        lon = math.floor(lon)

        tile = self.get_tile_name(lat, lon)

        hgt_file = self.terrain_dir / f"{tile}.hgt"
        # Temp names are this script's own. The server's terrain extension
        # downloads the same tiles (into the same folder when both run on one
        # machine) via "<tile>.hgt.gz", and two writers on one file corrupts it.
        gz_file = self.terrain_dir / f"{tile}.swarm.gz.tmp"
        part_file = self.terrain_dir / f"{tile}.swarm.hgt.part"

        # Already downloaded
        if self._is_cached(tile):
            print(f"[TERRAIN] Using cached {tile}.hgt")
            return hgt_file

        # Latitude folder
        lat_folder = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"

        url = f"{self.BASE_URL}/{lat_folder}/{tile}.hgt.gz"

        print(f"[TERRAIN] Downloading {tile}.hgt")

        try:

            with urllib.request.urlopen(url, timeout=30) as response:
                with open(gz_file, "wb") as destination:
                    shutil.copyfileobj(response, destination)

            # Unzip to a .part file and rename, so hgt_file only ever exists
            # when it is complete.
            with gzip.open(gz_file, "rb") as source:
                with open(part_file, "wb") as destination:
                    shutil.copyfileobj(source, destination)

            gz_file.unlink()
            part_file.replace(hgt_file)

            print(f"[TERRAIN] Downloaded {tile}.hgt")

            return hgt_file

        except Exception as e:

            print(f"[TERRAIN] Download failed: {e}")

            if gz_file.exists():
                gz_file.unlink()

            if part_file.exists():
                part_file.unlink()

            return None

    def get_elevation(self, latitude, longitude):

        # Determine required tile
        tile = self.get_tile_name(latitude, longitude)

        lat = math.floor(latitude)
        lon = math.floor(longitude)

        # Download if required
        hgt_file = self.download_tile(lat, lon)

        if hgt_file is None:
            return None

        # SRTM 1 arc-second = 3601 x 3601
        SIZE = 3601

        # Position inside tile
        lat_fraction = latitude - lat
        lon_fraction = longitude - lon

        # Convert coordinates to pixel
        row = int((1.0 - lat_fraction) * 3600)
        col = int(lon_fraction * 3600)

        # Clamp
        row = max(0, min(3600, row))
        col = max(0, min(3600, col))

        # Calculate byte offset
        offset = (row * SIZE + col) * 2

        try:

            with open(hgt_file, "rb") as f:

                f.seek(offset)

                data = f.read(2)

                elevation = struct.unpack(">h", data)[0]

            # SRTM void value
            if elevation == -32768:
                return None

            return elevation

        except Exception as e:

            print(f"[TERRAIN] Read error: {e}")
            return None


# --- Fence-driven download ----------------------------------------------------


def fence_bounds_latlon(yaml_path, margin_m):
    """(lat_min, lat_max, lon_min, lon_max) of the drawn fence, plus margin_m.

    rectangles.yaml stores the fence only in the sim frame (metres / 2, measured
    from `origin`, which is the SW corner of the outer polygon), so the vertices
    are converted back with cartToGeo -- the inverse of what the server used to
    write them. Every obstacle vertex is used: the outer polygon's wall quads
    are not labelled in the file, and inner fences lie inside the outer one.
    """
    import locatePosition

    with open(yaml_path) as f:
        world = yaml.safe_load(f)

    origin = world["origin"]
    if isinstance(origin, str):
        lat, lon = origin.strip("()").split(",")
        origin = (float(lat), float(lon))

    points = [p for wall in (world.get("obstacles") or []) for p in wall]
    if not points:
        raise ValueError(f"{yaml_path} has no obstacles to derive a fence from")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    # cartToGeo is linear in each axis (lat follows y, lon follows x), so the
    # two extreme corners give the whole bounding box.
    lat_min, lon_min = locatePosition.cartToGeo(
        origin, config.END_DISTANCE, [min(xs) * 2, min(ys) * 2]
    )
    lat_max, lon_max = locatePosition.cartToGeo(
        origin, config.END_DISTANCE, [max(xs) * 2, max(ys) * 2]
    )
    lat_min, lat_max = sorted((float(lat_min), float(lat_max)))
    lon_min, lon_max = sorted((float(lon_min), float(lon_max)))

    lat_pad = margin_m / 111320.0
    lon_pad = margin_m / (111320.0 * max(math.cos(math.radians(lat_min)), 1e-6))
    return lat_min - lat_pad, lat_max + lat_pad, lon_min - lon_pad, lon_max + lon_pad


_sync_lock = threading.Lock()
_sync_running = False
_sync_pending = False


def sync_terrain_for_fence(yaml_path=None):
    """Make sure the terrain tiles covering the current fence are on disk.

    Non-blocking: the download runs on a daemon thread, because tiles are
    ~26 MB each and this is called from the command-dispatch loop, which must
    not stall. Only the master computer runs the terrain gate, so other nodes
    skip it. If a sync is already running, a follow-up is queued rather than
    dropped -- the fence may have changed since that run started.
    """
    global _sync_running, _sync_pending
    if not state.master_flag:
        return
    with _sync_lock:
        if _sync_running:
            _sync_pending = True
            return
        _sync_running = True
    threading.Thread(
        target=_sync_worker,
        args=(yaml_path or config.RECTANGLES_PATH,),
        name="terrain-sync",
        daemon=True,
    ).start()


def _sync_worker(yaml_path):
    global _sync_running, _sync_pending
    while True:
        try:
            _sync_once(yaml_path)
        except Exception as e:
            print(f"[TERRAIN] Fence terrain sync failed: {e!r}")
        with _sync_lock:
            if _sync_pending:
                _sync_pending = False
                continue
            _sync_running = False
            return


def _sync_once(yaml_path):
    bounds = fence_bounds_latlon(yaml_path, config.TERRAIN_FENCE_MARGIN_M)
    print(
        "[TERRAIN] Fence area: "
        f"lat {bounds[0]:.4f}..{bounds[1]:.4f}, lon {bounds[2]:.4f}..{bounds[3]:.4f}"
    )
    result = TerrainManager(config.TERRAIN_DIR).download_bbox(*bounds)

    if result["downloaded"]:
        # The gate remembers missing tiles as missing; make it look again.
        try:
            from medur_swarm import terrain_gate

            terrain_gate.reset()
        except Exception as e:
            print(f"[TERRAIN] Could not reset terrain cache: {e!r}")

    print(
        f"[TERRAIN] Fence terrain ready -- downloaded {len(result['downloaded'])}, "
        f"cached {len(result['cached'])}, failed {len(result['failed'])}"
    )
    if result["failed"]:
        print(
            "[TERRAIN] Missing tiles (terrain checks over them will warn): "
            + ", ".join(result["failed"])
        )


if __name__ == "__main__":
    terrain = TerrainManager(config.TERRAIN_DIR)
    # print("Elevation:", terrain.get_elevation(26.956866716234416, 70.73133800961695), "meters")
    terrain.download_range(27.448812, 87.896140, 100)
    # terrain.download_range(12.989756, 80.164780, 5)
