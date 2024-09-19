import pandas as pd
import pytest
from unittest.mock import MagicMock, create_autospec, patch
import responses
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
import json
from collections import namedtuple
from typing import Callable

import census_converters.plugins.us_census_converters as us


class TestAPIManager:
    @pytest.fixture
    def api_manager(self):
        with us.api_manager.session.cache_disabled():
            yield us.api_manager

    @responses.activate
    def test_successful_call(self, api_manager):
        expected_data = {"success": "valid"}
        responses.get(api_manager.base_url, json=expected_data, status=200)

        data = api_manager.api_call()
        assert data == expected_data

    @responses.activate
    def test_httperror(self, api_manager):
        responses.get(api_manager.base_url, body=HTTPError("mock HTTPError"))

        with pytest.raises(HTTPError):
            api_manager.api_call()

    @responses.activate
    def test_timeout(self, api_manager):
        responses.get(api_manager.base_url, body=Timeout("mock Timeout"))

        with pytest.raises(Timeout):
            api_manager.api_call()

    @responses.activate
    def test_connectionerror(self, api_manager):
        responses.get(
            api_manager.base_url, body=ConnectionError("mock ConnectionError")
        )

        with pytest.raises(ConnectionError):
            api_manager.api_call()

    @responses.activate
    def test_requestexception(self, api_manager):
        responses.get(
            api_manager.base_url, body=RequestException("mock RequestException")
        )

        with pytest.raises(RequestException):
            api_manager.api_call()


class TestFormatDF:
    def test_successful_county_format_df(self):
        example_data = [
            ["P1_001N", "H1_001N", "state", "county"],
            ["570719", "233747", "10", "003"],
            ["237378", "142280", "10", "005"],
            ["181851", "72708", "10", "001"],
        ]
        ip = {"census_high_res_geo_unit": "county"}
        api_vars = ["P1_001N", "H1_001N"]
        df = us._format_df(example_data, ip, api_vars)

        expected_df = pd.DataFrame(
            {
                "GEO_CODE": ["10003", "10005", "10001"],
                "P1_001N": ["570719", "237378", "181851"],
                "H1_001N": ["233747", "142280", "72708"],
            }
        ).set_index("GEO_CODE")

        assert df.equals(expected_df)

    def test_successful_tract_format_df(self):
        example_data = [
            ["P1_001N", "H1_001N", "state", "county", "tract"],
            ["570719", "233747", "10", "003", "000200"],
            ["237378", "142280", "10", "005", "000300"],
            ["181851", "72708", "10", "001", "000400"],
        ]
        ip = {"census_high_res_geo_unit": "tract"}
        api_vars = ["P1_001N", "H1_001N"]
        df = us._format_df(example_data, ip, api_vars)

        expected_df = pd.DataFrame(
            {
                "GEO_CODE": ["10003000200", "10005000300", "10001000400"],
                "P1_001N": ["570719", "237378", "181851"],
                "H1_001N": ["233747", "142280", "72708"],
            }
        ).set_index("GEO_CODE")

        assert df.equals(expected_df)


FunctionCallMetadata = namedtuple("FunctionCallMetadata", ["params", "return_value"])


