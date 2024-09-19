"""
util

Module that captures utility functions needed for Synthetic population
generation
"""

import math
import random as rn
import os
import csv
import uuid
import pandas as pd
import pickle
from logger import log
from error import SynthEcoError


def random_round_to_integer(float_value, seed=None):
    """
    Function that implements a more fair rounding based on a threshold
    rather than straing rounding.

    float_value: The value you want to round to an integer
    seed: Specify a seed for reproducibility

    returns float value that is rounded to an integer

    """
    rn.seed(seed)
    r_num = rn.random()

    threshold = float_value - int(float_value)

    if r_num < threshold:
        return math.ceil(float_value)
    else:
        return math.floor(float_value)


class CSVFileCache:
    """
    CSVFileCache

    A simple helper class to store readily needed files that are created via
    API so that we don't need to rebuild them every time

    """

    def __init__(self, location_=None):
        """
        Constructor

        Arguments:
            location: location of the cache in directory space

        Returns:
            instance
        """

        if location_ is None:
            self._location = os.path.join(os.getcwd(), ".cache")
        else:
            self._location = location_

        if not os.path.exists(self._location):
            try:
                os.mkdir(self._location)
            except Exception as e:
                raise e

        self._fileDict = {}
        self._fileDictFile = os.path.join(self._location, ".files.csv")
        if os.path.exists(self._fileDictFile):
            self._update_filedict()
        else:
            with open(self._fileDictFile, "w+") as f:
                pass

    def add_file(self, name_, csvContents_, force_=False):
        """
        add_file

        This will add a csv file to the cache

        Arguments
           name_: moniker to tag the file
           csvContents_: a pandas dataframe to be stored
           force_: if True, overwrite the file that is there

        Returns:
            True if successful
        """

        # Check arguements
        assert type(csvContents_) == pd.DataFrame
        if name_ not in self._fileDict.keys():
            randomname = os.path.join(self._location, f"{uuid.uuid4()}.pkl")

            csvContents_.to_pickle(randomname)

            self._fileDict[name_] = randomname
            self._update_filedictfile()

        else:
            if force_:
                self.remove_file(name_)
                self.add_file(name_, csvContents_)
            else:
                raise SynthEcoError(
                    "CSVFileCache:add_file: cannot overwrite file with force"
                )
        return True

    def remove_file(self, name_):
        """
        remove_file

        Removes a file if it exists in the cache, null operation if not there

        Arguments:
            name_: key for the file to be deleted

        Returns:
            True if successful
        """

        try:
            if name_ in self._fileDict.keys():
                filename = self._fileDict[name_]
                if os.path.exists(filename):
                    os.remove(filename)
                del self._fileDict[name_]

            self._update_filedictfile()
            return True
        except Exception as e:
            raise SynthEcoError(f"CSVFileCache problem removing file {name_}:\n{e}")

    def get_location(self):
        return self._location

    def get_file_dict(self):
        return self._fileDict

    def get_file(self, name_):
        """
        get_file

        Arguements:
            name_: key for the file you want to get

        Returns:
            pandas dataframe with the contencts of the csv

        """

        if name_ not in self._fileDict.keys():
            print(f"Asking for a csv file {name_} that doesn't exist")
            return pd.DataFrame()

        fileget = self._fileDict[name_]
        return pd.read_pickle(fileget)

    def flush(self):
        """
        flush

        flushes and cleans the cache
        """
        try:
            filestorem = [x for x in self._fileDict.keys()]
            for x in filestorem:
                self.remove_file(x)
            return True
        except Exception as e:
            raise SynthEcoError(f"CSVFileCache: unable to flush the cache:\n{e}")

    def _update_filedictfile(self):
        try:
            with open(self._fileDictFile, "w") as f:
                for i, v in self._fileDict.items():
                    f.write(f"{i},{v}\n")
        except Exception as e:
            raise SynthEcoError(f"CSVFileCache: problem updating fileDictFile:\n{e}")

    def _update_filedict(self):
        try:
            self._fileDict = {}
            with open(self._fileDictFile, "r") as f:
                freader = csv.reader(f)
                for row in freader:
                    if os.path.exists(row[1]):
                        self._fileDict[row[0]] = row[1]

        except Exception as e:
            raise SynthEcoError(f"CSVFileCache: problem updating fileDict:\n{e}")
