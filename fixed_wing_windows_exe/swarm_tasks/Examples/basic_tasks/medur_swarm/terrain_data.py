import gzip
import shutil
import urllib.request
from pathlib import Path
import struct
import math


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

    def download_tile(self, lat, lon):

        lat = math.floor(lat)
        lon = math.floor(lon)

        tile = self.get_tile_name(lat, lon)

        hgt_file = self.terrain_dir / f"{tile}.hgt"
        gz_file = self.terrain_dir / f"{tile}.hgt.gz"

        # Already downloaded
        if hgt_file.exists():
            print(f"[TERRAIN] Using cached {tile}.hgt")
            return hgt_file

        # Latitude folder
        lat_folder = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"

        url = f"{self.BASE_URL}/{lat_folder}/{tile}.hgt.gz"

        print(f"[TERRAIN] Downloading {tile}.hgt")

        try:

            urllib.request.urlretrieve(url, gz_file)

            with gzip.open(gz_file, "rb") as source:
                with open(hgt_file, "wb") as destination:
                    shutil.copyfileobj(source, destination)

            gz_file.unlink()

            print(f"[TERRAIN] Downloaded {tile}.hgt")

            return hgt_file

        except Exception as e:

            print(f"[TERRAIN] Download failed: {e}")

            if gz_file.exists():
                gz_file.unlink()

            if hgt_file.exists():
                hgt_file.unlink()

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


terrain = TerrainManager(
    r"C:\Users\Dell\Documents\Fixedwing-Swarm\fixed_wing_windows_exe\swarm_tasks\Examples\basic_tasks\medur_swarm\terrain"
)

elevation = terrain.get_elevation(26.384215926666556, 70.86223468339631)
# terrain.download_range(26.37761818434305, 70.75533129776274, 50)
# terrain.download_range(12.989756, 80.164780, 5)
print("Elevation:", elevation, "meters")
