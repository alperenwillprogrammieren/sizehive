"""User accounts and everything hanging off them.

This is the first server-side identity in the project — until now all
user-specific state lived in the browser's localStorage (see CLAUDE.md).
Accounts exist because price alerts and search agents fundamentally can't
work without one: something has to run while the browser is closed and
know where to send the result.

Authentication is passwordless. A login link carries a single-use token; a
verified token mints a session. Neither token is stored in the clear —
only their SHA-256 hashes, so a database leak doesn't hand out sessions.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    #: Stored lowercased — the app treats addresses case-insensitively.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    price_alerts: Mapped[list["PriceAlert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    search_agents: Mapped[list["SearchAgent"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LoginToken(Base):
    """Single-use magic-link token. Consumed by setting `used_at`."""

    __tablename__ = "login_token"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Session(Base):
    __tablename__ = "user_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WatchlistItem(Base):
    """Server-side Merkliste. Mirrors the localStorage shape from Paket 1:
    an id plus the price at the moment of saving, nothing else."""

    __tablename__ = "watchlist_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variant.id", ondelete="CASCADE"), index=True)
    price_cents_at_save: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="watchlist_items")

    __table_args__ = (UniqueConstraint("user_id", "variant_id", name="uq_watchlist_user_variant"),)


class PriceAlert(Base):
    """Notify when a variant gets cheap enough.

    `target_price_cents` NULL means "tell me whenever it hits a new low we
    have never recorded before" — the alert version of Paket 2's all-time-low
    flag. `last_notified_price_cents` is what stops a flapping price from
    sending the same mail every run: a repeat only goes out below it.
    """

    __tablename__ = "price_alert"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variant.id", ondelete="CASCADE"), index=True)
    target_price_cents: Mapped[int | None] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_notified_price_cents: Mapped[int | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="price_alerts")

    __table_args__ = (UniqueConstraint("user_id", "variant_id", name="uq_alert_user_variant"),)


class SearchAgent(Base):
    """A saved filter querystring that reports newly imported matches.

    `query` is the same string the frontend already puts in the URL, so an
    agent is a saved search that got a job. "New" is decided by
    `variant.created_at > last_run_at`, using the column the "Neuheit" sort
    is already built on.
    """

    __tablename__ = "search_agent"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    query: Mapped[str] = mapped_column(String(2000))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="search_agents")
