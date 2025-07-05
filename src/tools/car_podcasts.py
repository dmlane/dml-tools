#!/usr/bin/env python3
"""Fetch X hours of podcasts from remote storage via rclone into local directory."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from importlib.metadata import version
from typing import List

import eyed3

from tools import Ansi, RawFormatter, read_config

LINE_LENGTH = 100


def list_remote_mp3s(remote: str) -> List[str]:
    """
    List remote mp3 files via rclone and return sorted full remote paths.

    Args:
        remote: The rclone remote name (e.g., "dropbox:Podcasts").

    Returns:
        A list of strings representing remote file paths sorted by basename.
    """

    try:
        result = subprocess.run(
            ["rclone", "lsjson", remote, "--recursive"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"{Ansi.RED}ERROR listing remote '{remote}':{Ansi.CLEAR_EOL}")
        print(e.stderr or e)
        return []
    entries = json.loads(result.stdout)
    mp3_entries = [
        e for e in entries if not e.get("IsDir", False) and e.get("Name", "").endswith(".mp3")
    ]
    paths = [f"{remote}/{e['Path']}" for e in mp3_entries]
    paths.sort(key=os.path.basename)
    return paths


def format_display(name: str) -> str:
    """
    Shorten filename for display if it exceeds LINE_LENGTH characters.

    Args:
        name: The filename or path string to format.

    Returns:
        A possibly truncated string ending with '....' if it was too long.
    """
    if len(name) > LINE_LENGTH:
        return name[: LINE_LENGTH - 4] + "...."
    return name


class CarPodcasts:
    """
    Fetch podcasts from a remote store into local via rclone.

    Attributes:
        verbose: Whether to enable verbose output.
        hours: Number of hours to fetch each batch.
        dry_run: If True, show actions without performing copy/delete.
        remote: The rclone remote identifier.
        dest: Local destination directory.
        quarantine: Local quarantine directory for bad files.
    """

    def __init__(self) -> None:
        """Initialize CarPodcasts with default values."""
        self.quarantine = None
        self.dest = None
        self.remote = None
        self.parser = None
        self.parser: argparse.ArgumentParser
        self.verbose = False
        self.hours = -1
        self.dry_run = False
        self.remote: str
        self.dest: str
        self.quarantine: str

    def make_parser(self) -> None:
        """Set up the command-line argument parser."""
        p = argparse.ArgumentParser(
            formatter_class=RawFormatter,
            description="Fetch a batch of files from remote storage into the target dir.",
        )
        p.add_argument(
            "-V",
            "--version",
            action="version",
            version=version("dml-tools"),
            help="Print the version number",
        )
        p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
        p.add_argument(
            "-H",
            "--hours-per-batch",
            type=int,
            default=-1,
            help="Hours of podcasts to fetch",
        )
        p.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            help="Show actions without copying or deleting files",
        )
        self.parser = p

    def parse_args(self) -> None:
        """Parse CLI arguments into object attributes."""
        args = self.parser.parse_args()
        self.verbose = args.verbose
        self.hours = args.hours_per_batch
        self.dry_run = args.dry_run

    def read_config(self) -> None:
        """
        Load configuration values for remote, dest, and batch size.

        Reads 'source_rclone_remote' from config and expands user home in paths.
        """
        cfg = read_config("podcasts")
        if self.hours < 0:
            self.hours = int(cfg.get("batch_hours", 0))
        self.remote = cfg["source_rclone_remote"]
        self.dest = os.path.expanduser(cfg.get("dest", ""))
        self.quarantine = os.path.expanduser(cfg.get("quarantine", ""))

    def process_file(self, remote_path: str) -> int:
        """
        Fetch, analyze, and move a single mp3. Returns its duration in seconds.

        Args:
            remote_path: The full rclone remote path to the mp3.

        Returns:
            The duration of the mp3 in seconds, or 0 if invalid/quarantined
            or in dry-run mode.
        """
        name = remote_path.split(":", 1)[1]
        disp = format_display(name)
        print(f"{Ansi.LIGHT_GREY}{disp}", end="\r")

        # Prepare temp path
        temp = os.path.join(tempfile.gettempdir(), "podcast_tmp.mp3")

        # --- 1) Dry-run: print and return 0 immediately ---
        if self.dry_run:
            print(Ansi.CLEAR_EOL)
            return 0

        # Copy down for real
        try:
            subprocess.run(
                ["rclone", "copyto", remote_path, temp],
                check=True,
                capture_output=not self.verbose,
            )
        except subprocess.CalledProcessError as e:
            print(f"{Ansi.RED}Failed to download {disp}:{Ansi.CLEAR_EOL}")
            print(e.stderr or e)
            # quarantine the path string (no temp file)
            open(os.path.join(self.quarantine, os.path.basename(name)), "wb").close()
            return 0
        print(Ansi.CLEAR_EOL)
        mp3_file = eyed3.load(temp)

        # --- 2) Invalid/corrupted files → quarantine + return 0 ---
        if not mp3_file:
            print(f"{Ansi.RED}{disp}\n - quarantine", end="")
            dest_path = os.path.join(self.quarantine, os.path.basename(name))
            shutil.move(temp, dest_path)
            return 0

        # --- 3) Valid file: move to dest, delete remote, return duration ---
        duration = int(mp3_file.info.time_secs)
        print(f"{Ansi.GREEN}{disp}\n  length {duration}s", end="")
        dest_path = os.path.join(self.dest, os.path.basename(name))
        shutil.move(temp, dest_path)
        try:
            subprocess.run(["rclone", "deletefile", remote_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"{Ansi.RED}Warning: could not delete remote {remote_path}:{Ansi.CLEAR_EOL}")
            print(e.stderr or e)
        return duration

    def fetch_files(self) -> None:
        """
        Fetch files until the batch hour limit is reached, moving them locally.
        """
        prefix = "(dry-run) " if self.dry_run else ""
        print(f"{prefix}Fetching {self.hours}h of podcasts...")

        remaining = self.hours * 3600
        os.makedirs(self.dest, exist_ok=True)
        os.makedirs(self.quarantine, exist_ok=True)
        eyed3.log.setLevel("WARNING" if self.verbose else "ERROR")

        for path in list_remote_mp3s(self.remote):
            if remaining <= 0:
                print(f"{Ansi.YELLOW}limit reached{Ansi.NC}")
                break
            duration = self.process_file(path)
            remaining -= duration

        total = self.hours * 3600 - remaining
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if not self.dry_run:
            summary = f"Added files totalling {h:02d}:{m:02d}:{s:02d}"
        else:
            summary = f"Would process up to {h:02d}:{m:02d}:{s:02d}"
        print(f"{Ansi.GREEN}{summary}{Ansi.NC}")


def main() -> None:
    """Main entry point for the script."""
    car = CarPodcasts()
    car.make_parser()
    car.parse_args()
    car.read_config()
    car.fetch_files()


if __name__ == "__main__":
    main()
