import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader

from pathlib import Path
from pprint import pprint

from extractor import extract_file_paths, extract_NMEA

from env_vars import DATA_DIR, SHAPE_FILE


if __name__ == "__main__":
    files = extract_file_paths(DATA_DIR)

    nmea_lines = []
    for file in files:
        nmea_lines += extract_NMEA(file)

    # Coordinates
    lats = [nmea.latitude for nmea in nmea_lines]
    lons = [nmea.longitude for nmea in nmea_lines]

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.set_extent([-130, -65, 24, 50])

    # Load TIGER roads shapefile
    shp = shpreader.Reader(str(SHAPE_FILE))
    ax.add_feature(cfeature.STATES, edgecolor="black", linewidth=1)

    for record in shp.records():
        geom = record.geometry
        if record.attributes["RTTYP"] == "I":
            ax.add_geometries(
                [geom],
                crs=ccrs.PlateCarree(),
                linewidth=0.8,
                edgecolor="green",
                facecolor="none",
            )

    ax.coastlines()
    ax.set_title("US Interstates (TIGER/Line)")

    ax.scatter(lons, lats, c="red", transform=ccrs.PlateCarree())

    plt.show()
