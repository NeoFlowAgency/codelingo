from __future__ import annotations

from datetime import date
from typing import Any
from supabase import Client, create_client

from app.config import get_settings
from app.services.seed_data import LESSONS
from app.services.gamification import compute_badges

settings = get_settings()

_admin_client: Client | None = None


class InMemoryStore:
    def __init__(self) -> None:
        self.profiles: dict[str, dict[str, Any]] = {}
        self.progress: dict[str, dict[str, dict[str, Any]]] = {}


demo_store = InMemoryStore()


def get_admin_client() -> Client | None:
    global _admin_client
    if _admin_client is None and settings.supabase_enabled:
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _admin_client


def get_user_from_token(token: str) -> dict | None:
    if not token:
        return None
    client = get_admin_client()
    if not client:
        return {"id": "demo-user", "email": "demo@local.dev"}

    user_resp = client.auth.get_user(token)
    return user_resp.user.model_dump() if user_resp and user_resp.user else None


def ensure_user_profile(user: dict) -> dict:
    client = get_admin_client()
    uid = user["id"]
    email = user.get("email", "")

    if not client:
        profile = demo_store.profiles.get(uid)
        if not profile:
            profile = {
                "user_id": uid,
                "email": email,
                "total_xp": 0,
                "streak": 0,
                "last_activity": None,
                "badges": [],
            }
            demo_store.profiles[uid] = profile
            demo_store.progress[uid] = {}
        return profile

    existing = client.table("profiles").select("*").eq("user_id", uid).execute()
    if existing.data:
        return existing.data[0]

    profile = {
        "user_id": uid,
        "email": email,
        "total_xp": 0,
        "streak": 0,
        "last_activity": None,
        "badges": [],
    }
    client.table("profiles").insert(profile).execute()
    return profile


def get_lessons_with_progress(user_id: str) -> list[dict]:
    client = get_admin_client()
    if not client:
        user_prog = demo_store.progress.setdefault(user_id, {})
        enriched = []
        for lesson in LESSONS:
            progress = user_prog.get(lesson["slug"], {"completed": False, "xp_earned": 0})
            enriched.append({**lesson, "progress": progress})
        return enriched

    progress_rows = (
        client.table("progress")
        .select("lesson_slug, completed, xp_earned")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    progress_map = {row["lesson_slug"]: row for row in progress_rows}
    enriched = []
    for lesson in LESSONS:
        p = progress_map.get(lesson["slug"], {"completed": False, "xp_earned": 0})
        enriched.append({**lesson, "progress": p})
    return enriched


def update_after_success(user_id: str, lesson_slug: str, xp_gain: int, streak: int, last_activity: str) -> dict:
    client = get_admin_client()

    if not client:
        profile = demo_store.profiles[user_id]
        profile["total_xp"] += xp_gain
        profile["streak"] = streak
        profile["last_activity"] = last_activity
        profile["badges"] = compute_badges(profile["total_xp"])
        demo_store.progress[user_id][lesson_slug] = {
            "lesson_slug": lesson_slug,
            "completed": True,
            "xp_earned": xp_gain,
            "completed_at": date.today().isoformat(),
        }
        return profile

    profile_resp = client.table("profiles").select("*").eq("user_id", user_id).execute()
    profile = profile_resp.data[0]
    new_total = profile["total_xp"] + xp_gain
    badges = compute_badges(new_total)

    client.table("profiles").update(
        {
            "total_xp": new_total,
            "streak": streak,
            "last_activity": last_activity,
            "badges": badges,
        }
    ).eq("user_id", user_id).execute()

    client.table("progress").upsert(
        {
            "user_id": user_id,
            "lesson_slug": lesson_slug,
            "completed": True,
            "xp_earned": xp_gain,
            "completed_at": date.today().isoformat(),
        },
        on_conflict="user_id,lesson_slug",
    ).execute()

    updated = client.table("profiles").select("*").eq("user_id", user_id).execute()
    return updated.data[0]
