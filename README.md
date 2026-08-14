# sizehive

Shopübergreifende Kleidungssuche mit facettierter Filterung nach vielen Attributen
(Passform, Bundhöhe, Beinform, Waschung, Material, ...) statt nur Größe und Preis.
MVP-Kategorie: Herrenjeans. Details siehe [`docs/SPEC.md`](docs/SPEC.md).

## Voraussetzungen

- Python 3.11+
- Node.js 20+
- Docker (für PostgreSQL)

## Setup

```bash
cp .env.example .env
```

### Datenbank

```bash
docker compose up -d db
```

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # Windows; unter Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Backend läuft auf http://localhost:8000, API-Doku unter http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend läuft auf http://localhost:5173 und proxied `/api/*` zum Backend
(siehe `frontend/vite.config.js`). Health-Check: http://localhost:5173/api/health.

## Projektstruktur

```
backend/    FastAPI + SQLAlchemy + Alembic
frontend/   React (Vite)
docs/       Spec und technische Entscheidungen
```
