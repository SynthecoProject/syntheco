import pytest

from syntheco import input_schema


@pytest.fixture
def schema_obj():
    return input_schema._schema


class TestCanadaInput:
    @pytest.fixture
    def canada_input(self, tmp_path):
        return {
            "census_year": 2016,
            "census_converter": "canada",
            "census_high_res_geo_unit": 2,
            "census_low_res_geo_unit": 462,
            "census_fitting_vars": ["AGEGRP", "HDGREE", "HHSIZE", "TOTINC"],
            "census_input_files": {
                "profile_data_csv": tmp_path,
                "pums_h_csv": tmp_path,
                "border_gml": tmp_path,
            },
            "output_log_file": "canada.out.txt",
            "output_data_log_file": "canada_data_out.txt",
            "census_fitting_procedure": "ipf",
            "census_household_sampling_procedure": "uniform",
            "debug_limit_geo_codes": 10,
            "parallel_num_cores": 4,
        }

    def test_valid_canada_input(self, schema_obj, canada_input):
        assert schema_obj.is_valid(canada_input)

    def test_invalid_canada_inputs(self, schema_obj, canada_input):
        for key in canada_input:
            # tests each key individually for invalid input
            invalid_input = canada_input.copy()
            invalid_input[key] = None
            assert not schema_obj.is_valid(invalid_input)

    def test_invalid_census_input_files_canada_input(self, schema_obj, canada_input):
        canada_input["census_input_files"]["profile_data_csv"] = "not a file"
        assert not schema_obj.is_valid(canada_input)


class TestUSInput:
    @pytest.fixture
    def us_input(self, tmp_path):
        return {
            "census_year": 2020,
            "census_converter": "us",
            "census_high_res_geo_unit": "tract",
            "census_low_res_geo_unit": "state:10",
            "census_fitting_vars": ["AGEP", "SCHL", "MAR", "HINCP"],
            "census_input_files": {
                "border_gml": tmp_path,
            },
            "output_log_file": "us.out.txt",
            "output_data_log_file": "us_data_out.txt",
            "census_fitting_procedure": "ipf",
            "census_household_sampling_procedure": "uniform",
            "debug_limit_geo_codes": 10,
            "parallel_num_cores": 4,
            "api_key": "key",
        }

    def test_valid_us_input(self, schema_obj, us_input):
        assert schema_obj.is_valid(us_input)

    def test_invalid_us_inputs(self, schema_obj, us_input):
        for key in us_input:
            invalid_input = us_input.copy()
            invalid_input[key] = None
            assert not schema_obj.is_valid(invalid_input)


def test_empty_input_is_invalid(schema_obj):
    assert not schema_obj.is_valid({})
