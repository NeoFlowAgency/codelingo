from fastapi import Depends, HTTPException, Request

from app.db.supabase import ensure_user, get_user_from_token


def get_current_user(request: Request) -> dict:
    token = request.headers.get("Authorization", "").replace("Bearer", "").strip()
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return ensure_user(user)


CurrentUser = Depends(get_current_user)
