#!/usr/bin/env python3
""" Fetches X hours of podcasts from source into local directory """

import argparse
import glob
import os
import shutil
from importlib.metadata import version

import eyed3

from tools import Ansi, RawFormatter, read_config

LINE_LENGTH = os.get_terminal_size()[0]


class CarPodcasts:  # pylint: disable=too-few-public-methods
    """Class to fetch podcasts from dropbox folder into local directory"""

    parser = None
    verbose = False
    hours_per_batch = -1
    quarantine_dir = None
    source_dir = None
    dest_dir = None

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
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=False,
            help="Verbose output",
        )
        self.parser.add_argument(
            "-H",
            "--hours-per-batch",
            type=int,
            default=-1,
            help="Hours of podcasts to fetch",
        )

    def parse_args(self):
        """Parse the command line arguments"""
        args = self.parser.parse_args()

        self.verbose = args.verbose
        self.hours_per_batch = args.hours_per_batch

    def read_config(self):
        """Read the config file"""
        config = read_config("podcasts")
        if self.hours_per_batch == -1:
            self.hours_per_batch = int(config["batch_hours"])
        self.source_dir = config["source"]
        self.dest_dir = config["dest"]
        self.quarantine_dir = config["quarantine"]

    def get_sorted_eligible_files(self):
        """Return a list of files in date order that are eligible for processing"""
        eligible = glob.glob(f"{self.source_dir}/*/*.mp3")
        eligible.sort(key=os.path.basename)
        return eligible

    def fetch_files(self):
        """Fetch the files up to the specified hours of podcasts"""
        print(f"Fetching {self.hours_per_batch} hours of podcasts -----------")
        remaining_seconds = self.hours_per_batch * 3600
        eligible = self.get_sorted_eligible_files()
        temp_copy = os.path.join(self.dest_dir, "temp_copy.mp3")
        num_files = 0
        os.makedirs(self.dest_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)

        # Raise eyed3 logging errors to avoid spamming the console
        # Examples of messages suppressed are:-
        #       Lame tag CRC check failed
        #       Invalid date: 2023-06-13T02:24:07.000Z
        eyed3.log.setLevel("ERROR")

        for original_file in eligible:
            short_name = original_file.replace(self.source_dir, "")[1:]
            if len(short_name) > LINE_LENGTH:
                display_name = short_name[: LINE_LENGTH - 4] + "...."
            else:
                display_name = short_name
            # Give the user something to see while we're doing a slow fetch
            print(f"{Ansi.LIGHT_GREY}{display_name}", end="\r")
            shutil.copyfile(original_file, temp_copy)
            mp3_file = eyed3.load(temp_copy)
            print(f"{Ansi.CLEAR_EOL}")
            if not mp3_file:
                print(f"{Ansi.RED}****{display_name}****\n - moving it to quarantine", end="")
                dest_file = os.path.join(self.quarantine_dir, os.path.basename(original_file))
                run_length = 0
            else:
                dest_file = os.path.join(self.dest_dir, os.path.basename(original_file))
                run_length = int(mp3_file.info.time_secs)
                print(
                    f"{Ansi.GREEN}{display_name}\n    with length of {run_length} seconds ", end=""
                )
            remaining_seconds -= run_length
            if remaining_seconds <= 0:
                os.remove(temp_copy)
                print(f"{Ansi.YELLOW}- exceeds the batch limit{Ansi.NC}")
                remaining_seconds += run_length
                break

            os.rename(temp_copy, dest_file)
            # os.remove(original_file)
            num_files += 1
            print(f"- successfully copied{Ansi.NC}")
        total_time = (self.hours_per_batch * 3600) - remaining_seconds
        hours = int(total_time / 3600)
        minutes = int((total_time % 3600) / 60)
        seconds = int((total_time % 3600) % 60)

        print(
            f"{Ansi.GREEN}I have added {Ansi.YELLOW}{num_files} files{Ansi.GREEN} "
            f"to {self.dest_dir} (Duration"
            f" {Ansi.YELLOW}{hours:02d}:{minutes:02d}:{seconds:02d}){Ansi.NC}"
        )

    # def main(self):
    #     """Main entry point"""
    #     self.make_cmd_line_parser()
    #     self.parse_args()
    #     self.read_config()
    #     self.fetch_files()


def main():
    """Main entry point"""
    car_podcasts = CarPodcasts()
    car_podcasts.make_cmd_line_parser()
    car_podcasts.parse_args()
    car_podcasts.read_config()
    car_podcasts.fetch_files()
