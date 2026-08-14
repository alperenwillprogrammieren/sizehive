# Technische Entscheidungen

Stichpunkte zu wesentlichen Entscheidungen aus M0–M7, mit Begründung. Chronologisch nach Meilenstein.

## M0 — Grundsetup

- **Postgres-Port 55432 statt 5432.** Auf der Entwicklungsmaschine lief bereits ein lokal
  installierter PostgreSQL-Dienst auf Port 5432, der mit Dockers Port-Forwarding kollidierte
  (Passwort-Auth schlug fehl, weil Verbindungen teils beim falschen Postgres landeten). Statt den
  bestehenden lokalen Dienst anzufassen, mappt `docker-compose.yml` den Container auf Host-Port
  `55432`. `.env.example` und `app/core/config.py` sind entsprechend gesetzt.
- Alembic `env.py` liest die DB-URL aus `app.core.config.settings` statt aus einer fest in
  `alembic.ini` hinterlegten URL, damit eine einzige Quelle der Wahrheit für die Verbindung existiert.

## M1 — Datenmodell

- Ganzzahlige Autoincrement-Primärschlüssel für alle vier Tabellen (kein UUID) — für den MVP
  ausreichend, kein bekannter Bedarf an client-generierten IDs oder Multi-Master-Replikation.
- `UniqueConstraint(shop_id, shop_sku)` auf `variant` ist der Anker für idempotenten Import (M2).
- `attributes`/`attribute_sources` als JSONB mit GIN-Index auf `attributes`, wie im Spec
  vorgeschlagen — neue Attribute/Kategorien bleiben Konfiguration statt Migration.

## M2 — Beispiel-Feeds und Import

- Drei Feeds mit bewusst unterschiedlichem Schema/Format simuliert (Awin: CSV; Belboon: CSV mit
  deutschen Spaltennamen, Semikolon-Trenner, Dezimalkomma; Tradedoubler: XML) — reale
  Affiliate-Feed-Heterogenität, nicht nur unterschiedliche Werte in gleicher Struktur.
- Produkt-Matching läuft über normalisiertes `(brand, model_name, category, gender)`, nicht über
  EAN — die Beispiel-Feeds haben absichtlich ~20% fehlende EANs, wie im Spec gefordert.
  Cross-Shop-Merge unter verschiedenen Markenschreibweisen funktioniert erst zuverlässig, seit M3s
  Brand-Normalizer vor dem Matching läuft (siehe M3).
- `price_snapshot` wird bei jedem Import-Lauf immer neu angehängt, nie aktualisiert — Preisverlauf
  entsteht als Nebenprodukt, wie im Spec vorgesehen.

## M3 — Normalisierung

- Marken-/Farb-Normalisierung über eine statische Alias-Tabelle (Schreibweise → kanonischer Wert),
  keine Fuzzy-Matching-Bibliothek. Vorhersagbar und leicht testbar, kostet aber manuelle Pflege bei
  neuen Schreibweisen, die noch nicht in der Tabelle stehen — für den MVP-Umfang (12 Marken, 7
  Farben) vertretbar.
- `scripts/generate_sample_feeds.py` importiert seine Markenliste jetzt aus
  `app.normalize.brand.CANONICAL_BRANDS`, statt sie zu duplizieren — verhindert, dass Testdaten und
  der Parser, der sie bereinigen soll, auseinanderlaufen.
- Größen-Parser erkennt nur die im Spec genannten Notationen (`W32/L34`, `32/34`, `W 32 L 34`,
  `32x34` plus Interpunktions-/Groß-Kleinschreibungs-Varianten). Bloße EU-Größen oder Buchstaben-
  größen gelten absichtlich als nicht parsebar (geloggt, nicht verworfen) — Größensystem-Umrechnung
  ist laut Spec explizit außerhalb des MVP.
- Brand-/Farb-Normalisierung retroaktiv in den Importer eingebaut: verbessert M2s
  Cross-Shop-Produkt-Matching rückwirkend (Produktanzahl sank von 82 auf 42 nach einem Reset+Reimport).

## M4 — Attribut-Extraktion

- **Schemaänderung:** `product.description` (Text) hinzugefügt. Das im Spec vorgeschlagene
  Datenmodell hatte keine Spalte für Titel/Beschreibung, aber M4 braucht den Freitext der Feeds zum
  Extrahieren. Ergänzt gemäß der ausdrücklichen Einladung im Spec, das Modell zu hinterfragen.
