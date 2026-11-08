"""compose-bug-video's command-line errors, each produced through the script itself."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/maestro-bug-video/scripts/compose-bug-video"
FFMPEG_WITH_DRAWTEXT = 'case "$*" in *-filters*) echo " ... drawtext          V->V" ;; esac'
FFMPEG_WITHOUT_DRAWTEXT = 'case "$*" in *-filters*) echo " ... scale          V->V" ;; esac'
FFPROBE = "echo 1.0"
COMPLETE_TOOLS = {"ffmpeg": FFMPEG_WITH_DRAWTEXT, "ffprobe": FFPROBE}


def make_bin_dir(directory, stubs):
    """A PATH holding only the stub scripts and the system tools the script reaches first."""
    directory.mkdir()
    for name, body in stubs.items():
        stub = directory / name
        stub.write_text(f"#!/bin/sh\n{body}\n")
        stub.chmod(0o755)
    (directory / "sed").symlink_to(shutil.which("sed"))

    return directory


def run_compose(arguments, *, bin_dir, cwd):
    return subprocess.run(
        [shutil.which("bash"), str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        cwd=cwd,
        env={"PATH": str(bin_dir)},
        timeout=30,
    )


def explain_arguments(*extra):
    return [
        "explain",
        "--video",
        "run.mp4",
        "--title",
        "Notes · Editor",
        "--subtitle",
        "Bug: the keyboard stays open",
        "--caption",
        "The keyboard never closes.",
        "--out",
        "bug.mp4",
        *extra,
    ]


def test_without_a_mode_prints_usage_and_exits_2(tmp_path):
    bin_dir = make_bin_dir(tmp_path / "bin", COMPLETE_TOOLS)

    result = run_compose([], bin_dir=bin_dir, cwd=tmp_path)

    first_line = result.stderr.splitlines()[0]
    assert (result.returncode, first_line) == (
        2,
        "Turns local Maestro recordings into a video a person can follow: a title card, plain "
        "captions, and a held final frame.",
    ), result.stderr


@pytest.mark.parametrize(
    ("case", "stubs", "arguments", "expected_error"),
    [
        (
            "option without value",
            COMPLETE_TOOLS,
            ["explain", "--title"],
            "missing value for --title",
        ),
        (
            "unknown option",
            COMPLETE_TOOLS,
            ["explain", "--colour", "red"],
            "unknown option --colour",
        ),
        ("no ffmpeg", {"ffprobe": FFPROBE}, explain_arguments(), "ffmpeg not found"),
        ("no ffprobe", {"ffmpeg": FFMPEG_WITH_DRAWTEXT}, explain_arguments(), "ffprobe not found"),
        (
            "ffmpeg without drawtext",
            {"ffmpeg": FFMPEG_WITHOUT_DRAWTEXT, "ffprobe": FFPROBE},
            explain_arguments(),
            "this ffmpeg lacks the drawtext filter (needs libfreetype)",
        ),
        (
            "missing caption",
            COMPLETE_TOOLS,
            ["explain", "--video", "run.mp4", "--title", "T", "--subtitle", "S", "--out", "o.mp4"],
            "--title, --subtitle, --caption and --out are required",
        ),
        (
            "hold with a unit",
            COMPLETE_TOOLS,
            explain_arguments("--hold", "4s"),
            '--hold must be a number of seconds, got "4s"',
        ),
        (
            "explain without its recording",
            COMPLETE_TOOLS,
            [*explain_arguments()[:2], "missing.mp4", *explain_arguments()[3:]],
            '--video must be an existing recording, got "missing.mp4"',
        ),
        (
            "compare without the after recording",
            COMPLETE_TOOLS,
            ["compare", "--before", "run.mp4", "--after", "missing.mp4", *explain_arguments()[3:]],
            "--before and --after must be existing recordings",
        ),
    ],
)
def test_rejects_unusable_input_with_one_message(tmp_path, case, stubs, arguments, expected_error):
    bin_dir = make_bin_dir(tmp_path / "bin", stubs)
    (tmp_path / "run.mp4").write_bytes(b"")

    result = run_compose(arguments, bin_dir=bin_dir, cwd=tmp_path)

    assert (result.returncode, result.stderr) == (1, f"compose-bug-video: {expected_error}\n"), case
