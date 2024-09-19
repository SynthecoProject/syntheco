"""
main

This is the main control module for syntheco
"""

import argparse
from census_converters.census_converter import CensusConverter
from census_fitting_procedures.census_fitting_procedure import CensusFittingProcedure
from census_household_sampling.census_household_sampling import CensusHouseholdSampling
from output_formatters.output_formatter import OutputFormatter

from input import InputParams
from global_tables import GlobalTables
from pums_data_tables import PUMSDataTables
from summary_data_tables import SummaryDataTables
from border_tables import BorderTables
from census_fitting_result import CensusFittingResult
from census_household_sampling_result import CensusHouseholdSamplingResult
from logger import setup_logger, log, data_log


def main():
    """
    main

    The main control module that defines the workflow of
    syntheco
    """
    parser = argparse.ArgumentParser(description="Synthco Command Line Parse")
    parser.add_argument(
        "-i", "--input_file", action="store", help="The input yaml file"
    )
    parser.add_argument(
        "-o",
        "--output_prefix",
        action="store",
        help="The prefix for the output files",
        default="syntheco_output",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Activates verbose output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Activates debugging output"
    )

    args = parser.parse_args()

    ip = InputParams(args.input_file)

    log_level = "INFO"
    if args.debug:
        log_level = "DEBUG"

    setup_logger(ip["output_log_file"], ip["output_data_log_file"], log_level)

    log(
        "INFO", "----------------------------------------------------------------------"
    )
    log("INFO", " Beginning SynthEco Run")
    log(
        "INFO", "----------------------------------------------------------------------"
    )
    log("INFO", "Input File = {}".format(args.input_file))
    log("INFO", "Input Params = {}".format(ip))

    data_log("----------------------------------------------------------------------")
    data_log(" Beginning SynthEco Run")
    data_log("----------------------------------------------------------------------")

    census_conv = ip["census_converter"]

    log("INFO", "Setting Up Global Converters")
    glob_table_conv = CensusConverter(ip, census_conv, "global")
    log("INFO", "Creating Global Tables")
    global_tables = GlobalTables(
        geo_unit_=ip["census_high_res_geo_unit"], converter_=glob_table_conv
    )

    log("INFO", "Global Tables Created")
    data_log(f"{global_tables}")

    log("INFO", "Setting Up Border Tables")
    bord_table_conv = CensusConverter(ip, census_conv, "border")
    log("INFO", "Border Converter Created")
    border_tables = BorderTables(
        geo_unit_=ip["census_high_res_geo_unit"], converter_=bord_table_conv
    )
    log("INFO", "Border Tables Created")

    log("INFO", "Setting up Census Converters")
    pums_table_conv = CensusConverter(ip, census_conv, "pums")
    summary_table_conv = CensusConverter(
        ip, census_conv, "summary", _global_tables=global_tables
    )
    log("INFO", "Creating Census Data Tables")
    summary_tables = SummaryDataTables(
        summary_variables_=ip["census_fitting_vars"],
        geo_unit_=ip["census_high_res_geo_unit"],
        converter_=summary_table_conv,
    )

    pums_heir_tables = PUMSDataTables(
        geo_unit_=ip["census_low_res_geo_unit"], converter_=pums_table_conv
    )
    log("INFO", "Done Setting Up Tables")

    data_log(f"{pums_heir_tables}")
    data_log(f"{summary_tables}")

    log("INFO", "Performing Census Fitting Procedure")
    census_fitting_procedure = CensusFittingProcedure(
        ip, global_tables, pums_heir_tables, summary_tables
    )
    census_fitting_result = CensusFittingResult(converter_=census_fitting_procedure)

    data_log(f"{census_fitting_result}")
    log("INFO", "Sampling Households from fitting results")
    census_household_sampling_proc = CensusHouseholdSampling(
        ip, census_fitting_result, pums_heir_tables, global_tables, border_tables
    )
    census_sampling_result = CensusHouseholdSamplingResult(
        sampling_proc_=census_household_sampling_proc
    )
    data_log(f"{census_sampling_result}")

    output_writer = OutputFormatter(ip, census_fitting_result, census_sampling_result)
    output_writer.write_output()


if __name__ == "__main__":
    main()
