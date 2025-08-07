"""
census_fitting_procedure

This module houses the skeleton class and initalization functions for
the main plugin framework for fitting procedures such at IPF
"""

import importlib
import pluggy
import pandas as pd

from syntheco.census_fitting_procedures.hookspec import hookspec, CensusFittingProcedureSpec
from syntheco.global_tables import GlobalTables
from syntheco.pums_data_tables import PUMSDataTables
from syntheco.summary_data_tables import SummaryDataTables
from syntheco.error import SynthEcoError
from syntheco.logger import log, data_log

plugin_map = {'ipf': {'module': 'census_fitting_procedures.plugins.ipf_census_fitting',
                      'class': 'IPFCensusHouseholdFittingProcedure'},
              'ipf_sep_p_h': {'module': 'census_fitting_procedures.plugins.ipt_census_with_separate_p_h_file',
                              'class': 'IPFCensusHouseholdWithSeparatePHFilesProcedure'}}


def initialize(fitting_procedure):
    """
    initializes

    This funciton initializes and registers the plugin for the skeleton
    class

    Arguments:
        - fitting_procedure (str): defines the top level of the plugin map

    Returns:
        A pluggy plugin manager that has been registered with the proper
        implementation plugin.
    """
    log("INFO", "Initializing Fitting Procedure with {} options".format(fitting_procedure))

    try:
        plug_manager = pluggy.PluginManager("census_fitting_procedures")
        plug_manager.add_hookspecs(CensusFittingProcedureSpec)
        if fitting_procedure not in plugin_map.keys():
            raise SynthEcoError("Trying to initialize a fitting procedure "
                                "that doesn't have a plugin {}".format(fitting_procedure))

        plug_map_entry = plugin_map[fitting_procedure]
        log("DEBUG", "Census Fitting Procedure Plugin Map: {}".format(plug_map_entry))
        mod = importlib.import_module(plug_map_entry['module'])
        plug = getattr(mod, plug_map_entry['class'])
        plug_manager.register(plug)
        return plug_manager
    except Exception as e:
        raise SynthEcoError("Census Fitting Procedure Plugin Failed to Intialize: {}".format(e))


class CensusFittingProcedure:
    """
    CensusFittingProcedure

    Skeleton class for plugin framework for performing fitting procedures
    such as IPF

    Arguments:
        input_params (InputParams): the input parameters for Syntheco

    """

    def __init__(self, input_params,
                 global_tables=None,
                 pums_tables=None, summary_tables=None):

        self.input_params = input_params
        plug_manager = initialize(self.input_params['census_fitting_procedure'])
        log("DEBUG", "Successfully initalized fitting plugin")
        # Checking tables to make sure they are of the right type and full

        if global_tables is None or not isinstance(global_tables, GlobalTables):
            raise SynthEcoError("Census Fitting Procedure Plugin Global Tables is either empty or of wrong type")
        if pums_tables is None or not isinstance(pums_tables, PUMSDataTables):
            raise SynthEcoError("Census Fitting Procedure Plugin PUMS Data Tables is either empty or of wrong type")
        if summary_tables is None or not isinstance(summary_tables, SummaryDataTables):
            raise SynthEcoError("Census Fitting Procedure Plugin Summary Tables is either empty or of wrong type")

        self.global_tables = global_tables
        self.pums_tables = pums_tables
        self.summary_tables = summary_tables
        self.hook = plug_manager.hook
        self.prepared_data_df = pd.DataFrame()
        self.proceessed_data_df = pd.DataFrame()

    def perform_fitting(self):
        """
        perform_fitting

        Stub function that wraps to the plugin specific implementation
        """
        return self.hook.perform_fitting(fit_proc_inst=self)[0]

    def fit_data(self):
        """
        This method actually performs the fitting procedure for the census
        data

        Returns:
            A dataframe with the processed data

        TODO: Document the proper dataformat
        """
        self.processed_data_df = self.perform_fitting()
        return self.processed_data_df
