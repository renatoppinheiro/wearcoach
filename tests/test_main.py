"""Unit tests for main.py's CLI wiring. Network-touching functions
(coach.strava/oura/garmin/llm) are monkeypatched — no real calls."""
from __future__ import annotations

import json

import pytest

import main
from coach import config


# --- argparse ----------------------------------------------------------------

def test_parser_no_command_defaults_to_none():
    args = main._build_parser().parse_args([])
    assert args.command is None


def test_parser_fetch_default_days():
    args = main._build_parser().parse_args(["fetch"])
    assert args.command == "fetch"
    assert args.days == 7


def test_parser_fetch_custom_days():
    args = main._build_parser().parse_args(["fetch", "--days", "14"])
    assert args.days == 14


def test_parser_brief_default_days():
    args = main._build_parser().parse_args(["brief"])
    assert args.command == "brief"
    assert args.days == 7


def test_parser_rejects_unknown_command():
    with pytest.raises(SystemExit):
        main._build_parser().parse_args(["bogus"])


# --- _fetch_all / cmd_fetch / cmd_brief --------------------------------------

@pytest.fixture(autouse=True)
def isolate_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "TOKENS_DIR", tmp_path / "data" / "tokens")


def test_fetch_all_prefers_oura_over_garmin(monkeypatch):
    monkeypatch.setattr(main.strava, "is_connected", lambda: True)
    monkeypatch.setattr(main.strava, "fetch_recent_activities", lambda days: [{"a": 1}])
    monkeypatch.setattr(main.oura, "is_connected", lambda: True)
    monkeypatch.setattr(main.oura, "fetch_recent_wellness", lambda days: [{"date": "x"}])
    monkeypatch.setattr(main.garmin, "is_connected", lambda: True)

    def garmin_should_not_be_called(days):
        raise AssertionError("garmin.fetch_recent_wellness should not be called when Oura is connected")

    monkeypatch.setattr(main.garmin, "fetch_recent_wellness", garmin_should_not_be_called)

    activities, wellness, source = main._fetch_all(7)

    assert activities == [{"a": 1}]
    assert wellness == [{"date": "x"}]
    assert source == "oura"


def test_fetch_all_no_wellness_connected(monkeypatch):
    monkeypatch.setattr(main.strava, "is_connected", lambda: True)
    monkeypatch.setattr(main.strava, "fetch_recent_activities", lambda days: [])
    monkeypatch.setattr(main.oura, "is_connected", lambda: False)
    monkeypatch.setattr(main.garmin, "is_connected", lambda: False)

    activities, wellness, source = main._fetch_all(7)

    assert wellness == []
    assert source is None


def test_cmd_fetch_raises_when_strava_not_connected(monkeypatch):
    monkeypatch.setattr(main.strava, "is_connected", lambda: False)
    with pytest.raises(SystemExit, match="not connected"):
        main.cmd_fetch(7)


def test_cmd_fetch_writes_snapshot(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(main.strava, "is_connected", lambda: True)
    monkeypatch.setattr(main.strava, "fetch_recent_activities", lambda days: [{"name": "Run"}])
    monkeypatch.setattr(main.oura, "is_connected", lambda: False)
    monkeypatch.setattr(main.garmin, "is_connected", lambda: False)

    main.cmd_fetch(7)

    files = list((tmp_path / "data").glob("snapshot-*.json"))
    assert len(files) == 1
    saved = json.loads(files[0].read_text(encoding="utf-8"))
    assert saved == {"activities": [{"name": "Run"}], "wellness": [], "wellness_source": None}
    assert "Fetched 1 activities" in capsys.readouterr().out


def test_cmd_brief_raises_when_strava_not_connected(monkeypatch):
    monkeypatch.setattr(main.strava, "is_connected", lambda: False)
    with pytest.raises(SystemExit, match="not connected"):
        main.cmd_brief(7)


def test_cmd_brief_writes_briefing_and_calls_llm(monkeypatch, tmp_path):
    monkeypatch.setattr(main.strava, "is_connected", lambda: True)
    monkeypatch.setattr(main.strava, "fetch_recent_activities", lambda days: [{"name": "Run"}])
    monkeypatch.setattr(main.oura, "is_connected", lambda: False)
    monkeypatch.setattr(main.garmin, "is_connected", lambda: False)

    captured_prompt = {}

    def fake_build(activities, wellness, source):
        captured_prompt["v"] = (activities, wellness, source)
        return "PROMPT"

    monkeypatch.setattr(main.prompt, "build", fake_build)
    monkeypatch.setattr(main.llm, "ask", lambda p: f"reply-to:{p}")

    main.cmd_brief(7)

    files = list((tmp_path / "data").glob("briefing-*.md"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "reply-to:PROMPT"
    assert captured_prompt["v"] == ([{"name": "Run"}], [], None)


# --- main() dispatch ---------------------------------------------------------

def test_main_fetch_days_out_of_range_exits(monkeypatch):
    monkeypatch.setattr(main.sys, "argv", ["main.py", "fetch", "--days", "0"])
    with pytest.raises(SystemExit, match="between 1 and 60"):
        main.main()


def test_main_brief_days_out_of_range_exits(monkeypatch):
    monkeypatch.setattr(main.sys, "argv", ["main.py", "brief", "--days", "999"])
    with pytest.raises(SystemExit, match="between 1 and 60"):
        main.main()


def test_main_keyboard_interrupt_returns_130(monkeypatch):
    monkeypatch.setattr(main.sys, "argv", ["main.py", "fetch"])

    def raise_interrupt(days):
        raise KeyboardInterrupt

    monkeypatch.setattr(main, "cmd_fetch", raise_interrupt)

    assert main.main() == 130


def test_main_generic_exception_becomes_clean_systemexit(monkeypatch):
    monkeypatch.setattr(main.sys, "argv", ["main.py", "fetch"])

    def raise_boom(days):
        raise ValueError("boom")

    monkeypatch.setattr(main, "cmd_fetch", raise_boom)

    with pytest.raises(SystemExit, match="Error: boom"):
        main.main()


def test_main_no_command_defaults_to_brief(monkeypatch):
    monkeypatch.setattr(main.sys, "argv", ["main.py"])
    calls = []
    monkeypatch.setattr(main, "cmd_brief", lambda days: calls.append(days))

    assert main.main() == 0
    assert calls == [7]
