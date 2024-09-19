"""
output_formatter

This module houses the skeleton class and initialization functions for
the main plugin framework for outputting results
"""

import importlib
import os
import pluggy


from output_formatters.hookspec import hookspec, OutputFormatterSpec
from input import InputParams
from census_fitting_result import CensusFittingResult
from census_household_sampling_result import CensusHouseholdSamplingResult
from logger import log, data_log
from error import SynthEcoError

# Map dictionary used to translate input commands to modules need
# to import

plugin_map = {
    "csv": {
        "module": "output_formatters.plugins.csv_outputter",
        "class": "CSVOutputter",
    }
}


def initialize(output_format):
    """
    initilize

    This function initializes and registers the plugin for the skeleton
    class

    Arguments:
        - output_format (str): defines the top level of the plugin map

    Returns:
        a pluggy plugin managers that has been registered with the proper
        implentation plugin.
    """
    try:
        plug_manager = pluggy.PluginManager("output_formatter")
        plug_manager.add_hookspecs(OutputFormatterSpec)

        if output_format not in plugin_map.keys():
            raise SynthEcoError(
                "Trying to initialize an output_formatter"
                + f"that doesn't have a plugin {output_format}"
            )

        plug_map_entry = plugin_map[output_format]

        log("DEBUG", f"output_formatter plugin map: {plug_map_entry}")

        mod = importlib.import_module(plug_map_entry["module"])
        plug = getattr(mod, plug_map_entry["class"])
        plug_manager.register(plug)
        return plug_manager
    except Exception as e:
        raise SynthEcoError(f"Output Formatter Plugin Failed to Initialize: {e}")


class OutputFormatter:
    """
    OutputFormatter

    Skeleton class for the plugin framework to output results
    """

    def __init__(self, input_params, fitting_result, sampling_result):
        """
        Constructor

        Arguments:
            - input_params (InputParams): the input paramters for Syntheco
            - fitting_result (CensusFittingresult class): result from a census fitting plugin
            - sampling_results (CensusHouseholdSamplingResult class): result from a household sampling procedure

        Returns:
            An instance of OutputFormatter
        """

        # Check argument types
        if input_params is None or not isinstance(input_params, InputParams):
            raise SynthEcoError(
                "Output Formatter Plugin Input Params is either empty or of wrong type"
            )
        if fitting_result is None or not isinstance(
            fitting_result, CensusFittingResult
        ):
            raise SynthEcoError(
                "Output Formatter Plugin Fitting result is either empty or of wrong type"
            )
        if sampling_result is None or not isinstance(
            sampling_result, CensusHouseholdSamplingResult
        ):
            raise SynthEcoError(
                "Output Formatter Plugin Sampling result is either empty or of wrong type"
            )

        self.input_params = input_params
        plug_manager = initialize(self.input_params["output_format"])

        self.fitting_result = fitting_result
        self.sampling_result = sampling_result
        self.hook = plug_manager.hook
        print(f"{self.hook}")

    def preprocess(self):
        """
        preprocess

        Stub function that wraps to the plugin for specific implementation
        """
        return self.hook.preprocess(out_format_inst=self)[0]

    def output(self):
        """
        output

        Stub function that wraps to the plugin for specific implemntation
        """
        return self.hook.output(out_format_inst=self)[0]

    def write_output(self):
        """
        write_outout

        This method performs all of the steps in writing the output

        Returns:
            True if output is written successfully

        """

        self.preprocessed_results = self.preprocess()
        return self.output()
