"""Login-link issuing, token verification and session lookup."""
from datetime import datetime, timezone
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.auth.tokens import expires_in, generate_token, hash_token, is_expired, normalize_email
from app.core.config import settings
from app.models import LoginToken, Session, User
from app.notify.mailer import send_mail

SESSION_COOKIE = "sizehive_session"


def get_or_create_user(session: DbSession, email: str) -> User:
    normalized = normalize_email(email)
    user = session.scalar(select(User).where(User.email == normalized))
    if user is None:
        user = User(email=normalized)
        session.add(user)
        session.flush()
    return user


#: Minimum gap between two login mails for the same address. Without it,
#: anyone could use the endpoint to mail-bomb a third party.
RESEND_COOLDOWN_SECONDS = 60


def issue_login_link(session: DbSession, email: str) -> str | None:
    """Creates a single-use token, mails the link, returns the link.

    Returns None when a link was already sent moments ago. The return value
    exists for tests and for the dev log — the endpoint never hands it back
    to the caller, or anyone could log in as anyone.
    """
    user = get_or_create_user(session, email)

    now = datetime.now(timezone.utc)
    recent = session.scalar(
        select(LoginToken)
        .where(LoginToken.user_id == user.id, LoginToken.used_at.is_(None))
        .order_by(LoginToken.created_at.desc())
        .limit(1)
    )
    if recent is not None and (now - recent.created_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        session.commit()  # persist the user row created above, if any
        return None

    token = generate_token()
    session.add(
        LoginToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=expires_in(minutes=settings.login_token_ttl_minutes),
        )
    )
    session.commit()

    link = f"{settings.frontend_base_url}/login?token={quote(token)}"
    send_mail(
        to=user.email,
        subject="Dein Login-Link für sizehive",
        body=(
            f"Hallo,\n\nmit diesem Link meldest du dich bei sizehive an:\n\n{link}\n\n"
            f"Der Link gilt {settings.login_token_ttl_minutes} Minuten und kann nur einmal "
            "verwendet werden.\n\nWenn du das nicht angefordert hast, ignoriere diese Mail.\n"
        ),
    )
    return link


def consume_login_token(session: DbSession, token: str) -> User | None:
    """Validates and burns a login token. Returns None for anything unusable."""
    record = session.scalar(select(LoginToken).where(LoginToken.token_hash == hash_token(token)))
    if record is None or record.used_at is not None or is_expired(record.expires_at):
        return None

    record.used_at = datetime.now(timezone.utc)
    user = session.get(User, record.user_id)
    if user is None:
        return None
    user.last_login_at = datetime.now(timezone.utc)
    session.commit()
    return user


def create_session(session: DbSession, user: User) -> str:
    """Returns the raw session token — the only time it exists in the clear."""
    token = generate_token()
    session.add(
        Session(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=expires_in(days=settings.session_ttl_days),
        )
    )
    session.commit()
    return token


def user_for_session_token(session: DbSession, token: str | None) -> User | None:
    if not token:
        return None
    record = session.scalar(select(Session).where(Session.token_hash == hash_token(token)))
    if record is None or is_expired(record.expires_at):
        return None
    return session.get(User, record.user_id)


def destroy_session(session: DbSession, token: str | None) -> None:
    if not token:
        return
    record = session.scalar(select(Session).where(Session.token_hash == hash_token(token)))
    if record is not None:
        session.delete(record)
        session.commit()


def purge_expired(session: DbSession) -> int:
    """Housekeeping for the notification run: drop dead tokens and sessions."""
    now = datetime.now(timezone.utc)
    removed = 0
    for model in (LoginToken, Session):
        for record in session.scalars(select(model).where(model.expires_at <= now)):
            session.delete(record)
            removed += 1
    session.commit()
    return removed
