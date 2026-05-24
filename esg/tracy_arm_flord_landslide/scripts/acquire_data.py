"""
acquire_data.py

Downloads DEM, bathymetry, and glacier imagery for Tracy Arm Fjord.
All files saved into data/raw/.
"""

from pathlib import Path
import requests

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, out_path: Path):
    """Simple streaming downloader."""
    print(f"Downloading: {url}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved → {out_path}")


# ---------------------------------------------------------
# ArcticDEM (Tracy Arm tile)
# ---------------------------------------------------------

def download_arcticdem():
    url = (
        "https://data.pgc.umn.edu/elev/dem/setsm/ArcticDEM/mosaic/v3.0/"
        "ArcticDEM_8m_2021.tif"
    )
    out = RAW_DIR / "tracy_arm_dem.tif"
    download_file(url, out)


# ---------------------------------------------------------
# NOAA Bathymetry (GEBCO subset)
# ---------------------------------------------------------

def download_bathymetry():
    url = (
        "https://www.ngdc.noaa.gov/thredds/fileServer/"
        "bathymetry/gebco/GEBCO_2023_sub_Alaska.tif"
    )
    out = RAW_DIR / "tracy_arm_bathymetry.tif"
    download_file(url, out)


# ---------------------------------------------------------
# Landsat/Sentinel (optional glacier imagery)
# ---------------------------------------------------------

def download_glacier_imagery():
    url = (
        "https://landsat-pds.s3.amazonaws.com/c1/L8/080/015/"
        "LC08_L1TP_080015_20200712_20200722_01_T1/LC08_L1TP_080015_20200712_B4.TIF"
    )
    out = RAW_DIR / "glacier_optical.tif"
    download_file(url, out)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    download_arcticdem()
    download_bathymetry()
    download_glacier_imagery()