- Extraktor als schmales `Protocol` (`app/extract/base.py`) definiert, `RuleBasedExtractor` ist die
  einzige Implementierung — ein späterer LLM-Extraktor kann danebengestellt werden, ohne dass
  aufrufender Code sich ändert (Spec-Anforderung "austauschbare Komponente").
- Konfidenzwerte sind statische Heuristiken (0.9 für mehrwortige Phrasen-Treffer, niedriger für
  einzelne generische Wörter), keine kalibrierten/gelernten Werte.

## M5 — Facettierte Such-API

- **Schemaänderung:** `variant.image_url` und `variant.created_at` hinzugefügt — Bild pro Angebot
  fehlte im Spec-Modell, wird aber für Ergebnisliste (M6) und Detailansicht (M7) gebraucht;
  `created_at` ist die Grundlage für die "Neuheit"-Sortierung.
- "Aktueller Preis" pro Variante = `price_snapshot` mit `max(captured_at)`, per Join-Subquery
  ermittelt (nicht per Window-Function) — einfacher, mit vernachlässigbarem Risiko bei exakt
  gleichzeitigen Timestamps.
- `/api/facets` folgt dem "Exclude-Self"-Prinzip: die Zählung für ein Facetten-Attribut ignoriert
  dessen eigenen aktiven Filter, berücksichtigt aber alle anderen — damit das Frontend nie eine
  Option zeigt, die zu einer Sackgasse führen würde (Spec-Anforderung).
- `sustainability` (JSONB-Array) ist als Suchfilter nutzbar (JSONB-Containment), aber nicht Teil
  der Facetten-Zählung — bräuchte `jsonb_array_elements`, für den MVP-Umfang nicht nötig.

## M6 — Frontend

- Filterzustand lebt in der URL-Query (`history.replaceState`, kein Redux/Zustand-Store) — direkte
  Umsetzung der Spec-Anforderung "Filterzustand steht in der URL, damit Suchen teilbar sind".
- Kein API-Client-Framework (kein React Query o. Ä.) — bei zwei Endpunkten und einem einzigen
  `useEffect` pro Seite unnötiger Overhead für den MVP-Umfang.

## M7 — Statistiken

- `scripts/simulate_price_history.py` erzeugt pro Variante 5–7 zusätzliche historische
  `price_snapshot`-Einträge (verteilt über ~35 Tage). Ohne das hätte jede Variante nur einen
  einzigen Preispunkt aus dem letzten Import — zu wenig, um Chart und Rabatt-Check sinnvoll zu
  zeigen. Nur für Dev-Daten gedacht, idempotent (überspringt bereits angereicherte Varianten).
- "Vergleichbare Jeans" für den Perzentil-Score = alle Varianten derselben Kategorie (im MVP gibt
  es nur eine: Herrenjeans). Naheliegendste Definition ohne die Kategorie-Grenze zu verlassen;
  könnte später auf ähnliche Attribute (z. B. gleicher Fit) verfeinert werden.
- Rabatt-Check prüft die aufgezeichnete `price_snapshot`-Historie der Variante: War der
  Streichpreis jemals der tatsächlich verlangte Preis? Basiert nur auf tatsächlich aufgezeichneten
  Daten, keine Annahme über die Zeit davor.
- `react-router-dom` als erste Routing-Abhängigkeit im Frontend eingeführt — ab M7 gibt es mit
  Suche/Detail/Dashboard drei echte, eigenständige Ansichten, die eine URL-basierte Navigation
  brauchen.
- Preisverlauf-Chart als eigenes, simples Inline-SVG-Component gebaut statt einer
  Chart-Bibliothek (z. B. Recharts) — hält die Frontend-Abhängigkeiten für ein einzelnes
  Liniendiagramm minimal.

## Übergreifend

- Nach jeder Schema- oder Normalisierungsänderung wurde die Dev-Datenbank per
  `alembic downgrade base && alembic upgrade head` zurückgesetzt und neu importiert, statt
  In-Place-Migrationsskripte für Bestandsdaten zu schreiben. Vertretbar, weil es sich ausschließlich
  um lokal generierte Beispieldaten handelt — sobald echte Feeds angebunden sind, braucht jede
  weitere Schemaänderung eine echte Migration mit Backfill statt eines Resets.
