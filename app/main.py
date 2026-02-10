from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import get_settings
from app.services.code_runner import validate_exercise
from app.services.gamification import update_streak
from app.services.seed_data import LESSON_MAP
from app.supabase_client import ensure_user_profile, get_lessons_with_progress, get_user_from_token, update_after_success

settings = get_settings()

app = FastAPI(title="CodeLingo Python")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class Submission(BaseModel):
    code: str


def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer", "").strip() if auth else ""
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ensure_user_profile(user)
    return user


@app.get("/", response_class=HTMLResponse)
def root() -> RedirectResponse:
    return RedirectResponse("/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/lessons", response_class=HTMLResponse)
def lessons_page(request: Request):
    return templates.TemplateResponse("lessons.html", {"request": request})


@app.get("/lessons/{slug}", response_class=HTMLResponse)
def lesson_detail_page(request: Request, slug: str):
    if slug not in LESSON_MAP:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse("lesson_detail.html", {"request": request, "slug": slug})


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/api/public-config")
def public_config():
    return {"supabase_url": settings.supabase_url, "supabase_anon_key": settings.supabase_anon_key}


@app.get("/api/bootstrap")
def bootstrap(user: dict = Depends(get_current_user)):
    lessons = get_lessons_with_progress(user["id"])
    profile = ensure_user_profile(user)
    completed = sum(1 for l in lessons if l["progress"].get("completed"))
    return {
        "user": {"id": user["id"], "email": user.get("email", "")},
        "profile": profile,
        "lessons": lessons,
        "stats": {
            "completed": completed,
            "total": len(lessons),
            "completion_pct": int((completed / max(len(lessons), 1)) * 100),
        },
    }


@app.get("/api/lessons")
def lessons_api(user: dict = Depends(get_current_user)):
    return get_lessons_with_progress(user["id"])


@app.get("/api/lessons/{slug}")
def lesson_api(slug: str, user: dict = Depends(get_current_user)):
    lessons = get_lessons_with_progress(user["id"])
    for lesson in lessons:
        if lesson["slug"] == slug:
            return lesson
    raise HTTPException(status_code=404, detail="Lesson not found")


@app.post("/api/exercises/{slug}/submit")
def submit_exercise(slug: str, payload: Submission, user: dict = Depends(get_current_user)):
    lesson = LESSON_MAP.get(slug)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    ok, output, feedback = validate_exercise(payload.code, lesson["exercise"])
    if not ok:
        return {"success": False, "feedback": feedback, "output": output}

    profile = ensure_user_profile(user)
    streak, last_activity = update_streak(profile.get("streak", 0), profile.get("last_activity"))
    updated = update_after_success(
        user_id=user["id"],
        lesson_slug=slug,
        xp_gain=lesson["exercise"]["xp"],
        streak=streak,
        last_activity=last_activity,
    )
    return {
        "success": True,
        "feedback": feedback,
        "output": output,
        "xp_gain": lesson["exercise"]["xp"],
        "profile": updated,
    }
