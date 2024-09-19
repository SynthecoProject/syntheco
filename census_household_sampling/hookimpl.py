"""
hookimpl

This module defines the plugin speck default implementation
"""

from census_household_sampling import hookimpl


class CensusHouseholdSamplingSpec:
    """
    CensusHouseholdSAmplingSpec

    wrapper class that defines the implmentation hooks for Plugins
    """

    @hookimpl
    def sample_households(house_samp_inst):
        """
        implementation spec
        """
        return
