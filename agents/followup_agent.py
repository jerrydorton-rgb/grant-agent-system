from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class FollowupAgent:
    def build(self, applications: list[dict[str, Any]]) -> list[dict[str, Any]]:
        today = datetime.utcnow().date()
        queue: list[dict[str, Any]] = []
        for app in applications:
            queue.append(
                {
                    "title": app["title"],
                    "source_name": app["source_name"],
                    "status": "drafted",
                    "followup_1": (today + timedelta(days=14)).isoformat(),
                    "followup_2": (today + timedelta(days=30)).isoformat(),
                    "followup_3": (today + timedelta(days=45)).isoformat(),
                    "recommended_message": "Confirm receipt, offer supplemental materials, and restate local business impact.",
                }
            )
        return queue
