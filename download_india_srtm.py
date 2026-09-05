import gzip
import shutil
import urllib.request
from pathlib import Path

TERRAIN_DIR = Path(r"C:\Users\Joel\Desktop\Fixedwing-Swarm\terrain")

# India approximate coverage
MIN_LAT = 6
MAX_LAT = 37
MIN_LON = 68
MAX_LON = 98

BASE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"

TERRAIN_DIR.mkdir(parents=True, exist_ok=True)


def get_tile_name(lat, lon):
    if lat >= 0:
        lat_name = f"N{lat:02d}"
    else:
        lat_name = f"S{abs(lat):02d}"

    if lon >= 0:
        lon_name = f"E{lon:03d}"
    else:
        lon_name = f"W{abs(lon):03d}"

    return f"{lat_name}{lon_name}"


def download_tile(lat, lon):
    tile = get_tile_name(lat, lon)

    hgt_file = TERRAIN_DIR / f"{tile}.hgt"
    gz_file = TERRAIN_DIR / f"{tile}.hgt.gz"

    # Already downloaded
    if hgt_file.exists():
        print(f"[SKIP] {tile}.hgt already exists")
        return

    # Example:
    # N10E077.hgt.gz
    lat_folder = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"

    url = f"{BASE_URL}/{lat_folder}/{tile}.hgt.gz"

    print(f"[DOWNLOAD] {tile}.hgt")

    try:
        urllib.request.urlretrieve(url, gz_file)

        with gzip.open(gz_file, "rb") as source:
            with open(hgt_file, "wb") as destination:
                shutil.copyfileobj(source, destination)

        gz_file.unlink()

        print(f"[OK] {tile}.hgt")

    except Exception as error:
        print(f"[ERROR] {tile}: {error}")

        if gz_file.exists():
            gz_file.unlink()

        if hgt_file.exists():
            hgt_file.unlink()


test_tiles = [
    (10, 77),
    (10, 78),
    (11, 77),
    (11, 78),
]

total_tiles = len(test_tiles)

for current_tile, (lat, lon) in enumerate(test_tiles, start=1):
    print(f"\n[{current_tile}/{total_tiles}]")
    download_tile(lat, lon)

print()
print("India SRTM download completed.")