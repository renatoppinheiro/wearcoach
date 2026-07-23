#!/usr/bin/env python3
"""wearcoach — a local CLI running coach for Strava + Oura + Garmin.

    python main.py setup     interactive: pick LLM, connect Strava/Oura/Garmin
    python main.py fetch     pull recent activities + wellness to data/
    python main.py brief     fetch, then ask the LLM for today's briefing

Everything runs on your machine. Tokens/keys live in .env and data/tokens/
(gitignored) — nothing is sent anywhere except direct calls to Strava, Oura,
Garmin, and whichever LLM you picked.

DISCLAIMER: this is an AI coach, not a medical professional. Stop on pain.
You own your training decisions.
"""
from __future__ import annotations

import json
import sys
from datetime import date

from coach import config, garmin, llm, oura, prompt, strava


def cmd_setup() -> None:
    print(__doc__)
    print("\n--- Coach ---")
    print("Recommended: use a coding agent you already have (Claude Code, Cursor,")
    print("Windsurf, Copilot, ...) — open this folder in it and just talk to it.")
    print("CLAUDE.md tells it what to do. No API key needed for this path.")
    uses_agent = input("Will you use a coding agent as your coach? [Y/n]: ").strip().lower() != "n"
    if uses_agent:
        print("Good — skipping LLM key setup. See README 'How to use it' section.")
    else:
        print("\n--- LLM provider (for the standalone `python main.py brief` fallback) ---")
        provider = input("Use 'anthropic' (Claude) or 'openai' (GPT)? [anthropic]: ").strip() or "anthropic"
        config.set_env_value("LLM_PROVIDER", provider)
        key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        if not config.env(key_name):
            key = input(f"Paste your {key_name}: ").strip()
            if key:
                config.set_env_value(key_name, key)

    print("\n--- Strava (required) ---")
    if input("Connect Strava now? [Y/n]: ").strip().lower() != "n":
        if config.require_env("STRAVA_CLIENT_ID"):
            cid = input("STRAVA_CLIENT_ID (from strava.com/settings/api): ").strip()
            config.set_env_value("STRAVA_CLIENT_ID", cid)
        if config.require_env("STRAVA_CLIENT_SECRET"):
            secret = input("STRAVA_CLIENT_SECRET: ").strip()
            config.set_env_value("STRAVA_CLIENT_SECRET", secret)
        strava.connect()

    print("\n--- Oura (optional, only if you own a ring) ---")
    if input("Connect Oura now? [y/N]: ").strip().lower() == "y":
        if config.require_env("OURA_CLIENT_ID"):
            cid = input("OURA_CLIENT_ID (from cloud.ouraring.com/oauth/applications): ").strip()
            config.set_env_value("OURA_CLIENT_ID", cid)
        if config.require_env("OURA_CLIENT_SECRET"):
            secret = input("OURA_CLIENT_SECRET: ").strip()
            config.set_env_value("OURA_CLIENT_SECRET", secret)
        oura.connect()

    print("\n--- Garmin (optional; password only ever goes to Garmin's login) ---")
    if input("Connect Garmin now? [y/N]: ").strip().lower() == "y":
        if config.require_env("GARMIN_EMAIL"):
            config.set_env_value("GARMIN_EMAIL", input("Garmin email: ").strip())
        if config.require_env("GARMIN_PASSWORD"):
            import getpass
            config.set_env_value("GARMIN_PASSWORD", getpass.getpass("Garmin password: "))
        garmin.connect()

    print("\nSetup done. Run: python main.py fetch")
    if uses_agent:
        print("Then open this folder in your coding agent and ask for today's briefing.")
    else:
        print("Then run: python main.py brief")


def _fetch_all(days: int) -> tuple[list[dict], list[dict], str | None]:
    activities = strava.fetch_recent_activities(days) if strava.is_connected() else []

    wellness: list[dict] = []
    wellness_source = None
    if oura.is_connected():
        wellness = oura.fetch_recent_wellness(days)
        wellness_source = "oura"
    elif garmin.is_connected():
        wellness = garmin.fetch_recent_wellness(days)
        wellness_source = "garmin"

    return activities, wellness, wellness_source


def cmd_fetch(days: int = 7) -> None:
    activities, wellness, source = _fetch_all(days)
    config.ensure_dirs()
    out_path = config.DATA_DIR / f"snapshot-{date.today().isoformat()}.json"
    out_path.write_text(
        json.dumps({"activities": activities, "wellness": wellness, "wellness_source": source}, indent=2),
        encoding="utf-8",
    )
    print(f"Fetched {len(activities)} activities, {len(wellness)} wellness days ({source or 'none'}).")
    print(f"Saved to {out_path.relative_to(config.ROOT)}")


def cmd_brief(days: int = 7) -> None:
    if not strava.is_connected():
        raise SystemExit("Strava not connected. Run: python main.py setup")

    print("Fetching recent data...")
    activities, wellness, source = _fetch_all(days)

    print("Asking your coach...\n")
    text = llm.ask(prompt.build(activities, wellness, source))
    print(text)

    config.ensure_dirs()
    out_path = config.DATA_DIR / f"briefing-{date.today().isoformat()}.md"
    out_path.write_text(text, encoding="utf-8")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "brief"
    if cmd == "setup":
        cmd_setup()
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "brief":
        cmd_brief()
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
