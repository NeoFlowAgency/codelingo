from datetime import date, timedelta

BADGES = [
    {"key": "starter", "label": "Premier pas", "xp": 20},
    {"key": "regular", "label": "Régulier", "xp": 80},
    {"key": "python_rookie", "label": "Python Rookie", "xp": 130},
]


def update_streak(current_streak: int, last_activity: str | None) -> tuple[int, str]:
    today = date.today()
    if not last_activity:
        return 1, today.isoformat()

    last = date.fromisoformat(last_activity)
    if last == today:
        return current_streak, last_activity
    if last == today - timedelta(days=1):
        return current_streak + 1, today.isoformat()
    return 1, today.isoformat()


def compute_badges(total_xp: int) -> list[str]:
    return [badge["key"] for badge in BADGES if total_xp >= badge["xp"]]
