"""
input_schema

A module to house the input schema for the yaml input files
"""

import os
from schema import Schema, And, Or, Optional

_schema_specs = {
    "common": {
        "census_year": int,
        "census_converter": And(str, Or("us", "canada")),
        Optional("census_input_files"): And(dict, {str: os.path.exists}),
        "census_fitting_vars": [str],
        "census_fitting_procedure": str,
        Optional("census_household_sampling_procedure", default="None"): str,
        Optional("output_log_file", default="sytheco_out.txt"): str,
        Optional("output_data_log_file", default="syntheco_data_out.txt"): str,
        Optional("output_prefix", default="syntheco_population"): str,
        Optional("output_format", default="csv"): str,
        Optional("ipf_max_iterations", default=10000): int,
        Optional("ipf_fail_on_nonconvergence", default=False): bool,
        Optional("ipf_convergence_rate", default=1.0e-5): float,
        Optional("ipf_rate_tolerance", default=1.0e-8): float,
        Optional("ipf_alpha", default=0.0): float,
        Optional("ipf_k", default=0.0001): float,
        Optional("debug_limit_geo_codes"): int,
        Optional("parallel_num_cores", default=1): int,
        Optional("cache_location"): str,
    },
    "us": {
        Optional("use_census_api", default=False): bool,
        Optional("census_data_dir"): str,
        "api_key": str,
        "census_high_res_geo_unit": str,
        "census_low_res_geo_unit": str,
    },
    "canada": {"census_high_res_geo_unit": int, "census_low_res_geo_unit": int},
}


class SynthEcoSchema(Schema):
    """
    SynthEcoSchema class

    This class extends the Schema class to offer a customized validation
    process relevant to SynthEco.
    """

    def validate(self, data: dict):
        """
        validate

        This will validate the SynthEco input file according to the schema
        defined above. First, the common schema will be validated. Then,
        the census converter will be determined from the input and it's
        specific schema will be validated.

        Returns:
            the validated schema
        """
        # validate common data
        validated_data: dict = self._validate_common_schema(data)

        # validate converter specific data
        if data["census_converter"] == "us":
            validated_data.update(self._validate_us_schema(data))
        elif data["census_converter"] == "canada":
            validated_data.update(self._validate_canada_schema(data))

        if any(key not in validated_data.keys() for key in data.keys()):
            unused_keys = [
                key for key in data.keys() if key not in validated_data.keys()
            ]
            print(
                f"The following input keys are not used by the schema: {unused_keys}",
            )

        return validated_data

    def _validate_common_schema(self, data: dict):
        """
        _validate_common_schema

        A helper function for the main validate method which will validate the
        common schema defined by the _schema_specs dictionary.

        Returns:
            the validated common schema
        """
        return Schema(_schema_specs["common"], ignore_extra_keys=True).validate(data)

    def _validate_us_schema(self, data: dict):
        """
        _validate_us_schema

        A helper function for the main validate method which will validate the
        US schema defined by the _schema_specs dictionary.

        Returns:
            the validated US schema
        """
        return Schema(_schema_specs["us"], ignore_extra_keys=True).validate(data)

    def _validate_canada_schema(self, data: dict):
        """
        _validate_canada_schema

        A helper function for the main validate method which will validate the
        Canada schema defined by the _schema_specs dictionary.

        Returns:
            the validated Canada schema
        """
        return Schema(_schema_specs["canada"], ignore_extra_keys=True).validate(data)


_schema = SynthEcoSchema({})  # initialized with empty schema
