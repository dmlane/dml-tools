""" Help formatter for argparse"""

import argparse
import textwrap


class RawFormatter(argparse.HelpFormatter):
    """Help formatter to split the text on newlines and indent each line"""

    def _fill_text(self, text, width, indent):
        """Split the text on newlines and indent each line"""
        return "\n".join(
            [
                textwrap.fill(line, width)
                for line in textwrap.indent(textwrap.dedent(text), indent).splitlines()
            ]
        )
