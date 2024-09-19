"""
hookspec

This module holds the specification for the plugins
and defines which members need to be implemented
"""

import pluggy
from census_converters import hookspec


class CensusConverterSpec:
    @hookspec
    def read_raw_data_into_pandas(cens_conv_inst):
        """
        read in the raw data into a pandas DataFrame

        This is templated with a keyword that is requered to be
        self when passed in through the class
        """
        return

    @hookspec
    def transform(cens_conv_inst):
        """
        transform

        This function actually transforms the raw data.

        This is templated with a keyword that is requered to be
        self when passed in through the class
        """
        return
