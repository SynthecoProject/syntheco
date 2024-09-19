"""
hookspec

This module holds the specification for the plugins
and defines which members need to be implemented
"""

import pluggy
from census_household_sampling import hookspec


class CensusHouseholdSamplingSpec:
    """
    CensusHouseholdSamplingSpec

    wrapper class that defines the implmentation hooks for Plugins
    """

    @hookspec
    def sample_households(house_samp_inst):
        """
        implementation spec
        """
        return
