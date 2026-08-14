# Spec: Sizehive

## Kontext für Claude Code

Ich baue eine Webapp, die Kleidung shopübergreifend durchsuchbar macht.

**Das Problem:** Wer online Kleidung sucht, muss 20 Shops einzeln durchklicken. Jeder Shop hat
eigene Filter, die nur innerhalb dieses Shops funktionieren. Preisvergleicher wie Idealo können
zwar Preise vergleichen, aber nicht nach Kleidungseigenschaften filtern.

**Das Alleinstellungsmerkmal:** Filtern nach möglichst vielen Eigenschaften gleichzeitig, über
alle Shops hinweg. Nicht nur Größe und Preis, sondern Passform, Bundhöhe, Beinform, Waschung,
Material, Verschlussart, Stretchanteil und so weiter. Das Ziel ist eine Suche wie
"Baggy, High Waist, 100 Prozent Baumwolle, dunkelblau, W32/L34, unter 60 Euro, lieferbar"
über alle angebundenen Shops in einer Abfrage.

**Arbeitsweise:** Arbeite die Meilensteine eigenständig und ohne Rückfragen durch.
Triff technische Entscheidungen selbst, installiere benötigte Dependencies selbst,
erstelle Dateien und Ordner selbst. Konkret:

- Arbeite M0 bis M7 der Reihe nach ab, ohne zwischendurch auf Bestätigung zu warten.
- Nach jedem Meilenstein ein eigener Commit mit aussagekräftiger Message,
  damit einzelne Schritte rückgängig gemacht werden können.
- Prüfe nach jedem Meilenstein selbst, ob das "Fertig, wenn"-Kriterium erfüllt ist.
  Wenn nicht, korrigiere, bevor du weitergehst.
- Halte am Ende in `docs/DECISIONS.md` in Stichpunkten fest, welche wesentlichen
  technischen Entscheidungen du getroffen hast und warum.
- Stoppe nur, wenn etwas ohne meine Mitwirkung nicht lösbar ist
  (z. B. Zugangsdaten, Accounts, externe Freischaltungen).

## Stack

Das Projekt wird komplett neu aufgesetzt, es gibt keinen bestehenden Code.

- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Datenbank: PostgreSQL (Attribute als JSONB mit GIN-Index)
- Frontend: React (Vite, JavaScript)
- Infrastruktur: Docker Compose für Datenbank und Services
- Versionskontrolle: Git

Struktur: `backend/` und `frontend/` als getrennte Ordner im Projekt-Root.

## MVP-Scope (bewusst eng, aber attributreich)

- **Eine** Kategorie: Herrenjeans. Die Attribut-Architektur muss aber so gebaut sein,
  dass eine neue Kategorie nur eine Konfiguration ist und keine Schemaänderung.
- **Drei** Datenquellen
- Facettierte Suche über alle unten genannten Attribute
- Sortierung: Preis, Rabatthöhe, Neuheit
- Detailansicht mit Preisverlauf
- Deeplink zum Shop

## Attribut-Taxonomie Jeans

Pflicht (kommt meist strukturiert aus dem Feed):
`brand`, `price`, `list_price`, `size_w`, `size_l`, `color`, `availability`, `gender`, `shop`

Kür (muss überwiegend aus Titel und Beschreibung abgeleitet werden):
`fit` (skinny, slim, straight, regular, relaxed, loose, baggy, wide leg),
`rise` (low, mid, high), `leg_shape` (tapered, straight, bootcut, flared),
`wash` (raw, light, mid, dark, black, stonewashed, used, destroyed),
`material` (Baumwollanteil, Elasthananteil), `stretch` (ja/nein),
`closure` (Knopfleiste, Reißverschluss), `pockets`, `sustainability` (Bio-Baumwolle, GOTS)

Wichtig: Jedes Attribut bekommt eine Herkunft (`feed`, `rule`, `llm`) und einen
Confidence-Wert. Abgeleitete Attribute dürfen im Frontend als solche erkennbar sein.

## Ausdrücklich nicht im MVP

- Bewertungen shopübergreifend (kommen in Produktfeeds meist nicht vor)
- Damenmode, Schuhe, andere Kategorien
- Nutzerkonten, Merklisten, Benachrichtigungen
- Größenumrechnung zwischen Systemen (W32 <-> 48 <-> M)

## Datenbeschaffung

Primärweg sind Affiliate-Produktfeeds (Awin, Belboon, Tradedoubler), nicht Scraping.
Feeds kommen als CSV oder XML und enthalten typischerweise: EAN, Marke, Produktname,
Beschreibung, Kategorie, Größe, Farbe, Material, aktueller Preis, Streichpreis,
Verfügbarkeit, Bild-URL, Deeplink.

Bis ich als Publisher freigeschaltet bin, arbeite ich mit lokalen Beispiel-Feeds im Ordner
`backend/data/samples/`. Diese müssen realistisch unsauber sein: gemischte Größenschreibweisen,
fehlende EANs, Attribute nur im Fließtext der Beschreibung, uneinheitliche Markenschreibweisen.

## Datenmodell (Vorschlag, gerne hinterfragen)

