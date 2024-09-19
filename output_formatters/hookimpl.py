"""
hookimpl

This module defines the plugin speck default implementation
"""

from output_formatters import hookimpl


class OutputFormattersSpec:
    """
    OutputFormattersSpec

    wrapper class that defines the implmentation hooks for Plugins
    """

    @hookimpl
    def preprocess(out_format_inst):
        """
        preprocess implementation spec
        """
        return

    @hookimpl
    def output(cens_conv_inst):
        """
        output implementation spec
        """

    return
