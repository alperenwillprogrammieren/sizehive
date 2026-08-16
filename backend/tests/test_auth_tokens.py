from datetime import datetime, timedelta, timezone

import pytest

from app.auth.tokens import (
    expires_in,
    generate_token,
    hash_token,
    is_expired,
    is_valid_email,
    normalize_email,
    verify_token,
)

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def test_tokens_are_unique_and_not_trivially_short():
    tokens = {generate_token() for _ in range(200)}
    assert len(tokens) == 200
    assert all(len(t) >= 32 for t in tokens)


def test_hash_is_stable_and_does_not_contain_the_token():
    token = generate_token()
    assert hash_token(token) == hash_token(token)
    assert token not in hash_token(token)
    assert len(hash_token(token)) == 64


def test_verify_token_accepts_only_the_matching_token():
    token = generate_token()
    other = generate_token()
    assert verify_token(token, hash_token(token)) is True
    assert verify_token(other, hash_token(token)) is False


def test_expiry_boundaries():
    expires = expires_in(minutes=20, now=NOW)
    assert expires == NOW + timedelta(minutes=20)
    assert is_expired(expires, now=NOW) is False
    assert is_expired(expires, now=NOW + timedelta(minutes=19)) is False
    # Exactly at the deadline counts as expired.
    assert is_expired(expires, now=NOW + timedelta(minutes=20)) is True
    assert is_expired(expires, now=NOW + timedelta(minutes=21)) is True


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  Alper@Example.COM ", "alper@example.com"),
        ("test@test.de", "test@test.de"),
    ],
)
def test_email_normalization(raw, expected):
    assert normalize_email(raw) == expected


@pytest.mark.parametrize(
    "email",
    ["a@b.de", "vorname.nachname@shop.example.com", "x+tag@mail.co.uk"],
)
def test_valid_emails(email):
    assert is_valid_email(email) is True


@pytest.mark.parametrize(
    "email",
    ["", "notanemail", "no@domain", "@example.com", "two@@example.com", "spaces @example.com", "a@b.", "x" * 400 + "@e.de"],
)
def test_invalid_emails(email):
    assert is_valid_email(email) is False