- `shop` — id, name, slug, affiliate_network
- `product` — id, brand, model_name, category, gender, `attributes` (JSONB), `attribute_sources` (JSONB)
- `variant` — id, product_id, shop_id, shop_sku, ean (nullable), size_raw, size_w, size_l, color, url
- `price_snapshot` — id, variant_id, price_cents, list_price_cents, in_stock, captured_at

Begründung JSONB statt fester Spalten: neue Attribute und neue Kategorien sollen ohne Migration
möglich sein. GIN-Index auf `attributes` für schnelle Filterung. Attribute, nach denen praktisch
immer gefiltert wird (Größe, Preis), bleiben bewusst als echte Spalten.

Prinzip: `price_snapshot` wird **nie** überschrieben, nur angehängt. Der Preisverlauf entsteht
dadurch automatisch als Nebenprodukt des Imports.

## Meilensteine

### M0 — Grundsetup
Projektstruktur anlegen: Git-Repo, `backend/` mit venv und FastAPI-Grundgerüst, `frontend/` mit
Vite und React, `docker-compose.yml` mit PostgreSQL, Alembic initialisieren, `.gitignore`,
`.env.example`, kurze `README.md` mit Startanleitung. CORS für den Vite-Dev-Server konfigurieren
und den Vite-Proxy `/api` auf das Backend zeigen lassen.
**Fertig, wenn:** Backend und Frontend starten, `/api/health` antwortet über den Vite-Proxy,
die Datenbank läuft im Container.

### M1 — Datenmodell und Migration
SQLAlchemy-Modelle für die vier Tabellen anlegen inklusive JSONB-Feldern und GIN-Index,
Alembic-Migration erzeugen und ausführen.
**Fertig, wenn:** `alembic upgrade head` läuft durch und die Tabellen existieren in Postgres.

### M2 — Beispiel-Feeds und Import
Drei realistisch unsaubere Beispiel-Feeds mit je mindestens 200 Artikeln generieren.
Import-Skript, das sie einliest und in die DB schreibt. Idempotent: zweimal laufen lassen
darf keine Duplikate erzeugen, aber einen zweiten Snapshot.
**Fertig, wenn:** nach zwei Läufen die Variant-Anzahl gleich bleibt und die Snapshot-Anzahl sich verdoppelt.

### M3 — Normalisierung
Parser für Größen (`W32/L34`, `32/34`, `W 32 L 34`, `32x34`) sowie für Marken- und
Farbschreibweisen. Nicht parsebare Werte werden protokolliert, nicht stillschweigend verworfen.
**Fertig, wenn:** Unit-Tests für mindestens 10 reale Schreibweisen je Feld grün sind.

### M4 — Attribut-Extraktion
Regelbasierte Extraktion der Kür-Attribute aus Produkttitel und Beschreibung
(Keyword- und Regex-Mapping, z. B. "weites Bein", "wide leg", "Loose Fit" -> `fit: loose`).
Ergebnis landet in `attributes`, Herkunft und Confidence in `attribute_sources`.
Die Extraktion muss als austauschbare Komponente gebaut sein, damit später ein
LLM-basierter Extraktor danebengestellt werden kann.
**Fertig, wenn:** mindestens 70 Prozent der Testartikel ein `fit` und ein `wash` haben
und ein Report die Abdeckung pro Attribut ausgibt.

### M5 — Facettierte Such-API
`GET /api/search` mit beliebiger Attributkombination als Query-Parameter, Preisspanne,
Größe, Sortierung und Pagination. Zusätzlich `GET /api/facets`, das für die aktuelle
Filterkombination die verfügbaren Werte samt Trefferanzahl zurückgibt, damit das Frontend
keine leeren Filteroptionen anzeigt.
**Fertig, wenn:** die Endpunkte in `/docs` testbar sind und eine Kombination aus mindestens
fünf Filtern plausible Ergebnisse liefert.

### M6 — Frontend
Suchseite mit Facettenleiste links, Ergebnisliste rechts (Bild, Marke, Name, Preis, Shop, Link).
Filter zeigen Trefferanzahlen, aktive Filter sind als Chips entfernbar, Filterzustand steht
in der URL, damit Suchen teilbar sind.
**Fertig, wenn:** ich im Browser mehrere Filter kombinieren, entfernen und die URL teilen kann.

### M7 — Statistiken
- Perzentil-Score pro Artikel ("günstiger als X Prozent der vergleichbaren Jeans")
- Preisverlauf-Chart in der Detailansicht
- Rabatt-Check: war der Streichpreis jemals der tatsächliche Verkaufspreis
- Attribut-Abdeckung als internes Dashboard, damit ich sehe, wo die Extraktion schwächelt
**Fertig, wenn:** die Detailansicht Chart und Score anzeigt und das Dashboard erreichbar ist.

## Auftrag

Arbeite M0 bis M7 vollständig und eigenständig ab. Melde dich erst wieder, wenn alle
Meilensteine erfüllt sind oder wenn du an einem Punkt wirklich nicht ohne mich weiterkommst.
Gib mir am Ende eine kurze Zusammenfassung: was läuft, was fehlt, wie ich es starte.
