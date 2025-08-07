"""
hookspec

This module holds the specification for the plugins
and defines which members need to be implemented
"""


import pluggy
from syntheco.census_fitting_procedures import hookspec


class CensusFittingProcedureSpec:

    @hookspec
    def perform_fitting(fit_proc_inst):
        """
        fitting implmentation spec
        """
        return
