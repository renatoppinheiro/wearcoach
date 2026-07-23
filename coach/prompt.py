"""Compose the daily briefing prompt from whatever sources are connected."""
from __future__ import annotations

import json


def build(activities: list[dict], wellness: list[dict], wellness_source: str | None) -> str:
    parts = [
        "Here is my recent training and wellness data. Give me a short "
        "coaching briefing for today: how I'm recovering, whether to go "
        "hard/easy/rest today, and one thing to watch this week.\n",
        "## Recent activities (last 7-14 days)",
        json.dumps(activities, indent=2, ensure_ascii=False) if activities else "(none synced)",
    ]

    if wellness_source:
        parts += [
            f"\n## Wellness ({wellness_source})",
            json.dumps(wellness, indent=2, ensure_ascii=False) if wellness else "(no data yet)",
        ]
    else:
        parts.append(
            "\n## Wellness\nNo wearable wellness connected — base the call on "
            "training load/frequency and ask me how I'm feeling (sleep, "
            "soreness, energy) if it matters for today's call."
        )

    return "\n".join(parts)
