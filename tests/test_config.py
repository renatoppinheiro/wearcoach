"""Unit tests for coach.config. No network, no real .env touched."""
from __future__ import annotations

from coach import config


def test_env_reads_os_environ(monkeypatch):
    monkeypatch.setenv("WEARCOACH_TEST_KEY", "value")
    assert config.env("WEARCOACH_TEST_KEY") == "value"


def test_env_default_when_missing(monkeypatch):
    monkeypatch.delenv("WEARCOACH_TEST_MISSING", raising=False)
    assert config.env("WEARCOACH_TEST_MISSING") is None
    assert config.env("WEARCOACH_TEST_MISSING", "fallback") == "fallback"


def test_require_env_reports_missing(monkeypatch):
    monkeypatch.setenv("A", "1")
    monkeypatch.delenv("B", raising=False)
    monkeypatch.setenv("C", "")
    assert config.require_env("A", "B", "C") == ["B", "C"]


def test_require_env_empty_when_all_present(monkeypatch):
    monkeypatch.setenv("A", "1")
    monkeypatch.setenv("B", "2")
    assert config.require_env("A", "B") == []


def _isolate_paths(monkeypatch, tmp_path):
    root = tmp_path
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(config, "ENV_PATH", root / ".env")
    monkeypatch.setattr(config, "DATA_DIR", root / "data")
    monkeypatch.setattr(config, "TOKENS_DIR", root / "data" / "tokens")


def test_set_env_value_creates_env_from_example(monkeypatch, tmp_path):
    _isolate_paths(monkeypatch, tmp_path)
    (tmp_path / ".env.example").write_text("FOO=\nBAR=default\n", encoding="utf-8")

    config.set_env_value("FOO", "hello")

    content = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "FOO=hello" in content
    assert "BAR=default" in content  # rest of the example file preserved
    assert config.env("FOO") == "hello"


def test_set_env_value_updates_existing_key(monkeypatch, tmp_path):
    _isolate_paths(monkeypatch, tmp_path)
    (tmp_path / ".env").write_text("FOO=old\nOTHER=untouched\n", encoding="utf-8")

    config.set_env_value("FOO", "new")

    lines = (tmp_path / ".env").read_text(encoding="utf-8").splitlines()
    assert "FOO=new" in lines
    assert "OTHER=untouched" in lines
    assert lines.count("FOO=new") == 1  # not duplicated


def test_set_env_value_appends_new_key(monkeypatch, tmp_path):
    _isolate_paths(monkeypatch, tmp_path)
    (tmp_path / ".env").write_text("EXISTING=1\n", encoding="utf-8")

    config.set_env_value("NEWKEY", "v")

    lines = (tmp_path / ".env").read_text(encoding="utf-8").splitlines()
    assert "EXISTING=1" in lines
    assert "NEWKEY=v" in lines


def test_ensure_dirs_creates_tokens_dir(monkeypatch, tmp_path):
    _isolate_paths(monkeypatch, tmp_path)
    assert not (tmp_path / "data" / "tokens").exists()
    config.ensure_dirs()
    assert (tmp_path / "data" / "tokens").is_dir()
