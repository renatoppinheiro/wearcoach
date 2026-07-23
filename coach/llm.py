"""Thin provider switch: Anthropic (Claude) or OpenAI (GPT). Pick with
LLM_PROVIDER in .env; only that provider's key is required."""
from __future__ import annotations

from . import config

SYSTEM_PROMPT = (
    "You are a supportive, data-driven running/endurance coach. You are NOT a "
    "medical professional and must never give clinical or nutrition advice. "
    "If wellness data suggests overreaching, illness, or pain, your first "
    "instruction is always to scale the session down or rest, and to see a "
    "doctor for anything that looks medical. Be concise, specific, and cite "
    "the numbers you were given."
)


def ask(prompt: str) -> str:
    provider = (config.env("LLM_PROVIDER") or "anthropic").lower()
    if provider == "anthropic":
        return _ask_anthropic(prompt)
    if provider == "openai":
        return _ask_openai(prompt)
    raise SystemExit(f"Unknown LLM_PROVIDER '{provider}' — use 'anthropic' or 'openai'.")


def _ask_anthropic(prompt: str) -> str:
    missing = config.require_env("ANTHROPIC_API_KEY")
    if missing:
        raise SystemExit("Set ANTHROPIC_API_KEY in .env (get one at console.anthropic.com).")
    import anthropic

    client = anthropic.Anthropic(api_key=config.env("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=config.env("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def _ask_openai(prompt: str) -> str:
    missing = config.require_env("OPENAI_API_KEY")
    if missing:
        raise SystemExit("Set OPENAI_API_KEY in .env (get one at platform.openai.com).")
    from openai import OpenAI

    client = OpenAI(api_key=config.env("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=config.env("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content
