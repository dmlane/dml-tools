""" Read config file"""

import os
from configparser import BasicInterpolation, ConfigParser

import appdirs

from tools.common.utils import get_dropbox_folder_location

CONFIG = os.path.join(appdirs.user_config_dir("net.dmlane"), "tools.ini")
VARS = {
    "DROPBOX": get_dropbox_folder_location(),
}


class EnvInterpolation(BasicInterpolation):  # pylint: disable=too-few-public-methods
    """Interpolation which expands environment variables in values."""

    def before_get(
        self, parser, section, option, value, defaults
    ):  # pylint: disable=too-many-arguments
        """Expand environment variables in values"""
        value = super().before_get(parser, section, option, value, defaults)

        return os.path.expanduser(value)


def read_config(section, ini_path=CONFIG):
    """Read config file - returning a dictionary of config values from section"""
    if not os.path.exists(ini_path):
        raise FileNotFoundError(ini_path)
    config = ConfigParser(
        interpolation=EnvInterpolation(),
        defaults=VARS,
        # {
        #     "DROPBOX": get_dropbox_folder_location(),
        # },
    )
    config.read(ini_path)
    return dict(config[section])


if __name__ == "__main__":
    xx = read_config("podcasts")
    print(xx)
