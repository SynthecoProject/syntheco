"""
census_sampling_result

This class is for the results of the households sampleing procedures
"""

import pandas as pd
from census_household_sampling.census_household_sampling import CensusHouseholdSampling
from error import SynthEcoError
from logger import log, data_log


class CensusHouseholdSamplingResult:
    """
    CensusHouseholdSamplingResult

    Class that holds the data as a result of household sampling procedure.
    Mainly, it will be the geographic assignments of all of the households in
    the population
    """

    def __init__(self, sampling_proc_=None, data_=None):
        """
        Constructor

        Arguments:
            sampling_proc_: The sampling procedure initialized, needs to be
                            an instance of CensusHouseholdSampling
            data_: utility in case one wants to create a instance from
                   existing data
        """

        if not isinstance(sampling_proc_, CensusHouseholdSampling):
            raise SynthEcoError(
                "Trying to initilize CensusHousholdSamplingResult with "
                + "plugin of the wrong type {}".format(type(sampling_proc_))
            )

        self.sampling_proc = sampling_proc_

        if data_ is None:
            self.data = self.sampling_proc.perform_household_sampling()
        else:
            self.data = data_

    def __str__(self):
        """
        This method returns a nice print out of the CensusHouseholdSamplingResult
        """

        return "\n".join(
            [
                "Census Houshold Sampling Result",
                "------------------------------------------------------",
                "{}".format(self.data["Household Geographic Assignments"]),
            ]
        )
