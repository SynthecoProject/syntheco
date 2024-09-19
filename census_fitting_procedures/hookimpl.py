"""
hookimpl

This module defines the plugin spec default implementation
"""

from census_fitting_procedures import hookimpl


class CensusFittingProcedureSpec:
    """
    CensusFittingProceduresSpec

    wrapper class that defines the implmentation hooks for Plugins
    """

    @hookimpl
    def perform_fitting(fit_proc_inst):
        """
        fitting implmentation spec
        """
        return
