"""
census_converter

This module houses the skeleton class and initialization functions for
the main plugin framework for census conversion

TODO: Add Debug and Verbosity
TODO: Add error handling and variable checking
"""

import importlib
import pluggy
import pandas as pd
import json
from pathlib import Path
import os

from census_converters.hookspec import hookspec, CensusConverterSpec
from logger import log, data_log
from error import SynthEcoError

# Map dictionary used to translate input commands to the modules needed
# needed to import
plugin_map = {
    "canada": {
        "module": "census_converters.plugins.canada_census_converters",
        "global": "CanadaCensusGlobalPlugin",
        "metadata_json": "{}/plugins/canada_pums_info.json".format(
            Path(__file__).parent
        ),
        "pums": "CanadaCensusPUMSPlugin",
        "summary": "CanadaCensusSummaryPlugin",
        "border": "CanadaCensusBorderPlugin",
    },
    "us": {
        "module": "census_converters.plugins.us_census_converters",
        "global": "USCensusGlobalPlugin",
        "metadata_json": "{}/plugins/us_pums_info.json".format(Path(__file__).parent),
        "pums": "USCensusPUMSPlugin",
        "summary": "USCensusSummaryPlugin",
        "border": "USCensusBorderPlugin",
    },
}


def initialize(census_converter="canada", table_type="global"):
    """
    initialize

    This funciton initializes and registers the plugin for the skeleton
    class

    Arguments:
        - census_converter (str): defines the top level of the plugin map
        - table_type (str): defines the type of table for the plugin

    Returns:
        A pluggy plugin manager that has been registered with the proper
        implementation plugin.
    """
    log(
        "INFO",
        "Intitializing Census Converter with {},{} options".format(
            census_converter, table_type
        ),
    )
    try:
        plug_manager = pluggy.PluginManager("census_converters")
        plug_manager.add_hookspecs(CensusConverterSpec)

        if census_converter not in plugin_map.keys():
            raise SynthEcoError(
                "Trying to initialize a census converter "
                "that doesn't have a plugin {}".format(census_converter)
            )
        plug_map_entry = plugin_map[census_converter]

        if table_type not in plug_map_entry.keys():
            raise SynthEcoError(
                "Trying to initialize a census converter "
                "with a table type that doesn't have a "
                "plugin {}.{}".format(census_converter, table_type)
            )

        log("DEBUG", "Plugin Map: {}".format(plug_map_entry))
        mod = importlib.import_module(plug_map_entry["module"])
        plug = getattr(mod, plug_map_entry[table_type])
        plug_manager.register(plug)
        return plug_manager
    except Exception as e:
        raise SynthEcoError("Census Conveter Plugin Failed to Initialize: {}".format(e))


class CensusConverter:
    """
    CensusConveter

    Skeleton class for the plugin framework for conveting census
    data to Syntheco data standards
    """

    def __init__(self, input_params, census_converter, table_type, _global_tables=None):
        """
        Constructor

        Arguments:
            - input_params (InputParams): the input paramters for Syntheco
            - census_conveter (str): defines which set of converters needed
            - table_type (str): defines the type of table needed (e.g. global)

        Returns:
            An instance of CensusConverter
        """
        self.input_params = input_params
        self.global_tables = _global_tables
        plug_manager = initialize(census_converter, table_type)
        self.metadata_json = json.load(
            open(plugin_map[census_converter]["metadata_json"], "r"), parse_int=str
        )
        self.hook = plug_manager.hook
        self.raw_data_df = self.read_raw_data_into_pandas()
        self.processed_data_df = pd.DataFrame()

    def read_raw_data_into_pandas(self):
        """
        read_raw_data_into_pandas

        Stub function that wraps to the plugin specific implementation
        """
        return self.hook.read_raw_data_into_pandas(cens_conv_inst=self)[0]

    def transform(self):
        """
        transform

        Stub function that wraps to the plugin specific implementation
        """
        return self.hook.transform(cens_conv_inst=self)[0]

    def convert(self):
        """
        This method performs the conversion from raw data to
        the final table for core Syntheco use


        Returns:
            A data with processed data, the format and tables
            that are in this data are dependent on the converter and
            type of table that is to be the result. Please refer to
            the concrete converter class for details in the "converters"
            directory
        """
        self.processed_data_df = self.transform()
        return self.processed_data_df
