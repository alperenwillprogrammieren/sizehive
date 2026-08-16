"""Accounts: passwordless login, server-side Merkliste, Preisalarme, Suchagenten.

Everything here needs server-side identity, which is exactly why these
features couldn't exist in Paket 1 — a price alert has to be evaluated
while the browser is closed.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.api.schemas import (
    LoginRequest,
    PriceAlertIn,
    PriceAlertOut,
    PriceAlertsResponse,
    SearchAgentIn,
    SearchAgentOut,
    SearchAgentsResponse,
    UserResponse,
    VerifyRequest,
    WatchlistEntry,
    WatchlistEntryIn,
    WatchlistImportRequest,
    WatchlistResponse,
)
from app.api.search import get_session
from app.auth.deps import current_user, optional_user
from app.auth.service import (
    SESSION_COOKIE,
    consume_login_token,
    create_session,
    destroy_session,
    issue_login_link,
)
from app.auth.tokens import is_valid_email
from app.core.config import settings
from app.models import PriceAlert, SearchAgent, User, Variant, WatchlistItem

router = APIRouter()

MAX_AGENTS_PER_USER = 25
MAX_ALERTS_PER_USER = 200


def _to_alert(alert: PriceAlert) -> PriceAlertOut:
    return PriceAlertOut(
        id=alert.id,
        variant_id=alert.variant_id,
        target_price_eur=alert.target_price_cents / 100 if alert.target_price_cents is not None else None,
        active=alert.active,
        created_at=alert.created_at,
        last_notified_at=alert.last_notified_at,
    )


def _to_agent(agent: SearchAgent) -> SearchAgentOut:
    return SearchAgentOut(
        id=agent.id,
        name=agent.name,
        query=agent.query,
        active=agent.active,
        created_at=agent.created_at,
        last_run_at=agent.last_run_at,
    )


def _require_variant(session: DbSession, variant_id: int) -> None:
    if session.get(Variant, variant_id) is None:
        raise HTTPException(status_code=404, detail="variant not found")


# ----------------------------------------------------------------- Auth


@router.post("/auth/request-link", status_code=202)
def request_login_link(payload: LoginRequest, session: DbSession = Depends(get_session)):
    if not is_valid_email(payload.email):
        raise HTTPException(status_code=422, detail="invalid email address")

    issue_login_link(session, payload.email)
    # Always the same answer, whether the address is new, known, or just
    # rate-limited — the response must not reveal who has an account.
    return {"status": "sent"}


@router.post("/auth/verify", response_model=UserResponse)
def verify_login(payload: VerifyRequest, response: Response, session: DbSession = Depends(get_session)):
    user = consume_login_token(session, payload.token)
    if user is None:
        raise HTTPException(status_code=400, detail="login link invalid or expired")

    token = create_session(session, user)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )
    return UserResponse(email=user.email, created_at=user.created_at)


@router.get("/auth/me", response_model=UserResponse | None)
def me(user: User | None = Depends(optional_user)):
    if user is None:
        return None
    return UserResponse(email=user.email, created_at=user.created_at)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, session: DbSession = Depends(get_session)):
    # Delete the session server-side too — clearing only the cookie would
    # leave a token that still works if it was captured.
    destroy_session(session, request.cookies.get(SESSION_COOKIE))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


# ------------------------------------------------------------ Merkliste


@router.get("/account/watchlist", response_model=WatchlistResponse)
def get_watchlist(user: User = Depends(current_user), session: DbSession = Depends(get_session)):
    items = session.scalars(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.created_at.desc())
    ).all()
    return WatchlistResponse(
        items=[
            WatchlistEntry(
                variant_id=item.variant_id,
                price_eur_at_save=item.price_cents_at_save / 100 if item.price_cents_at_save is not None else None,
                created_at=item.created_at,
            )
            for item in items
        ]
    )


def _add_watchlist_item(session: DbSession, user: User, entry: WatchlistEntryIn) -> bool:
    """Returns True when a new row was created. Idempotent per variant."""
    existing = session.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id, WatchlistItem.variant_id == entry.variant_id
        )
    )
    if existing is not None:
        return False
    session.add(
        WatchlistItem(
            user_id=user.id,
            variant_id=entry.variant_id,
            price_cents_at_save=(
                round(entry.price_eur_at_save * 100) if entry.price_eur_at_save is not None else None
            ),
        )
    )
    return True


@router.post("/account/watchlist", status_code=201)
def add_to_watchlist(
    entry: WatchlistEntryIn,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    _require_variant(session, entry.variant_id)
    created = _add_watchlist_item(session, user, entry)
    session.commit()
    return {"created": created}


@router.post("/account/watchlist/import")
def import_watchlist(
    payload: WatchlistImportRequest,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    """One-way merge of the browser's local Merkliste into the account.

    Local-only entries are added; anything already on the server keeps its
    original `price_cents_at_save`, because that value is a historical
    measurement and overwriting it would falsify the "since you saved it"
    comparison.
    """
    known_ids = set(session.scalars(select(Variant.id).where(Variant.id.in_([e.variant_id for e in payload.items]))))
    imported = 0
    for entry in payload.items:
        if entry.variant_id in known_ids and _add_watchlist_item(session, user, entry):
            imported += 1
    session.commit()
    return {"imported": imported, "skipped": len(payload.items) - imported}


@router.delete("/account/watchlist/{variant_id}", status_code=204)
def remove_from_watchlist(
    variant_id: int,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    item = session.scalar(
        select(WatchlistItem).where(WatchlistItem.user_id == user.id, WatchlistItem.variant_id == variant_id)
    )
    if item is not None:
        session.delete(item)
        session.commit()
    return Response(status_code=204)


# --------------------------------------------------------- Preisalarme


@router.get("/account/alerts", response_model=PriceAlertsResponse)
def get_alerts(user: User = Depends(current_user), session: DbSession = Depends(get_session)):
    alerts = session.scalars(
        select(PriceAlert).where(PriceAlert.user_id == user.id).order_by(PriceAlert.created_at.desc())
    ).all()
    return PriceAlertsResponse(alerts=[_to_alert(a) for a in alerts])


@router.post("/account/alerts", response_model=PriceAlertOut, status_code=201)
def create_alert(
    payload: PriceAlertIn,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    _require_variant(session, payload.variant_id)
    if payload.target_price_eur is not None and payload.target_price_eur <= 0:
        raise HTTPException(status_code=422, detail="target price must be positive")

    target_cents = round(payload.target_price_eur * 100) if payload.target_price_eur is not None else None

    alert = session.scalar(
        select(PriceAlert).where(PriceAlert.user_id == user.id, PriceAlert.variant_id == payload.variant_id)
    )
    if alert is None:
        existing_count = session.scalar(
            select(func.count()).select_from(PriceAlert).where(PriceAlert.user_id == user.id)
        )
        if existing_count >= MAX_ALERTS_PER_USER:
            raise HTTPException(status_code=409, detail="alert limit reached")
        alert = PriceAlert(user_id=user.id, variant_id=payload.variant_id)
        session.add(alert)

    # Re-arm on every change: a new target invalidates the old dedup state.
    alert.target_price_cents = target_cents
    alert.active = True
    alert.last_notified_at = None
    alert.last_notified_price_cents = None
    session.commit()
    return _to_alert(alert)


@router.delete("/account/alerts/{variant_id}", status_code=204)
def delete_alert(
    variant_id: int,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    alert = session.scalar(
        select(PriceAlert).where(PriceAlert.user_id == user.id, PriceAlert.variant_id == variant_id)
    )
    if alert is not None:
        session.delete(alert)
        session.commit()
    return Response(status_code=204)


# ---------------------------------------------------------- Suchagenten


@router.get("/account/agents", response_model=SearchAgentsResponse)
def get_agents(user: User = Depends(current_user), session: DbSession = Depends(get_session)):
    agents = session.scalars(
        select(SearchAgent).where(SearchAgent.user_id == user.id).order_by(SearchAgent.created_at.desc())
    ).all()
    return SearchAgentsResponse(agents=[_to_agent(a) for a in agents])


@router.post("/account/agents", response_model=SearchAgentOut, status_code=201)
def create_agent(
    payload: SearchAgentIn,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name must not be empty")

    existing = session.scalars(select(SearchAgent).where(SearchAgent.user_id == user.id)).all()
    if len(existing) >= MAX_AGENTS_PER_USER:
        raise HTTPException(status_code=409, detail="agent limit reached")

    for agent in existing:
        if agent.query == payload.query:
            raise HTTPException(status_code=409, detail="agent for this search already exists")

    # last_run_at starts now: an agent reports what appears *after* it was
    # created, never the whole existing catalog as a first mail.
    agent = SearchAgent(
        user_id=user.id,
        name=name[:200],
        query=payload.query[:2000],
        last_run_at=datetime.now(timezone.utc),
    )
    session.add(agent)
    session.commit()
    return _to_agent(agent)


@router.delete("/account/agents/{agent_id}", status_code=204)
def delete_agent(
    agent_id: int,
    user: User = Depends(current_user),
    session: DbSession = Depends(get_session),
):
    agent = session.scalar(select(SearchAgent).where(SearchAgent.id == agent_id, SearchAgent.user_id == user.id))
    if agent is not None:
        session.delete(agent)
        session.commit()
    return Response(status_code=204)
