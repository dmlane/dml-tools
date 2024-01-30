""" Test config functionality"""

import os

import mock

from tools.common import read_config

HOME = os.path.expanduser("~")

EXPECTED_CONFIG_DICT = {
    "batch_hours": "987",
    "dest": f"{HOME}/DIR_DEST",
    "dropbox": "/Users/dave/Library/CloudStorage/Dropbox",
    "extra": "ignore",
    "quarantine": f"{HOME}/Work/Podcasts4IOS.quarantine",
    "source": f"{HOME}/Library/CloudStorage/Dropbox/DIR_SOURCE",
}


def test_config_read_ok():
    """Test config read ok"""
    ini_path = os.path.dirname(os.path.realpath(__file__)) + "/testresources/test1.ini"
    dropbox_db_path = os.path.dirname(os.path.realpath(__file__)) + "/testresources/host.db"
    # Use a mock to ensure we always get the same location (even if no Dropbox installed)
    with mock.patch("tools.common.utils.HOST_DB_PATH", dropbox_db_path):
        xx = read_config("podcasts", ini_path=ini_path)
    assert xx == EXPECTED_CONFIG_DICT
