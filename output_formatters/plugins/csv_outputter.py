"""
csv_outputter

This is the implementation of outputting CSV files for population outputs
"""

from output_formatters import hookimpl
from logger import log
from error import SynthEcoError


class CSVOutputter:
    """
    CSVOutputter

    This is the class that houses the implmementation hooks for writing out CSV results files
    """

    @hookimpl
    def preprocess(out_format_inst):
        """
        preprocess

        At this point, this function is a pass through as there are no preprocessing
        steps necessary for this outputter

        Arguments:
            out_format_inst: instance variable of OutputFomatter

        Returns:
            None as there is nothing to do
        """

        return {"preprocessed_output": None}

    @hookimpl
    def output(out_format_inst):
        try:
            log("INFO", "Outputting CSVs")
            ip = out_format_inst.input_params
            out_house_coords = f"{ip['output_prefix']}.households_coords.csv"
            out_households = f"{ip['output_prefix']}.households.csv"
            out_people = f"{ip['output_prefix']}.people.csv"

            out_format_inst.sampling_result.data[
                "Household Geographic Assignments"
            ].to_csv(out_house_coords, index=False)
            if isinstance(out_format_inst.fitting_result.data["Derived PUMS"], dict):
                out_format_inst.fitting_result.data["Derived PUMS"]["Person"].to_csv(
                    out_people, index=False
                )
                out_format_inst.fitting_result.data["Derived PUMS"]["Household"].to_csv(
                    out_households, index=False
                )
            else:
                out_format_inst.fitting_result.data["Derived PUMS"].to_csv(
                    out_people, index=False
                )
            log("INFO", "Successfully wrote CSVs")

            return True
        except Exception as e:
            raise SynthEcoError(f"CVSOutputter.output: unable to write files:\n{e}")
