"""
census_household_sampling

This module houses the skeleton class and initilization functions
for the main plugin framework for census household sampling algorithms
"""

import importlib
import pluggy
import pandas as pd
import json
from pathlib import Path
import os

from census_household_sampling.hookspec import hookspec, CensusHouseholdSamplingSpec
from global_tables import GlobalTables
from pums_data_tables import PUMSDataTables
from border_tables import BorderTables
from input import InputParams
from census_fitting_result import CensusFittingResult
from logger import log, data_log
from error import SynthEcoError

plugin_map = {
    "uniform": {
        "module": "census_household_sampling.plugins.uniform_household_sampling",
        "class": "UniformHouseholdSampling",
    }
}


def initialize(sampling_procedure):
    """
    initialize

    This funciton initializes and registers the plugin for the skeleton
    class

    Arguments:
        - sampling_proceducre (str): defines the top level of the plugin map

    Returns:
        A pluggy plugin manager that has been registered with the proper
        implementation plugin.
    """
    try:
        plug_manager = pluggy.PluginManager("census_household_sampling")
        plug_manager.add_hookspecs(CensusHouseholdSamplingSpec)

        if sampling_procedure not in plugin_map.keys():
            raise SynthEcoError(
                "Trying to initialize a census household sampling"
                "that doesn't have a plugin {}".format(sampling_procedure)
            )

        plug_map_entry = plugin_map[sampling_procedure]

        log("DEBUG", "census_household_sampling plugin map: {}".format(plug_map_entry))

        mod = importlib.import_module(plug_map_entry["module"])
        plug = getattr(mod, plug_map_entry["class"])
        plug_manager.register(plug)
        return plug_manager
    except Exception as e:
        raise SynthEcoError(
            "Census Household Sampling Plugin Failed to Initialize: {}".format(e)
        )


class CensusHouseholdSampling:
    """
    CensushouseholdSampling

    Skeleton class for the plugin framework for randomly sampling and placing Households
    within a geographic area
    """

    def __init__(
        self,
        input_params,
        fitting_result,
        pums_data_tables,
        global_tables,
        border_tables,
    ):
        """
        Constructor

        Arguments:
            - input_params (InputParams): the input paramters for Syntheco
            - fitting_result (CensusFittingresult class): result from a census fitting plugin
            - pums_census_conv (PUMSDataTables class): result from the census converter
            - global_tables (GlobalTables class):

        Returns:
            An instant of CensusHouseholdSampling
        """

        # Check argument types
        if input_params is None or not isinstance(input_params, InputParams):
            raise SynthEcoError(
                "Census Household Sampling Plugin Input Params is either empty or of wrong type"
            )
        if global_tables is None or not isinstance(global_tables, GlobalTables):
            raise SynthEcoError(
                "Census Household Sampling Plugin Global Tables is either empty or of wrong type"
            )
        if fitting_result is None or not isinstance(
            fitting_result, CensusFittingResult
        ):
            raise SynthEcoError(
                "Census Household Sampling Plugin Fitting result is either empty or of wrong type"
            )
        if pums_data_tables is None or not isinstance(pums_data_tables, PUMSDataTables):
            raise SynthEcoError(
                "Census Household Sampling Plugin PUMS Tables are either empty or of wrong type"
            )
        if border_tables is None or not isinstance(border_tables, BorderTables):
            raise SynthEcoError(
                "Census Household Sampling Plugin Border Tables are either empty or of wrong type"
            )

        self.input_params = input_params
        plug_manager = initialize(
            self.input_params["census_household_sampling_procedure"]
        )

        self.global_tables = global_tables
        self.pums_data_tables = pums_data_tables
        self.fitting_result = fitting_result
        self.border_tables = border_tables
        self.hook = plug_manager.hook
        self.processed_data_df = pd.DataFrame()

    def sample_households(self):
        """
        sample_households

        Stub function that wraps to the plugin specific implementation
        """
        return self.hook.sample_households(house_samp_inst=self)[0]

    def perform_household_sampling(self):
        """
        perform_household_sampling

        This method actually performs the sampling procedure and return
        the result

        Returns:
            A dataframe of the sampled households

        TODO: Document the proper data format
        """
        self.processed_data_df = self.sample_households()
        return self.processed_data_df