class TestUSCensusPlugins:
    @pytest.fixture
    def ip(self):
        input_params = MagicMock()
        input_params.data = {
            "census_year": 2020,
            "census_fitting_vars": ["BDSP"],
            "census_high_res_geo_unit": "county",
            "census_low_res_geo_unit": "state:10",
            "api_key": "key",
        }

        def mock_get_item(key):
            return input_params.data[key]

        input_params.__getitem__.side_effect = mock_get_item

        def has_keyword(kw):
            return kw in input_params.data

        input_params.has_keyword.side_effect = has_keyword

        return input_params

    @pytest.fixture
    def cens_conv_inst(self, ip):
        mock_census_converter = MagicMock()
        mock_census_converter.input_params = ip

        with open("census_converters/plugins/us_pums_info.json") as meta:
            mock_census_converter.metadata_json = json.load(meta)

        return mock_census_converter

    def read_scaffold(
        self,
        cens_conv_inst,
        api_call_meta: FunctionCallMetadata,
        format_df_meta: FunctionCallMetadata,
        read_func: Callable,
    ):
        mock_api_call = create_autospec(us.api_manager.api_call)
        mock_api_call.return_value = api_call_meta.return_value

        mock_format_df = create_autospec(us._format_df)
        mock_format_df.return_value = format_df_meta.return_value

        expected_output: pd.DataFrame = format_df_meta.return_value

        api_call_patch = (
            "census_converters.plugins.us_census_converters.api_manager.api_call",
            mock_api_call,
        )
        format_df_patch = (
            "census_converters.plugins.us_census_converters._format_df",
            mock_format_df,
        )
        with patch(*api_call_patch), patch(*format_df_patch):
            output: pd.DataFrame = read_func(cens_conv_inst)

        mock_api_call.assert_called_once_with(**api_call_meta.params)
        mock_format_df.assert_called_once_with(**format_df_meta.params)

        assert output.equals(expected_output)

    def test_global_read(self, cens_conv_inst):
        api_call_params = {
            "url": "/2020/dec/pl",
            "params": {
                "get": "P1_001N,H1_001N",
                "for": "county:*",
                "in": "state:10",
                "key": "key",
            },
        }
        api_call_return_value = [
            ["P1_001N", "H1_001N", "state", "county"],
            ["570719", "233747", "10", "003"],
            ["237378", "142280", "10", "005"],
            ["181851", "72708", "10", "001"],
        ]
        api_call_meta = FunctionCallMetadata(api_call_params, api_call_return_value)

        format_df_params = {
            "data": api_call_meta.return_value,
            "ip": cens_conv_inst.input_params,
            "api_vars": [
                "P1_001N",
                "H1_001N",
            ],
        }
        format_df_return_value = pd.DataFrame(
            {
                "GEO_CODE": ["10003", "10005", "10001"],
                "P1_001N": ["570719", "237378", "181851"],
                "H1_001N": ["233747", "142280", "72708"],
            }
        ).set_index("GEO_CODE")
        format_df_meta = FunctionCallMetadata(format_df_params, format_df_return_value)

        self.read_scaffold(
            cens_conv_inst,
            api_call_meta,
            format_df_meta,
            us.USCensusGlobalPlugin.read_raw_data_into_pandas,
        )

    def test_summary_read(self, cens_conv_inst):
        api_call_params = {
            "url": "/2020/acs/acs5/profile",
            "params": {
                "get": "DP04_0039E,DP04_0040E,DP04_0041E,DP04_0042E,DP04_0043E,DP04_0044E",
                "for": "county:*",
                "in": "state:10",
                "key": "key",
            },
        }
        api_call_return_value = [
            [
                "DP04_0039E",
                "DP04_0040E",
                "DP04_0041E",
                "DP04_0042E",
                "DP04_0043E",
                "DP04_0044E",
                "state",
                "county",
            ],
            ["4021", "21129", "46047", "88742", "54050", "10253", "10", "003"],
            ["1109", "3736", "26295", "74145", "28034", "7804", "10", "005"],
            ["699", "4101", "13745", "36720", "14367", "3441", "10", "001"],
        ]
        api_call_meta = FunctionCallMetadata(api_call_params, api_call_return_value)

        format_df_params = {
            "data": api_call_meta.return_value,
            "ip": cens_conv_inst.input_params,
            "api_vars": [
                "DP04_0039E",
                "DP04_0040E",
                "DP04_0041E",
                "DP04_0042E",
                "DP04_0043E",
                "DP04_0044E",
            ],
        }
        format_df_return_value = pd.DataFrame(
            {
                "GEO_CODE": ["10003", "10005", "10001"],
                "DP04_0039E": ["4021", "1109", "699"],
                "DP04_0040E": ["21129", "3736", "4101"],
                "DP04_0041E": ["46047", "26295", "13745"],
                "DP04_0042E": ["88742", "74145", "36720"],
                "DP04_0043E": ["54050", "28034", "14367"],
                "DP04_0044E": ["10253", "7804", "3441"],
            }
        ).set_index("GEO_CODE")
        format_df_meta = FunctionCallMetadata(format_df_params, format_df_return_value)

        self.read_scaffold(
            cens_conv_inst,
            api_call_meta,
            format_df_meta,
            us.USCensusSummaryPlugin.read_raw_data_into_pandas,
        )

    def test_pums_read(self, cens_conv_inst):
        api_call_params = {
            "url": "/2020/acs/acs5/pums",
            "params": {"get": "SERIALNO,BDSP", "for": "state:10", "key": "key"},
        }
        api_call_return_value = [
            ["SERIALNO", "BDSP", "state"],
            ["2019HU0234188", "0", "10"],
            ["2019HU0235156", "1", "10"],
            ["2019HU0235295", "2", "10"],
            ["2019HU0235857", "3", "10"],
            ["2019HU0236850", "4", "10"],
            ["2019HU0237117", "5", "10"],
        ]
        api_call_meta = FunctionCallMetadata(api_call_params, api_call_return_value)

        format_df_params = {
            "data": api_call_meta.return_value,
            "formulate_geo_code": False,
        }
        format_df_return_value = pd.DataFrame(
            {
                "SERIALNO": [
                    "2019HU0234188",
                    "2019HU0235156",
                    "2019HU0235295",
                    "2019HU0235857",
                    "2019HU0236850",
                    "2019HU0237117",
                ],
                "BDSP": ["0", "1", "2", "3", "4", "5"],
                "state": ["10", "10", "10", "10", "10", "10"],
            }
        )
        format_df_meta = FunctionCallMetadata(format_df_params, format_df_return_value)

        self.read_scaffold(
            cens_conv_inst,
            api_call_meta,
            format_df_meta,
            us.USCensusPUMSPlugin.read_raw_data_into_pandas,
        )

    def transform_scaffold(
        self, cens_conv_inst, expected_output: dict, transform_func: Callable
    ):
        output: dict = transform_func(cens_conv_inst)

        assert output.keys() == expected_output.keys()
        for data, expected_data in zip(output.values(), expected_output.values()):
            print(data)
            print(expected_data)
            assert type(data) == type(expected_data)

            if type(data) == pd.DataFrame:
                expected_data = expected_data.astype(data.dtypes)
                assert data.equals(expected_data)
            else:
                assert data == expected_data

    def test_global_transform(self, cens_conv_inst):
        cens_conv_inst.raw_data_df = pd.DataFrame(
            {
                "GEO_CODE": ["10003", "10005", "10001"],
                "P1_001N": ["570719", "237378", "181851"],
                "H1_001N": ["233747", "142280", "72708"],
            }
        ).set_index("GEO_CODE")

        expected_pop_df = pd.DataFrame(
            {
                "GEO_CODE": ["10003", "10005", "10001"],
                "total": [570719.0, 237378.0, 181851.0],
            }
        ).set_index("GEO_CODE")
        expected_nh_df = pd.DataFrame(
            {
                "GEO_CODE": ["10003", "10005", "10001"],
                "total": [233747.0, 142280.0, 72708.0],
            }
        ).set_index("GEO_CODE")
        expected_geos_of_interest = ["10003", "10005", "10001"]

        expected_output = {
            "total_population_by_geo": expected_pop_df,
            "number_households_by_geo": expected_nh_df,
            "geos_of_interest": expected_geos_of_interest,
            "census_variable_metadata": cens_conv_inst.metadata_json,
        }

        self.transform_scaffold(
            cens_conv_inst, expected_output, us.USCensusGlobalPlugin.transform
        )

    def test_summary_transform(self, cens_conv_inst):
        cens_conv_inst.raw_data_df = pd.DataFrame(
            {
                "GEO_CODE": ["10003"],
                "DP04_0039E": ["4021"],
                "DP04_0040E": ["21129"],
                "DP04_0041E": ["46047"],
                "DP04_0042E": ["88742"],
                "DP04_0043E": ["54050"],
                "DP04_0044E": ["10253"],
            }
        ).set_index("GEO_CODE")

        expected_output = {
            "BDSP": pd.DataFrame(
                {
                    "GEO_CODE": [
                        "10003",
                        "10003",
                        "10003",
                        "10003",
                        "10003",
                        "10003",
                    ],
                    "BDSP": [
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                    ],
                    "total": [
                        4021.0,
                        21129.0,
                        46047.0,
                        88742.0,
                        54050.0,
                        10253.0,
                    ],
                }
            ).set_index("GEO_CODE")
        }

        self.transform_scaffold(
            cens_conv_inst, expected_output, us.USCensusSummaryPlugin.transform
        )

    def test_pums_transform(self, cens_conv_inst):
        cens_conv_inst.raw_data_df = pd.DataFrame(
            {
                "HH_ID": [
                    "2019HU0234188",
                    "2019HU0235156",
                    "2019HU0235295",
                    "2019HU0235857",
                    "2019HU0236850",
                    "2019HU0237117",
                ],
                "BDSP": ["0", "1", "2", "3", "4", "5"],
                "state": ["10", "10", "10", "10", "10", "10"],
            }
        )

        expected_cat_df = pd.DataFrame(
            {
                "HH_ID": [
                    "2019HU0234188",
                    "2019HU0235156",
                    "2019HU0235295",
                    "2019HU0235857",
                    "2019HU0236850",
                    "2019HU0237117",
                ],
                "BDSP_V": ["0", "1", "2", "3", "4", "5"],
                "state": ["10", "10", "10", "10", "10", "10"],
                "BDSP": ["1", "2", "3", "4", "5", "6"],
            }
        )
        expected_freq_df = pd.DataFrame(
            {
                "BDSP": ["1", "2", "3", "4", "5", "6"],
                "total": ["1", "1", "1", "1", "1", "1"],
            }
        )

        expected_output = {
            "categorical_table": expected_cat_df,
            "frequency_table": expected_freq_df,
            "raw_data": cens_conv_inst.raw_data_df,
        }

        self.transform_scaffold(
            cens_conv_inst, expected_output, us.USCensusPUMSPlugin.transform
        )
