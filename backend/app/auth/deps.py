"""FastAPI dependencies for reading the current user off the session cookie."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as DbSession

from app.api.search import get_session
from app.auth.service import SESSION_COOKIE, user_for_session_token
from app.models import User


def optional_user(request: Request, session: DbSession = Depends(get_session)) -> User | None:
    return user_for_session_token(session, request.cookies.get(SESSION_COOKIE))


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user
