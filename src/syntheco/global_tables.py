"""
global_tables

This class that holds the standard tables that are needed across
the synthetic ecosystem generation process.

"""
import pandas as pd


class GlobalTables:
    """
    GlobalTables class

    This is a class to hold the standard tables needed for various aspects
    of the Syntheco ecosystem generation system.
    """
    def __init__(self, geo_unit_=None, converter_=None):
        """
        Creation operator
        """
        self.geo_unit = geo_unit_
        self.converter = converter_
        self.data = self.converter.convert()

    def __str__(self):
        """
        This method returns a nice print out of the GlobalTables
        """
        return_str = "\n".join(["Global Tables",
                                "------------------------------------------------------"])
        for x in self.data.values():
            if isinstance(x, pd.DataFrame):
                return_str += f"{x.name}\n{x}\n"
            elif isinstance(x, dict):
                for n, v in list(x.items())[1:10]:
                    return_str += f"{n}: {v}\n"
            else:
                return_str += f"{x[1:10]}\n"
        return return_str

    def __getitem__(self, item):
        return self.data[item]
