"""
uniform_household_sampling

This is the implementation of uniform household sampling to place
households within a geographic area
"""

from census_household_sampling import hookimpl
from logger import log, data_log
from error import SynthEcoError

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import multiprocessing as mp
import random as rn


class UniformHouseholdSampling:
    """
    UniformHouseholdSampling

    This class houses the implemented hooks for uniform geographic
    sampling of households from the result of the fitting selection
    procedures (e.g. IPF)
    """

    @hookimpl
    def sample_households(house_samp_inst):
        """
        sample_households

        Function that takes the households in a list and places them on
        a map

        Arguments:
            house_samp_inst - instance variable for all of the necessary data
                              through the plugin (see census_fitting_procedure)

        Returns:
            A new PUMS file with the geographic coordinates for all of the
            households
        """
        try:
            if house_samp_inst.pums_data_tables.is_separate():
                pums_deriv_df = house_samp_inst.fitting_result.data["Derived PUMS"][
                    "Household"
                ]
            else:
                pums_deriv_df = house_samp_inst.fitting_result.data["Derived PUMS"]

            pums_deriv_df = pums_deriv_df.sort_values(by=["GEO_CODE", "HH_ID"])
            border_gdf = house_samp_inst.border_tables.data

            hh_df = pums_deriv_df[["HH_ID", "GEO_CODE"]].drop_duplicates()
            hh_dict = {}

            hh_freq = hh_df.groupby("GEO_CODE").size()
            hh_args = []
            for gc, n in hh_freq.items():
                gc_border_gdf = border_gdf.loc[border_gdf["GEO_UNIT"] == gc]
                hh_args.append([gc, gc_border_gdf, n])

            with mp.Manager() as manager:
                hh_dict_p = manager.dict()
                argList = [tuple([hh_dict_p] + x) for x in hh_args]
                with manager.Pool(
                    house_samp_inst.input_params["parallel_num_cores"]
                ) as pool:
                    res = pool.map(
                        UniformHouseholdSampling._select_house_coordinates_helper,
                        argList,
                    )
                hh_dict = dict(hh_dict_p)

            hh_df["latlon"] = hh_df.apply(
                lambda x: hh_dict[x["GEO_CODE"]].pop(), axis=1
            )
            hh_df["longitude"] = hh_df.apply(lambda x: x["latlon"][0], axis=1)
            hh_df["latitude"] = hh_df.apply(lambda x: x["latlon"][1], axis=1)
            hh_df = hh_df.drop(columns=["latlon"])

            return {"Household Geographic Assignments": hh_df}

        except Exception as e:
            raise SynthEcoError(
                "uniform_household_sampling:sample_households\n{}".format(e)
            )

    @staticmethod
    def _select_house_coordinates_helper(args):
        """
        _select_households_helper
        Helper function for parallel execution of the random coordinate selector
        """
        return UniformHouseholdSampling._select_house_coordinates(*args)

    @staticmethod
    def _select_house_coordinates(hh_dict, geo_code, border_gdf, n):
        geocode_gdf = border_gdf.loc[border_gdf["GEO_UNIT"] == geo_code]
        coords = []
        while len(coords) < n:
            random_point = Point(
                rn.uniform(geocode_gdf.bounds["minx"], geocode_gdf.bounds["maxx"]),
                rn.uniform(geocode_gdf.bounds["miny"], geocode_gdf.bounds["maxy"]),
            )
            g_test = geocode_gdf["geometry"].contains(random_point)
            g_test.index = ["0"]
            if g_test[0]:
                coords.append((random_point.x, random_point.y))

        hh_dict[geo_code] = coords
