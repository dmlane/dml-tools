"""Utility functions"""

import base64
import os

HOST_DB_PATH = os.path.join(os.environ["HOME"], ".dropbox/host.db")


def get_dropbox_folder_location():
    """
    Try to locate the Dropbox folder.

    Returns:
        (str) Full path to the current Dropbox folder
    """
    if not os.path.exists(HOST_DB_PATH):
        raise FileNotFoundError(HOST_DB_PATH)
    with open(HOST_DB_PATH, "r") as f_hostdb:  # pylint: disable=unspecified-encoding
        data = f_hostdb.read().split()

    dropbox_home = base64.b64decode(data[1]).decode()

    return dropbox_home
