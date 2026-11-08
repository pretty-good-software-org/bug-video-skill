"""Behavior of record-maestro-run's step reading, which decides what text reaches the video."""

from __future__ import annotations

import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/maestro-bug-video/scripts/record-maestro-run"


def load_script():
    loader = SourceFileLoader("record_maestro_run", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    # Bytecode would land in __pycache__ inside the distributed skill directory.
    writes_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes_bytecode

    return module


record = load_script()


def command_entry(kind, body, **metadata):
    """One commands.json entry: Maestro sets every other command kind to null."""
    defaults = {"duration": 0, "status": "COMPLETED", "depth": 0}

    return {"command": {"otherCommand": None, kind: body}, "metadata": defaults | metadata}


@pytest.mark.parametrize(
    ("kind", "body", "expected"),
    [
        (
            "inputTextCommand",
            {"label": "Type the password", "text": "hunter2"},
            "Type the password",
        ),
        ("launchAppCommand", {"appId": "com.example.notes"}, "Launch com.example.notes"),
        ("tapOnElement", {"selector": {"textRegex": "Save"}}, 'Tap on "Save"'),
        ("tapOnElement", {"selector": {"idRegex": "save_button"}}, "Tap on id save_button"),
        ("tapOnElement", {"selector": {}}, "Tap on the element"),
        ("inputTextCommand", {"text": "${MAESTRO_PASSWORD}"}, "Input ${MAESTRO_PASSWORD}"),
        ("eraseTextCommand", {}, "Erase the text field"),
        ("hideKeyboardCommand", {}, "Hide the keyboard"),
        ("swipeCommand", {}, "Swipe"),
        (
            "scrollUntilVisible",
            {"selector": {"textRegex": "Settings"}},
            'Scroll until "Settings" is visible',
        ),
        ("setAirplaneModeCommand", {"value": "Enable"}, "Enable airplane mode"),
        (
            "assertConditionCommand",
            {"condition": {"visible": {"idRegex": "shift"}}},
            "id shift is visible",
        ),
        (
            "assertConditionCommand",
            {"condition": {"notVisible": {"idRegex": "shift"}}},
            "id shift is not visible",
        ),
        ("assertConditionCommand", {"condition": {}}, "assertCondition"),
        ("backPressCommand", {}, "backPress"),
    ],
)
def test_describe_uses_the_label_or_the_command_as_written(kind, body, expected):
    text = record.describe(kind, body)

    assert text == expected, f"{kind} {body} described as {text!r}, expected {expected!r}"


def test_read_steps_skips_bookkeeping_and_nested_commands(tmp_path):
    commands_json = tmp_path / "commands.json"
    entries = [
        command_entry("defineVariablesCommand", {}, timestamp=1_000_100),
        command_entry("launchAppCommand", {"appId": "com.example.notes"}, timestamp=1_000_500),
        command_entry("tapOnElement", {"label": "Inside runFlow"}, timestamp=1_001_000, depth=1),
        command_entry("stopRecordingCommand", {}, timestamp=1_002_000),
    ]
    commands_json.write_text(json.dumps(entries))

    steps = record.read_steps(commands_json, started_at_ms=1_000_000)

    texts = [step.text for step in steps]
    assert texts == ["Launch com.example.notes"], f"unexpected steps {texts}"


def test_read_steps_times_each_step_from_the_recording_start(tmp_path):
    commands_json = tmp_path / "commands.json"
    entries = [
        command_entry(
            "assertConditionCommand",
            {"label": "Expected: the keyboard closes – it stays open"},
            timestamp=1_003_000,
            duration=250,
            status="WARNED",
        ),
    ]
    commands_json.write_text(json.dumps(entries))

    steps = record.read_steps(commands_json, started_at_ms=1_000_000)

    expected = [
        record.Step("Expected: the keyboard closes – it stays open", 3.0, 3.25, "WARNED"),
    ]
    assert steps == expected, f"steps {steps}, expected {expected}"


def test_find_commands_json_ignores_the_debug_output_copy(tmp_path):
    run_file = tmp_path / "2026-11-08_120000" / "commands-(flow.yaml).json"
    debug_file = tmp_path / "debug" / "commands-(flow.yaml).json"
    for path in (run_file, debug_file):
        path.parent.mkdir(parents=True)
        path.write_text("[]")

    found = record.find_commands_json(tmp_path)

    assert found == run_file, f"found {found}, expected the run's own {run_file}"


def test_find_commands_json_rejects_a_run_without_one(tmp_path):
    with pytest.raises(RuntimeError) as error:
        record.find_commands_json(tmp_path)

    assert str(error.value) == (
        f"record-maestro-run: expected one commands.json under {tmp_path}, found 0"
    )


def test_find_fonts_falls_back_to_the_first_complete_pair(tmp_path):
    macos = record.Fonts(tmp_path / "Arial.ttf", tmp_path / "Arial Bold.ttf")
    linux = record.Fonts(tmp_path / "DejaVuSans.ttf", tmp_path / "DejaVuSans-Bold.ttf")
    for path in (macos.regular, linux.regular, linux.bold):
        path.write_bytes(b"")

    fonts = record.find_fonts([macos, linux])

    assert fonts == linux, f"chose {fonts}, expected the complete Linux pair {linux}"


def test_find_fonts_rejects_a_system_without_any_pair(tmp_path):
    macos = record.Fonts(tmp_path / "Arial.ttf", tmp_path / "Arial Bold.ttf")

    with pytest.raises(RuntimeError) as error:
        record.find_fonts([macos])

    assert str(error.value) == (
        "record-maestro-run: no fonts found; install Arial (macOS) or DejaVu Sans (Linux)"
    )


def test_the_video_starts_when_the_first_step_starts():
    steps = [
        record.Step("Open the app", 6.5, 7.25, "COMPLETED"),
        record.Step("Tap Save", 7.5, 8.0, "COMPLETED"),
    ]

    lead_in = record.seconds_before_first_step(steps)

    assert lead_in == 6.5, f"lead-in {lead_in}, expected the first step's start, 6.5"


def test_a_first_step_timed_before_the_recording_cuts_nothing():
    steps = [record.Step("Open the app", -0.25, 0.5, "COMPLETED")]

    lead_in = record.seconds_before_first_step(steps)

    assert lead_in == 0.0, f"lead-in {lead_in}, expected 0.0"


def test_a_run_without_steps_renders_nothing():
    with pytest.raises(RuntimeError) as error:
        record.seconds_before_first_step([])

    assert str(error.value) == (
        "record-maestro-run: Maestro ran no steps, so there is nothing to show"
    )


def test_a_shifted_step_is_timed_from_the_trimmed_start():
    step = record.Step("Open the app", 6.5, 7.25, "COMPLETED")

    shifted = step.shifted(6.5)

    assert shifted == record.Step("Open the app", 0.0, 0.75, "COMPLETED"), f"got {shifted}"


def test_a_trimmed_recording_drops_the_lead_in():
    recording = record.Recording(Path("screen.mp4"), 12.0, 1_000)

    trimmed = recording.trimmed(6.5)

    assert trimmed == record.Recording(Path("screen.mp4"), 5.5, 1_000, 6.5), f"got {trimmed}"


def test_the_device_screen_starts_where_the_recording_was_trimmed():
    recording = record.Recording(Path("screen.mp4"), 5.5, 1_000, 6.5)

    filters = record.filters_with_screen(["color=c=black[canvas]", "drawtext=text=x"], recording)

    assert filters[0] == (
        "[0:v]trim=start=6.500,setpts=PTS-STARTPTS,fps=30,scale=-2:984,"
        "tpad=stop_mode=clone:stop_duration=5.500,trim=duration=5.500[screen]"
    ), f"screen chain {filters[0]}"
