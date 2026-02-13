from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.db.supabase import demo_store, fetch_curriculum, get_admin_client
from app.domain.curriculum import LESSONS
from app.services.exercise_engine import grade_submission
from app.services.progression import BADGES, completion_percentage, compute_level, update_streak

router = APIRouter(prefix="/api")
settings = get_settings()


class OnboardingPayload(BaseModel):
    display_name: str
    goal: str


class SubmissionPayload(BaseModel):
    lesson_id: str
    quiz_answer: str
    code: str


def _fetch_user_state(uid: str) -> dict:
    client = get_admin_client()
    if not client:
        progress_map = demo_store.user_progress.setdefault(uid, {})
        streak = demo_store.user_streak.setdefault(uid, {"current_streak": 0, "best_streak": 0, "last_activity_date": None})
        user = demo_store.users[uid]
        earned_badges = list(demo_store.user_badges.setdefault(uid, set()))
        history = demo_store.xp_history.setdefault(uid, [])
        completed = {lid for lid, row in progress_map.items() if row.get("is_completed")}
        return {
            "user": user,
            "progress_rows": list(progress_map.values()),
            "streak": streak,
            "badges": earned_badges,
            "history": history,
            "completion": completion_percentage(completed),
        }

    user = client.table("users").select("*").eq("id", uid).execute().data[0]
    progress_rows = client.table("user_progress").select("*").eq("user_id", uid).execute().data
    streak_rows = client.table("user_streak").select("*").eq("user_id", uid).execute().data
    badges_rows = client.table("user_badges").select("badges(id,name)").eq("user_id", uid).execute().data
    history = client.table("xp_history").select("*").eq("user_id", uid).order("created_at", desc=True).execute().data
    completed = {row["lesson_id"] for row in progress_rows if row.get("is_completed")}
    return {
        "user": user,
        "progress_rows": progress_rows,
        "streak": streak_rows[0] if streak_rows else {"current_streak": 0, "best_streak": 0, "last_activity_date": None},
        "badges": [row["badges"] for row in badges_rows if row.get("badges")],
        "history": history,
        "completion": completion_percentage(completed),
    }


@router.get("/public-config")
def public_config():
    return {"supabase_url": settings.supabase_url, "supabase_anon_key": settings.supabase_anon_key}


@router.get("/curriculum")
def curriculum(_: dict = CurrentUser):
    return fetch_curriculum()


@router.get("/dashboard")
def dashboard(user: dict = CurrentUser):
    state = _fetch_user_state(user["id"])
    return {
        "user": state["user"],
        "streak": state["streak"],
        "completion_pct": state["completion"],
        "total_xp": state["user"].get("total_xp", 0),
        "level": state["user"].get("current_level", 1),
        "completed_lessons": len([r for r in state["progress_rows"] if r.get("is_completed")]),
        "badges": state["badges"],
    }


@router.get("/profile")
def profile(user: dict = CurrentUser):
    state = _fetch_user_state(user["id"])
    return {
        "user": state["user"],
        "streak": state["streak"],
        "history": state["history"],
        "badges": state["badges"],
        "progress": state["progress_rows"],
    }


@router.post("/onboarding")
def complete_onboarding(payload: OnboardingPayload, user: dict = CurrentUser):
    uid = user["id"]
    client = get_admin_client()
    if not client:
        demo_store.users[uid]["display_name"] = payload.display_name.strip() or demo_store.users[uid]["display_name"]
        demo_store.users[uid]["goal"] = payload.goal
        demo_store.users[uid]["onboarding_completed"] = True
        return demo_store.users[uid]

    updated = (
        client.table("users")
        .update({"display_name": payload.display_name.strip(), "goal": payload.goal, "onboarding_completed": True})
        .eq("id", uid)
        .execute()
        .data[0]
    )
    return updated


@router.post("/submit")
def submit(payload: SubmissionPayload, user: dict = CurrentUser):
    lesson = next((l for l in LESSONS if l["id"] == payload.lesson_id), None)
    if not lesson:
        return {"success": False, "message": "Leçon introuvable."}

    if payload.quiz_answer != lesson["quiz"]["answer"]:
        return {"success": False, "message": "Quiz incorrect. Relis la leçon.", "xp_gain": 0}

    result = grade_submission(payload.code, lesson["exercise"]["expected_output"])
    if not result.is_correct:
        return {"success": False, "message": result.feedback, "output": result.output, "xp_gain": 0}

    uid = user["id"]
    xp_gain = lesson["exercise"]["xp"]
    client = get_admin_client()

    if not client:
        row = demo_store.user_progress.setdefault(uid, {}).get(payload.lesson_id, {})
        if row.get("is_completed"):
            return {"success": True, "message": "Déjà validé.", "output": result.output, "xp_gain": 0}

        demo_store.user_progress[uid][payload.lesson_id] = {
            "user_id": uid,
            "lesson_id": payload.lesson_id,
            "is_completed": True,
            "xp_earned": xp_gain,
            "completed_at": date.today().isoformat(),
        }
        profile = demo_store.users[uid]
        profile["total_xp"] += xp_gain
        profile["current_level"] = compute_level(profile["total_xp"])
        streak = update_streak(
            demo_store.user_streak[uid]["current_streak"],
            demo_store.user_streak[uid]["best_streak"],
            demo_store.user_streak[uid]["last_activity_date"],
        )
        demo_store.user_streak[uid].update(streak)
        demo_store.xp_history[uid].append({"reason": f"lesson:{payload.lesson_id}", "xp_delta": xp_gain, "created_at": date.today().isoformat()})
        for badge in BADGES:
            if profile["total_xp"] >= badge["rule_xp"]:
                demo_store.user_badges[uid].add(badge["id"])
        return {"success": True, "message": result.feedback, "output": result.output, "xp_gain": xp_gain}

    existing = (
        client.table("user_progress")
        .select("id,is_completed")
        .eq("user_id", uid)
        .eq("lesson_id", payload.lesson_id)
        .execute()
        .data
    )
    if existing and existing[0]["is_completed"]:
        return {"success": True, "message": "Déjà validé.", "output": result.output, "xp_gain": 0}

    client.table("user_progress").upsert(
        {"user_id": uid, "lesson_id": payload.lesson_id, "is_completed": True, "xp_earned": xp_gain, "completed_at": date.today().isoformat()},
        on_conflict="user_id,lesson_id",
    ).execute()

    user_row = client.table("users").select("total_xp").eq("id", uid).execute().data[0]
    new_xp = int(user_row["total_xp"]) + xp_gain
    client.table("users").update({"total_xp": new_xp, "current_level": compute_level(new_xp)}).eq("id", uid).execute()

    streak_row = client.table("user_streak").select("*").eq("user_id", uid).execute().data[0]
    streak = update_streak(streak_row["current_streak"], streak_row["best_streak"], streak_row["last_activity_date"])
    client.table("user_streak").update(streak).eq("user_id", uid).execute()

    client.table("xp_history").insert({"user_id": uid, "reason": f"lesson:{payload.lesson_id}", "xp_delta": xp_gain}).execute()

    for badge in BADGES:
        if new_xp >= badge["rule_xp"]:
            client.table("user_badges").upsert({"user_id": uid, "badge_id": badge["id"], "earned_at": date.today().isoformat()}, on_conflict="user_id,badge_id").execute()

    return {"success": True, "message": result.feedback, "output": result.output, "xp_gain": xp_gain}
