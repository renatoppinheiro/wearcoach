"""Unit tests for coach.llm. No real network calls — SDK clients are faked."""
from __future__ import annotations

import pytest

from coach import llm


# --- ask() dispatch ---------------------------------------------------------

def test_ask_dispatches_to_anthropic(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(llm, "_ask_anthropic", lambda p: f"anthropic:{p}")
    assert llm.ask("hi") == "anthropic:hi"


def test_ask_dispatches_to_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm, "_ask_openai", lambda p: f"openai:{p}")
    assert llm.ask("hi") == "openai:hi"


def test_ask_defaults_to_anthropic_when_unset(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setattr(llm, "_ask_anthropic", lambda p: "used-default")
    assert llm.ask("hi") == "used-default"


def test_ask_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ANTHROPIC")
    monkeypatch.setattr(llm, "_ask_anthropic", lambda p: "ok")
    assert llm.ask("hi") == "ok"


def test_ask_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bard")
    with pytest.raises(SystemExit, match="Unknown LLM_PROVIDER"):
        llm.ask("hi")


# --- missing key guards ------------------------------------------------------

def test_ask_anthropic_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        llm._ask_anthropic("hi")


def test_ask_openai_missing_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        llm._ask_openai("hi")


# --- SDK call shape (client classes faked, no network) -----------------------

def test_ask_anthropic_builds_request_and_joins_text_blocks(monkeypatch):
    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "key")

    captured = {}

    class FakeBlock:
        def __init__(self, type_, text=""):
            self.type = type_
            self.text = text

    class FakeResp:
        content = [FakeBlock("text", "Hello "), FakeBlock("other"), FakeBlock("text", "coach")]

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return FakeResp()

    class FakeClient:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.messages = FakeMessages()

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)

    result = llm._ask_anthropic("what's my plan today")

    assert result == "Hello coach"
    assert captured["api_key"] == "key"
    assert captured["system"] == llm.SYSTEM_PROMPT
    assert captured["messages"] == [{"role": "user", "content": "what's my plan today"}]


def test_ask_openai_builds_request_and_returns_content(monkeypatch):
    import openai

    monkeypatch.setenv("OPENAI_API_KEY", "key")

    captured = {}

    class FakeMessage:
        content = "Hello from GPT"

    class FakeChoice:
        message = FakeMessage()

    class FakeResp:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return FakeResp()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.chat = FakeChat()

    monkeypatch.setattr(openai, "OpenAI", FakeClient)

    result = llm._ask_openai("what's my plan today")

    assert result == "Hello from GPT"
    assert captured["api_key"] == "key"
    assert captured["messages"][0] == {"role": "system", "content": llm.SYSTEM_PROMPT}
    assert captured["messages"][1] == {"role": "user", "content": "what's my plan today"}
