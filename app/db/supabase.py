from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings
from app.domain.curriculum import LESSONS, MODULES

settings = get_settings()
_admin_client: Client | None = None


@dataclass
class DemoStore:
    users: dict[str, dict[str, Any]] = field(default_factory=dict)
    user_progress: dict[str, dict[str, Any]] = field(default_factory=dict)
    user_streak: dict[str, dict[str, Any]] = field(default_factory=dict)
    user_badges: dict[str, set[str]] = field(default_factory=dict)
    xp_history: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


demo_store = DemoStore()


def get_admin_client() -> Client | None:
    global _admin_client
    if _admin_client is None and settings.supabase_enabled:
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _admin_client


def get_user_from_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    client = get_admin_client()
    if not client:
        return {"id": "demo-user", "email": "demo@codelingo.dev"}

    response = client.auth.get_user(token)
    if not response or not response.user:
        return None
    return response.user.model_dump()


def ensure_user(user: dict[str, Any]) -> dict[str, Any]:
    uid = user["id"]
    email = user.get("email", "")

    client = get_admin_client()
    if not client:
        profile = demo_store.users.get(uid)
        if profile:
            return profile
        profile = {
            "id": uid,
            "email": email,
            "display_name": email.split("@")[0] if email else "CodeLearner",
            "avatar_seed": "bot",
            "onboarding_completed": False,
            "current_level": 1,
            "total_xp": 0,
            "created_at": date.today().isoformat(),
        }
        demo_store.users[uid] = profile
        demo_store.user_progress.setdefault(uid, {})
        demo_store.user_streak.setdefault(uid, {"current_streak": 0, "best_streak": 0, "last_activity_date": None})
        demo_store.user_badges.setdefault(uid, set())
        demo_store.xp_history.setdefault(uid, [])
        return profile

    existing = client.table("users").select("*").eq("id", uid).execute().data
    if existing:
        return existing[0]

    payload = {
        "id": uid,
        "email": email,
        "display_name": email.split("@")[0] if email else "CodeLearner",
        "avatar_seed": "bot",
        "onboarding_completed": False,
        "current_level": 1,
        "total_xp": 0,
    }
    client.table("users").insert(payload).execute()
    client.table("user_streak").insert({"user_id": uid}).execute()
    return client.table("users").select("*").eq("id", uid).execute().data[0]


def fetch_curriculum() -> dict[str, Any]:
    return {"modules": MODULES, "lessons": LESSONS}
