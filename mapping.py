"""
mapping

just a basic utility to make a map of the Households
in a synthetic population

This needs to be incorporated into the main tool
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import numpy as np
import argparse

from input import InputParams


def main():
    parser = argparse.ArgumentParser(description="Synthco Command Line Parse")
    parser.add_argument(
        "-i", "--input_file", action="store", help="The input yaml file"
    )
    parser.add_argument("-s", "--syntheco_prefix", action="store")
    parser.add_argument(
        "-o",
        "--output_prefix",
        action="store",
        help="The prefix for the output files",
        default="syntheco_output",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Activates verbose output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Activates debugging output"
    )

    args = parser.parse_args()

    ip = InputParams(args.input_file)

    synth_hh_df = pd.read_csv(
        "{}.households.csv".format(args.syntheco_prefix), dtype={"GEO_CODE": float}
    )

    # Extract the appropriate geocodes
    geo_codes = synth_hh_df["GEO_CODE"].drop_duplicates().tolist()

    border_gml_file = ip["census_input_files"]["border_gml"]

    border_gdf = gpd.read_file(border_gml_file)
    border_gdf = border_gdf.to_crs("WGS 84")

    reduced_gdf = border_gdf[border_gdf["CTUID"].isin(geo_codes)]
    reduced_gdf = reduced_gdf.to_crs("WGS 84")

    geometry = [
        Point(xy) for xy in zip(synth_hh_df["longitude"], synth_hh_df["latitude"])
    ]

    hh_data = gpd.GeoDataFrame(synth_hh_df, crs=reduced_gdf.crs, geometry=geometry)
    ax = reduced_gdf.plot()
    hh_data.plot(ax=ax, color="red", markersize=1)
    plt.savefig("map.jpg")


if __name__ == "__main__":
    main()
