import pytest
import random as rn
import os
import csv
import pandas as pd
import shutil

from error import SynthEcoError
import util


class TestRandomRoundToInteger:
    def test_round_float_up(self):
        float_value = 1.2
        seed = 1

        rn.seed(1)
        assert rn.random() == 0.13436424411240122

        assert util.random_round_to_integer(float_value, seed) == 2

    def test_round_float_down(self):
        float_value = 1.1
        seed = 1

        rn.seed(1)
        assert rn.random() == 0.13436424411240122

        assert util.random_round_to_integer(float_value, seed) == 1


class TestFileCache:
    def test_file_cache(self):
        # test without a path
        csvFileCache = util.CSVFileCache(
            location_=os.path.join(os.getcwd(), "cache_test")
        )
        assert csvFileCache.get_location() == os.path.join(os.getcwd(), "cache_test")

        assert csvFileCache.flush()

        csvDF = pd.DataFrame({"id": [0, 1, 2], "a": [1, 2, 3], "b": [4, 5, 6]})
        csvDF = csvDF.set_index("id")
        assert csvFileCache.add_file("test", csvDF)
        assert csvFileCache.get_file("test").equals(csvDF)

        assert csvFileCache.add_file("test1", csvDF)
        assert csvFileCache.remove_file("test1")

        with pytest.raises(SynthEcoError):
            csvFileCache.add_file("test", csvDF)

        assert csvFileCache.add_file("test", csvDF, force_=True)
        assert csvFileCache.get_file("test").equals(csvDF)

        assert csvFileCache.flush()
        shutil.rmtree(csvFileCache.get_location())
