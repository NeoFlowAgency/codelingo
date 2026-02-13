from __future__ import annotations

from datetime import date, timedelta

from app.domain.curriculum import LESSONS

BADGES = [
    {"id": "first-steps", "name": "Premier pas", "rule_xp": 25},
    {"id": "focused", "name": "Concentré", "rule_xp": 100},
    {"id": "python-rookie", "name": "Python Rookie", "rule_xp": 200},
]


def compute_level(total_xp: int) -> int:
    return max(1, total_xp // 80 + 1)


def update_streak(current_streak: int, best_streak: int, last_activity: str | None) -> dict:
    today = date.today()
    if not last_activity:
        return {"current_streak": 1, "best_streak": max(best_streak, 1), "last_activity_date": today.isoformat()}

    previous = date.fromisoformat(last_activity)
    if previous == today:
        return {"current_streak": current_streak, "best_streak": best_streak, "last_activity_date": last_activity}

    if previous == today - timedelta(days=1):
        next_streak = current_streak + 1
        return {"current_streak": next_streak, "best_streak": max(best_streak, next_streak), "last_activity_date": today.isoformat()}

    return {"current_streak": 1, "best_streak": best_streak, "last_activity_date": today.isoformat()}


def completion_percentage(completed_lesson_ids: set[str]) -> int:
    return int((len(completed_lesson_ids) / max(len(LESSONS), 1)) * 100)
