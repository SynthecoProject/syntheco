"""
hookspec

This module holds the specification for the plugins
and defines which members need to be implemented
"""

import pluggy
from output_formatters import hookspec


class OutputFormatterSpec:
    """
    OutputFormatterSpec

    Spec for the output formatting plugins
    """

    @hookspec
    def preprocess(out_format_inst):
        """
        preprocess

        place for processing that needs to occur before writing outputs

        This is templated with a keyword that is requered to be
        self when passed in through the class
        """

        return

    @hookspec
    def output(out_format_inst):
        """
        output

        Function that writes output.

        This is templated with a keyword that is requered to be
        self when passed in through the class
        """

        return
