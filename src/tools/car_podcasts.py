#!/usr/bin/env python3
""" Fetches X hours of podcasts from source into local directory """

import argparse
from importlib.metadata import version

from . import RawFormatter


class CarPodcasts:  # pylint: disable=too-few-public-methods
    """Class to fetch podcasts from dropbox folder into local directory"""

    parser = None

    def __init__(self):
        pass

    def make_cmd_line_parser(self):
        """Set up the command line parser"""
        self.parser = argparse.ArgumentParser(
            formatter_class=RawFormatter,
            description=(
                "Fetch a batch of files from my podcasts folder and put them into\n"
                "the target directory. The batch length is set in the config file."
            ),
        )
        self.parser.add_argument(
            "-V",
            "--version",
            action="version",
            version=version("dml-tools"),
            help="Print the version number",
        )
        self.parser.add_argument("mp3_file", required=True)


# logger = get_logger("podcasts.log", logging.INFO)
# logger.info("Start of car_podcasts run")
#
# POD_SOURCE = os.path.expanduser("~/Library/CloudStorage/Dropbox/OnDemand/Podcasts/mp3")
# POD_DEST = os.path.expanduser("~/Work/Podcasts4IOS")
# POD_BATCH_HOURS = 12
#
#
# class CustomError(Exception):
#     """Custom exception"""
#
#
# def main():
#     """Main entry point"""
#     try:
#         # source_dir = config.POD_SOURCE
#         source_dir = POD_SOURCE
#         if not os.path.isdir(source_dir):
#             raise CustomError(f"Directory {source_dir} does not exist")
#         # dest_dir = config.POD_DEST
#         dest_dir = POD_DEST
#
#         if not os.path.isdir(dest_dir):
#             os.makedirs(dest_dir)
#         # Total time of podcasts to be processed
#         # batch_seconds = int(config.POD_BATCH_HOURS) * 3600
#         batch_seconds = POD_BATCH_HOURS * 3600
#         # Get a list of eligible files
#         prefix_length = len(source_dir) + 1
#         eligible = glob.glob(f"{source_dir}/*/*.mp3")
#         eligible.sort(key=os.path.basename)
#
#         total_duration = 0
#         for file_name in eligible:
#             # Force file to be local (won't work while Dropbox not updated)
#             dest_file = dest_dir + "/" + os.path.basename(file_name)
#
#             shutil.copy(file_name, dest_file)
#             #
#             duration = eyed3.load(dest_file).info.time_secs
#             total_duration += duration
#             if total_duration >= batch_seconds:
#                 os.remove(dest_file)
#                 break
#             logger.info("Added file %s", file_name[prefix_length:])
#             os.remove(file_name)
#
#     except Exception as inst:  # pylint: disable=broad-except
#         field = inst.args
#         logger.critical(field)
#         logger.critical(traceback.format_exc())
#         logger.critical("Aborting ??????????")
#
#     logger.info("End of run ++++++++++")
#
#
# if __name__ == "__main__":
#     main()
