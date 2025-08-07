"""
summary tables

This class is a base class for summary tables needed to
create sythetic ecosystems. This class should provide a ready representation
to be able to perform the Iterative Proportional Fitting procedure and should
be completely independent from where the data comes
"""


import pandas as pd


class SummaryDataTables:
    def __init__(self, summary_variables_=None,
                 geo_unit_=None,
                 converter_=None,
                 data_=None):
        """
        Creation Operator
        """

        self.summary_variables = summary_variables_
        self.geo_unit = geo_unit_
        self.converter = converter_
        if data_ is None:
            self.data = self.converter.convert()
        else:
            self.data = data_

    def validate(self):
        """
        This is a function that will validate that the data for the Summary
        Table is correct
        """

        return True

    def __str__(self):
        """
        This method returns a nice print out of the GlobalTables
        """
        return '\n'.join(["Summary Tables",
                          "------------------------------------------------------"] +
                         [f"{x.name}\n{x}" for x in self.data.values()])
