#!/usr/bin/env python3
"""wearcoach — a local CLI running coach for Strava + Oura + Garmin.

    python main.py setup            interactive: pick coach mode, connect accounts
    python main.py fetch [--days N] pull recent activities + wellness to data/
    python main.py brief [--days N] fetch, then ask the LLM for today's briefing

Everything runs on your machine. Tokens/keys live in .env and data/tokens/
(gitignored) — nothing is sent anywhere except direct calls to Strava, Oura,
Garmin, and whichever LLM you picked.

DISCLAIMER: this is an AI coach, not a medical professional. Stop on pain.
You own your training decisions.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import date

if sys.version_info < (3, 10):
    sys.exit(f"wearcoach needs Python 3.10+ (found {sys.version.split()[0]}).")

try:
    from coach import config, garmin, llm, oura, prompt, strava
except ModuleNotFoundError as e:
    sys.exit(
        f"Missing dependency ({e.name}). Run:\n"
        f"  pip install -r requirements.txt"
    )


def _step(label: str) -> None:
    print(f"\n--- {label} ---")


def _prompt_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  (required — try again, or Ctrl+C to cancel)")


def _confirm(label: str, default_yes: bool) -> bool:
    hint = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"{label} {hint}: ").strip().lower()
    if not answer:
        return default_yes
    return answer == "y"


def _run_step(label: str, fn, *args) -> bool:
    """Run a connect step, catching failures so one bad account doesn't kill setup."""
    try:
        fn(*args)
        return True
    except SystemExit as e:
        print(f"  {label} not connected: {e}")
        return False
    except KeyboardInterrupt:
        raise
    except Exception as e:  # noqa: BLE001 — surface any provider error, keep wizard alive
        print(f"  {label} connection failed: {e}")
        return False


def cmd_setup() -> None:
    print(__doc__)
    _step("Coach mode")
    print("Recommended: use a coding agent you already have (Claude Code, Cursor,")
    print("Windsurf, Copilot, ...) — open this folder in it and just talk to it.")
    print("CLAUDE.md tells it what to do. No API key needed for this path.")
    uses_agent = _confirm("Will you use a coding agent as your coach?", default_yes=True)

    if uses_agent:
        print("Good — skipping LLM key setup. See README 'How to use it' section.")
    else:
        _step("LLM provider (for the standalone `python main.py brief` fallback)")
        provider = input("Use 'anthropic' (Claude) or 'openai' (GPT)? [anthropic]: ").strip().lower() or "anthropic"
        while provider not in ("anthropic", "openai"):
            provider = input("Please type 'anthropic' or 'openai': ").strip().lower()
        config.set_env_value("LLM_PROVIDER", provider)
        key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        if not config.env(key_name):
            config.set_env_value(key_name, _prompt_required(f"Paste your {key_name}"))

    _step("Strava (required)")
    strava_ok = False
    if _confirm("Connect Strava now?", default_yes=True):
        if config.require_env("STRAVA_CLIENT_ID"):
            config.set_env_value(
                "STRAVA_CLIENT_ID", _prompt_required("STRAVA_CLIENT_ID (from strava.com/settings/api)")
            )
        if config.require_env("STRAVA_CLIENT_SECRET"):
            config.set_env_value("STRAVA_CLIENT_SECRET", _prompt_required("STRAVA_CLIENT_SECRET"))
        strava_ok = _run_step("Strava", strava.connect)

    _step("Oura (optional, only if you own a ring)")
    if _confirm("Connect Oura now?", default_yes=False):
        if config.require_env("OURA_CLIENT_ID"):
            config.set_env_value(
                "OURA_CLIENT_ID", _prompt_required("OURA_CLIENT_ID (from cloud.ouraring.com/oauth/applications)")
            )
        if config.require_env("OURA_CLIENT_SECRET"):
            config.set_env_value("OURA_CLIENT_SECRET", _prompt_required("OURA_CLIENT_SECRET"))
        _run_step("Oura", oura.connect)

    _step("Garmin (optional; password only ever goes to Garmin's login)")
    if _confirm("Connect Garmin now?", default_yes=False):
        if config.require_env("GARMIN_EMAIL"):
            config.set_env_value("GARMIN_EMAIL", _prompt_required("Garmin email"))
        if config.require_env("GARMIN_PASSWORD"):
            import getpass
            password = getpass.getpass("Garmin password: ").strip()
            if not password:
                print("  (skipped — no password entered)")
            else:
                config.set_env_value("GARMIN_PASSWORD", password)
        _run_step("Garmin", garmin.connect)

    _step("Done")
    if not strava_ok:
        print("Strava isn't connected yet — re-run `python main.py setup` when ready, it's required.")
    print("Run: python main.py fetch")
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


def cmd_fetch(days: int) -> None:
    if not strava.is_connected():
        raise SystemExit("Strava not connected. Run: python main.py setup")

    activities, wellness, source = _fetch_all(days)
    config.ensure_dirs()
    out_path = config.DATA_DIR / f"snapshot-{date.today().isoformat()}.json"
    out_path.write_text(
        json.dumps({"activities": activities, "wellness": wellness, "wellness_source": source}, indent=2),
        encoding="utf-8",
    )
    print(f"Fetched {len(activities)} activities, {len(wellness)} wellness days ({source or 'none'}).")
    print(f"Saved to {out_path.relative_to(config.ROOT)}")


def cmd_brief(days: int) -> None:
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
    print(f"\nSaved to {out_path.relative_to(config.ROOT)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wearcoach", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("setup", help="connect accounts, pick coach mode")

    fetch_p = sub.add_parser("fetch", help="pull recent data to data/")
    fetch_p.add_argument("--days", type=int, default=7, help="days of history to pull (default 7)")

    brief_p = sub.add_parser("brief", help="fetch + ask your coach for a briefing")
    brief_p.add_argument("--days", type=int, default=7, help="days of history to pull (default 7)")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    command = args.command or "brief"

    try:
        if command == "setup":
            cmd_setup()
        elif command == "fetch":
            if args.days < 1 or args.days > 60:
                sys.exit("--days must be between 1 and 60")
            cmd_fetch(args.days)
        elif command == "brief":
            days = getattr(args, "days", 7)
            if days < 1 or days > 60:
                sys.exit("--days must be between 1 and 60")
            cmd_brief(days)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — top-level: clean message beats a raw traceback
        sys.exit(f"Error: {e}")

    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "buffer"):  # Windows console default (cp1252) mangles em-dashes etc.
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    raise SystemExit(main())
