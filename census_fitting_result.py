"""
census_fitting_result

This class is for the results of a census fitting procedure
"""

import pandas as pd
from census_fitting_procedures.census_fitting_procedure import CensusFittingProcedure
from error import SynthEcoError
from logger import log, data_log


class CensusFittingResult:
    def __init__(self, converter_=None, data_=None):
        """
        Creation operator

        Arguments:
            converter_: the census_fitting_procedure plugin
            data_: If one would like to pass in the data rather
                   computing the data, present for copy operations
                   and future caching
        """

        if not isinstance(converter_, CensusFittingProcedure):
            raise SynthEcoError(
                "Trying to initialize CensusFittingResult with "
                + "plugin on the wrong type {}".format(type(converter_))
            )

        self.converter = converter_

        if data_ is None:
            self.data = self.converter.fit_data()
        else:
            self.data = data_

    def __str__(self):
        """
        This method returns a nice print out of CensusFittingResult
        """

        return "\n".join(
            [
                "Census Fitting Result",
                "------------------------------------------------------",
            ]
            + ["{}:\n{}".format(x, self.data[x]) for x in list(self.data)[0:10]]
        )
