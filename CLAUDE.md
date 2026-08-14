# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repo is currently a bare scaffold (`main.py` is the unmodified PyCharm template). The
full product spec lives at `docs/SPEC.md` — read it before doing any work here, it is the
source of truth for scope, data model, and milestones. Everything below is derived from that
spec and describes the target architecture as milestones M0–M7 are built out.

## What sizehive is

A webapp that makes clothing searchable across shops. Individual shops each have their own
filters that don't work across sites, and price comparators (Idealo etc.) compare price but not
clothing attributes. Sizehive's differentiator: faceted search across *many* garment attributes
simultaneously (fit, rise, leg shape, wash, material, stretch, closure, etc.), not just size and
price, across all connected shops in one query.

MVP scope is deliberately narrow: one category (men's jeans), three data sources, but the
attribute architecture must support adding a new category as pure configuration — never a schema
change.

## Working style for this project

The spec's own instructions (see `docs/SPEC.md`, section "Arbeitsweise") set the operating mode:

- Work through milestones M0–M7 in order, making technical decisions autonomously (choice of
  libraries, file/folder layout, etc.) without stopping to ask.
- Commit after each milestone with a message that lets that step be reverted independently.
- After each milestone, verify its own "Fertig, wenn" (done-when) criterion before moving on;
  fix it before proceeding if it doesn't hold.
- Record significant technical decisions and their rationale in `docs/DECISIONS.md` as they're
  made.
- Only stop and ask the user when genuinely blocked on something outside Claude's control
  (credentials, accounts, external approvals — e.g. affiliate network publisher access).

## Architecture (target, per spec)

**Repo layout:** `backend/` and `frontend/` as separate top-level folders.

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic.
- **Database:** PostgreSQL. Attributes are stored as JSONB with a GIN index rather than as fixed
  columns, so new attributes/categories don't require migrations. Fields that are almost always
  filtered on (size, price) stay as real columns for performance.
- **Frontend:** React via Vite (JavaScript, not TypeScript).
- **Infra:** Docker Compose for Postgres and services. Vite dev server proxies `/api` to the
  backend; CORS is configured for the Vite dev server.

### Data model

Four tables:

- `shop` — id, name, slug, affiliate_network
- `product` — id, brand, model_name, category, gender, `attributes` (JSONB), `attribute_sources` (JSONB)
- `variant` — id, product_id, shop_id, shop_sku, ean (nullable), size_raw, size_w, size_l, color, url
- `price_snapshot` — id, variant_id, price_cents, list_price_cents, in_stock, captured_at

Key invariant: **`price_snapshot` rows are append-only, never overwritten.** Price history is a
free side effect of repeated imports, not a separately maintained feature.

### Attribute provenance

Every attribute value carries an origin (`feed`, `rule`, or `llm`) and a confidence score, stored
in `attribute_sources` alongside `attributes`. Derived (non-feed) attributes must be visually
distinguishable from feed-sourced ones in the frontend.

**Required attributes** (from feed, structured): `brand`, `price`, `list_price`, `size_w`,
`size_l`, `color`, `availability`, `gender`, `shop`.

**Derived attributes** (mostly extracted from free-text title/description): `fit` (skinny, slim,
straight, regular, relaxed, loose, baggy, wide leg), `rise` (low, mid, high), `leg_shape`
(tapered, straight, bootcut, flared), `wash` (raw, light, mid, dark, black, stonewashed, used,
destroyed), `material` (cotton/elastane share), `stretch` (yes/no), `closure`, `pockets`,
`sustainability`.

The rule-based extractor (regex/keyword mapping) must be built as a swappable component — the
plan is to later place an LLM-based extractor alongside it, not to replace it.

### Data sourcing

Primary path is affiliate product feeds (Awin, Belboon, Tradedoubler) as CSV/XML — not scraping.
Until publisher access is granted, work uses realistic-but-messy local sample feeds under
`backend/data/samples/` (mixed size notations, missing EANs, attributes only in free-text
descriptions, inconsistent brand spellings). Import must be idempotent: re-running an import must
not duplicate `variant` rows, but must append a new `price_snapshot` per run.

## Explicitly out of scope for MVP

Cross-shop reviews, women's fashion/shoes/other categories, user accounts/wishlists/notifications,
size conversion between systems (W32 ↔ 48 ↔ M).

## Milestones

Full detail and "done-when" criteria for each are in `docs/SPEC.md`. Summary:

| # | Milestone | Done-when |
|---|---|---|
| M0 | Base setup: git, backend FastAPI skeleton + venv, frontend Vite+React, docker-compose (Postgres), Alembic init, `.gitignore`, `.env.example`, `README.md`, CORS + `/api` proxy | Backend & frontend start, `/api/health` responds through the Vite proxy, DB runs in container |
| M1 | SQLAlchemy models for the 4 tables incl. JSONB + GIN index, Alembic migration | `alembic upgrade head` succeeds, tables exist |
| M2 | 3 sample feeds (200+ items each), idempotent import script | Two import runs: variant count unchanged, snapshot count doubles |
| M3 | Size/brand/color normalization parsers (`W32/L34`, `32/34`, `W 32 L 34`, `32x34`, etc.) | Unit tests green for ≥10 real-world spellings per field |
| M4 | Rule-based attribute extraction from title/description, swappable extractor interface | ≥70% of test articles get a `fit` and a `wash`, coverage report per attribute |
| M5 | `GET /api/search` (arbitrary attribute combo, price range, size, sort, pagination) + `GET /api/facets` (available values + counts for current filter state) | Endpoints testable in `/docs`, ≥5 combined filters return plausible results |
| M6 | Frontend: facet sidebar + result list, removable filter chips, filter state in URL | Combine/remove multiple filters in-browser, URL is shareable |
| M7 | Percentile price score, price-history chart, discount-honesty check (was list price ever real), internal attribute-coverage dashboard | Detail view shows chart + score, dashboard reachable |

## Commands

Not yet applicable — no backend/frontend scaffold exists until M0 is complete. Once M0 lands,
this section should be updated with the actual dev/test/migrate commands (expected to be
FastAPI/uvicorn + pytest on the backend, Vite dev/build on the frontend, `alembic` for
migrations, `docker compose up` for Postgres) — check `backend/README.md` or the root
`README.md` created in M0 for the current exact commands rather than assuming.