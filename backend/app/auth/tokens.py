"""Token generation and hashing for passwordless login.

Kept separate from the DB layer so the rules — how tokens are produced,
how they're hashed, when they count as expired — are unit-testable without
a database.

Only hashes are ever persisted. SHA-256 without a salt is the right call
here (and *not* the right call for passwords): these tokens are 32 bytes of
`secrets` output, so there is no dictionary to attack and no need for a
slow KDF, while an unsalted hash keeps the lookup a plain indexed equality.
"""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

TOKEN_BYTES = 32


def generate_token() -> str:
    """A fresh, URL-safe secret. Returned once, never stored as-is."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    return secrets.compare_digest(hash_token(token), token_hash)


def expires_in(minutes: int = 0, days: int = 0, now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)) + timedelta(minutes=minutes, days=days)


def is_expired(expires_at: datetime, now: datetime | None = None) -> bool:
    return expires_at <= (now or datetime.now(timezone.utc))


#: Deliberately permissive: enough to reject obvious typos and junk without
#: pulling in an RFC-5322 validator dependency. The login link is the real
#: proof that an address exists.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


def is_valid_email(email: str) -> bool:
    candidate = email.strip()
    return len(candidate) <= 320 and bool(_EMAIL_PATTERN.match(candidate))


def normalize_email(email: str) -> str:
    """Addresses are compared case-insensitively; the local part technically
    may be case-sensitive, but no real mail provider treats it that way and
    matching on the raw string would silently create duplicate accounts."""
    return email.strip().lower()
