"""Test suite for CarPodcasts module using pytest."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

import tools.car_podcasts as cpr


@pytest.fixture(autouse=True)
def temp_dirs(monkeypatch, tmp_path):
    """
    Fixture to create temporary directories and patch configuration.

    Sets up a fake config for CarPodcasts to use temp paths.
    """
    config = {
        "batch_hours": "1",
        "source_rclone_remote": "test_remote",
        "dest": str(tmp_path / "dest"),
        "quarantine": str(tmp_path / "quarantine"),
    }
    # Patch read_config to return our test config
    monkeypatch.setattr(cpr, "read_config", lambda key: config)
    # Ensure tempdir points to tmp_path for predictable temp file location
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    return tmp_path


def test_list_remote_mp3s(monkeypatch):
    """
    Test that list_remote_mp3s filters and sorts mp3 files correctly.
    """
    sample = [
        {"Path": "a.mp3", "Name": "a.mp3", "IsDir": False},
        {"Path": "b.txt", "Name": "b.txt", "IsDir": False},
        {"Path": "sub/c.mp3", "Name": "c.mp3", "IsDir": False},
    ]
    completed = MagicMock()
    completed.stdout = json.dumps(sample)

    with patch("subprocess.run", return_value=completed) as mock_run:
        paths = cpr.list_remote_mp3s("fake:")
    mock_run.assert_called_once()
    # Expect only mp3 entries, sorted by basename
    assert sorted(paths) == sorted(["fake:/sub/c.mp3", "fake:/a.mp3"])


def test_empty_remote_listing(monkeypatch):
    """
    Test that listing when remote has no files returns an empty list.
    """
    completed = MagicMock()
    completed.stdout = json.dumps([])

    with patch("subprocess.run", return_value=completed):
        paths = cpr.list_remote_mp3s("fake:")
    assert paths == []


def test_quarantine_invalid_mp3(monkeypatch, tmp_path):
    """
    Test that invalid/corrupted mp3 files are moved to quarantine.
    """
    # Prepare fake remote file
    remote_name = "fake:bad.mp3"
    monkeypatch.setattr(cpr, "list_remote_mp3s", lambda remote: [remote_name])
    # No-op rclone copy
    # Create placeholder temp file for quarantine move
    temp_path = tmp_path / "podcast_tmp.mp3"
    temp_path.write_bytes(b"corrupt")
    monkeypatch.setattr(cpr.subprocess, "run", lambda *args, **kwargs: None)
    # eyed3.load returns None → invalid mp3
    monkeypatch.setattr(cpr.eyed3, "load", lambda path: None)

    car = cpr.CarPodcasts()
    car.make_parser()
    car.parse_args = lambda: None
    car.dry_run = False
    car.verbose = False
    car.hours = 1
    car.read_config()
    car.fetch_files()

    # Quarantine directory should contain 'bad.mp3'
    quarantined = os.listdir(car.quarantine)
    assert "bad.mp3" in quarantined


def test_dry_run_no_moves(monkeypatch, tmp_path):
    """
    Test that in dry-run mode, no files are moved or deleted.
    """
    remote_name = "fake:good.mp3"
    monkeypatch.setattr(cpr, "list_remote_mp3s", lambda remote: [remote_name])
    monkeypatch.setattr(cpr.subprocess, "run", lambda *args, **kwargs: None)
    fake_info = MagicMock(time_secs=30)
    fake_mp3 = MagicMock(info=fake_info)
    monkeypatch.setattr(cpr.eyed3, "load", lambda path: fake_mp3)

    car = cpr.CarPodcasts()
    car.make_parser()
    car.parse_args = lambda: None
    car.dry_run = True
    car.verbose = False
    car.hours = 1
    car.read_config()
    car.fetch_files()

    # No files should be moved in dry-run mode
    assert os.listdir(car.dest) == []
    assert os.listdir(car.quarantine) == []
