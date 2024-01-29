""" Test utils functionality"""

import os

import mock

from tools.common.utils import get_dropbox_folder_location

# HOST_DB_PATH


def test_get_dropbox_location():
    """Test that we get correct location back"""
    dropbox_db_path = os.path.dirname(os.path.realpath(__file__)) + "/testresources/host.db"
    # Use a mock to ensure we always get the same location (even if no Dropbox installed)
    with mock.patch("tools.common.utils.HOST_DB_PATH", dropbox_db_path):
        dropbox_location = get_dropbox_folder_location()
    assert dropbox_location == "/Users/dave/Library/CloudStorage/Dropbox"
