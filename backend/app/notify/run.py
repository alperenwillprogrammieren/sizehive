"""Notification run: evaluate price alerts and search agents, send mail.

Meant to be run periodically (cron / systemd timer), after the import:

    python -m app.importers.run && python -m app.notify.run

It is safe to run repeatedly. Price alerts dedupe on the last notified
price (see notify/rules.py); search agents advance `last_run_at` on every
run, so an article is reported at most once per agent.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session as DbSession

from app.api.search import (
    _add_common_joins,
    _apply_filters,
    _latest_price_subquery,
    filters_from_query_string,
)
from app.auth.service import purge_expired
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import PriceAlert, PriceSnapshot, Product, SearchAgent, Shop, User, Variant
from app.notify.mailer import send_mail
from app.notify.rules import AlertState, should_notify

logger = logging.getLogger(__name__)

#: How many example hits a search-agent mail lists before summarising.
AGENT_MAIL_EXAMPLES = 5


def _euro(cents: int) -> str:
    return f"{cents / 100:.2f} €".replace(".", ",")


def _product_url(variant_id: int) -> str:
    return f"{settings.frontend_base_url}/product/{variant_id}"


def run_price_alerts(session: DbSession) -> int:
    """Returns the number of notifications sent."""
    latest = _latest_price_subquery()
    lows = (
        select(
            PriceSnapshot.variant_id.label("variant_id"),
            func.min(PriceSnapshot.price_cents).label("low_cents"),
        )
        .group_by(PriceSnapshot.variant_id)
        .subquery()
    )

    rows = session.execute(
        select(PriceAlert, User, Variant, Product, Shop, PriceSnapshot, lows.c.low_cents)
        .select_from(PriceAlert)
        .join(User, PriceAlert.user_id == User.id)
        .join(Variant, PriceAlert.variant_id == Variant.id)
        .join(Product, Variant.product_id == Product.id)
        .join(Shop, Variant.shop_id == Shop.id)
        .join(latest, latest.c.variant_id == Variant.id)
        .join(
            PriceSnapshot,
            and_(
                PriceSnapshot.variant_id == latest.c.variant_id,
                PriceSnapshot.captured_at == latest.c.captured_at,
            ),
        )
        .join(lows, lows.c.variant_id == Variant.id)
        .where(PriceAlert.active.is_(True))
    ).all()

    sent = 0
    for alert, user, variant, product, shop, current, low_cents in rows:
        state = AlertState(
            current_cents=current.price_cents,
            all_time_low_cents=low_cents,
            target_cents=alert.target_price_cents,
            last_notified_price_cents=alert.last_notified_price_cents,
            in_stock=current.in_stock,
        )
        if not should_notify(state):
            continue

        reason = (
            f"Dein Zielpreis von {_euro(alert.target_price_cents)} ist erreicht."
            if alert.target_price_cents is not None
            else "Das ist der günstigste Preis, seit wir diesen Artikel beobachten."
        )
        send_mail(
            to=user.email,
            subject=f"Preisalarm: {product.brand} {product.model_name} für {_euro(current.price_cents)}",
            body=(
                f"{product.brand} {product.model_name}\n"
                f"{variant.size_raw} · {variant.color} · {shop.name}\n\n"
                f"Aktueller Preis: {_euro(current.price_cents)}\n"
                f"{reason}\n\n"
                f"{_product_url(variant.id)}\n\n"
                "Diesen Alarm kannst du auf der Artikelseite wieder entfernen.\n"
            ),
        )
        alert.last_notified_at = datetime.now(timezone.utc)
        alert.last_notified_price_cents = current.price_cents
        sent += 1

    session.commit()
    return sent


def _new_matches_for_agent(session: DbSession, agent: SearchAgent, since: datetime):
    """Variants matching the agent's stored filters that appeared after `since`.

    "New" uses variant.created_at — the same column the "Neuheit" sort is
    built on — so a re-import of an existing offer never counts as new.
    """
    filters = filters_from_query_string(agent.query)
    stmt = _apply_filters(
        _add_common_joins(select(Variant, Product, Shop, PriceSnapshot)), filters
    ).where(Variant.created_at > since)
    return session.execute(stmt.order_by(Variant.created_at.desc())).all()


def run_search_agents(session: DbSession) -> int:
    agents = session.scalars(select(SearchAgent).where(SearchAgent.active.is_(True))).all()

    sent = 0
    now = datetime.now(timezone.utc)
    for agent in agents:
        since = agent.last_run_at or agent.created_at
        try:
            matches = _new_matches_for_agent(session, agent, since)
        except Exception:
            # One broken stored query must not abort the whole run.
            logger.exception("search agent %s has an unusable query: %r", agent.id, agent.query)
            continue

        agent.last_run_at = now
        if not matches:
            continue

        user = session.get(User, agent.user_id)
        if user is None:
            continue

        lines = []
        for variant, product, shop, price in matches[:AGENT_MAIL_EXAMPLES]:
            lines.append(
                f"- {product.brand} {product.model_name} · {variant.size_raw} · {shop.name} "
                f"· {_euro(price.price_cents)}\n  {_product_url(variant.id)}"
            )
        more = len(matches) - len(lines)
        if more > 0:
            lines.append(f"… und {more} weitere.")

        send_mail(
            to=user.email,
            subject=f"Suchagent „{agent.name}\": {len(matches)} neue Treffer",
            body=(
                f"Für deinen Suchagenten „{agent.name}\" sind {len(matches)} neue Angebote "
                f"dazugekommen:\n\n" + "\n".join(lines) + "\n\n"
                f"Alle Treffer ansehen: {settings.frontend_base_url}/?{agent.query}\n"
            ),
        )
        agent.last_notified_at = now
        sent += 1

    session.commit()
    return sent


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    session = SessionLocal()
    try:
        alerts_sent = run_price_alerts(session)
        agents_sent = run_search_agents(session)
        purged = purge_expired(session)
    finally:
        session.close()

    print(f"price alerts: {alerts_sent} mail(s)")
    print(f"search agents: {agents_sent} mail(s)")
    print(f"expired tokens/sessions removed: {purged}")


if __name__ == "__main__":
    run()
