"""
border_tables

This class holds the standard tables that are needed for defining
administrative borders for the synthetic ecosystem
generation process
"""


class BorderTables:
    """
    BorderTables

    Class to hold the geographic data for sampling and mapping
    """
    def __init__(self, geo_unit_=None, converter_=None):
        """
        Creation Operator
        """
        self.geo_unit = geo_unit_
        self.converter = converter_
        self.data = self.converter.convert()

    def __str__(self):
        """
        This method returns a nice print out of the Border Table
        """
        return "\n".join(["Border Tables",
                          "".join(["_" for x in range(80)]),
                          f"{self.data}"])
