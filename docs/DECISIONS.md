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

## Post-MVP-Erweiterung: Volltextsuche + weitere Kategorien

Auf Wunsch nach M7 ergänzt: Volltextsuche (`q`-Parameter) und der Nachweis, dass "neue Kategorie
ist Konfiguration, keine Schemaänderung" (Spec, MVP-Scope) tatsächlich trägt — zwei weitere
Kategorien (T-Shirts, Sneaker) mit eigener Attribut-Taxonomie, ohne Migration.

- **Kein Schemawechsel nötig.** `product.category` war schon immer eine freie String-Spalte,
  `attributes`/`attribute_sources` schon immer JSONB — genau wie im Spec vorgesehen. Die
  Erweiterung ist ausschließlich neuer Code (Taxonomie-Registry, zwei neue Extraktoren,
  generalisierte Filter-/Facetten-Logik), keine einzige Alembic-Migration.
- **Attribut-Filter generisch statt benannt.** Vorher hatte `/api/search` feste, einzeln
  deklarierte Query-Parameter für jedes Jeans-Attribut (`fit`, `rise`, `wash`, ...). Das hätte für
  jede neue Kategorie weitere Parameter gebraucht und wäre der eigentlichen Spec-Anforderung
  "beliebige Attributkombination" nicht gerecht geworden. Jetzt gilt: jeder Query-Parameter, der
  nicht in einer kleinen reservierten Liste steht, wird generisch als
  `Product.attributes[<name>].astext == value` ausgewertet. `material` (verschachteltes Objekt)
  und `sustainability` (Tag-Liste) bleiben bewusst als dedizierte Parameter, weil ihr
  Vergleich (Zahlenbereich bzw. Containment) sich nicht als flache Gleichheit ausdrücken lässt.
- **Facetten dynamisch statt statisch.** `/api/facets` ermittelt die verfügbaren Attribut-Facetten
  per `SELECT DISTINCT jsonb_object_keys(attributes)` statt über eine feste Liste — eine neue
  Kategorie mit neuen Attributnamen taucht automatisch in den Facetten auf, ohne Codeänderung an
  dieser Stelle.
- **Frontend spiegelt dasselbe Prinzip.** `filters.js` behandelt jeden nicht reservierten
  URL-Parameter generisch als Attribut-Filter (`filters.attrs`); `FacetSidebar` rendert, was die
  API an Facetten liefert, mit einem Label-Wörterbuch, das für unbekannte Attributnamen auf den
  Rohschlüssel zurückfällt statt zu crashen. Für 2–3 Kategorien ist ein von Hand gepflegtes
  Label-Wörterbuch die richtige Grenze — vollautomatische, sprachlich saubere Labels für beliebige
  zukünftige Attributnamen wären Over-Engineering für diesen Umfang.
- **"Größe" bleibt jeans-spezifisch.** `size_w`/`size_l` sind nach wie vor W/L-Spalten für Jeans;
  T-Shirt-Größen (S–XXL) und Schuhgrößen (EU-Zahlen) laufen nur über `size_raw` plus die generische
  Attribut-Filterung, nicht über eigene Spalten. Der Jeans-Größenparser (M3) markiert sie korrekt
  als nicht parsebar (geloggt, nicht geraten) — das ist beabsichtigtes Verhalten, kein Bug, und
  konsistent mit der expliziten Nicht-MVP-Grenze "Größenumrechnung zwischen Systemen".
- **Produkt-Matching-Bug beim ersten Anlauf:** Die Marken-Alias-Tabelle in
  `app/normalize/brand.py` ist die gemeinsame Quelle für alle Kategorien (Generator UND Parser
  nutzen dieselbe Tabelle, siehe M3). Beim Hinzufügen von Sneaker-Marken (Nike, Adidas, ...) zu
  dieser gemeinsamen Tabelle wählte der Jeans-Template-Generator versehentlich auch aus der vollen
  Markenliste statt nur aus jeans-passenden Marken — Ergebnis waren "Nike Jeans" in den
  Testdaten. Behoben durch eine explizite `JEANS_BRANDS`-Teilliste im Generator statt der vollen
  Tabelle. Zeigt, dass eine geteilte Konfigurationsquelle über Kategorien hinweg zwar Duplikation
  vermeidet, aber explizite Scoping-Grenzen pro Kategorie braucht, wo die Domänen sich nicht
  überschneiden.
- **Preisverlauf-Simulationsskript ist idempotent pro Variante**, nicht nur pro Lauf: beim
  Reset+Reimport nach der Kategorie-Erweiterung lief es erneut über alle (jetzt 780 statt 660)
  Varianten und reicherte nur die tatsächlich neuen an.

## Post-MVP-Erweiterung: Paket 1 (lokaler Nutzerzustand) + Paket 2 (gemessener Rabatt)

### Paket 1 — Merkliste, gespeicherte Suchen, Dark Mode

- **localStorage statt Nutzerkonten.** Merkliste, gespeicherte Suchen und "zuletzt angesehen"
  sind bewusst pro Browser und ohne Login umgesetzt. Damit bleibt die in `CLAUDE.md` gezogene
  Grenze "keine serverseitige Identität" bestehen, und drei der vier gewünschten Features sind
  ohne Auth, Mailversand und DSGVO-Fragen sofort nutzbar. Ein späterer Umzug auf echte Konten
  ist eine Migration der Datenhaltung, keine Neukonzeption der UI.
- **Gespeichert werden nur IDs, nie Produktkopien.** Die Merkliste hält `variant_id` plus
  Zeitstempel; alles Anzeigbare wird bei jedem Aufruf über den neuen Endpunkt
  `GET /api/variants?ids=…` frisch geladen. Eine im Browser eingefrorene Produktkopie würde sonst
  Preise anzeigen, die es nicht mehr gibt — genau der Fehler, den diese Seite eigentlich aufdeckt.
  Der Endpunkt liefert dieselbe Item-Form wie `/api/search`, deshalb rendert die Merkliste
  dieselbe Karte wie die Suche (`ResultCard`), ohne zweite Darstellungslogik.
- **Ausnahme `price_eur_at_save`.** Der Preis zum Zeitpunkt des Merkens wird lokal festgehalten,
  weil er ein historischer Messwert ist und nicht rekonstruiert werden kann: Er ist die
  Vergleichsbasis für "günstiger/teurer als beim Merken".
- **Gespeicherte Suche = Querystring.** Der Filterzustand liegt bereits vollständig in der URL
  (M6). Eine gespeicherte Suche speichert deshalb nur diesen String plus einen Namen — kein
  zweites Filter-Schema, das mit `filters.js` synchron gehalten werden müsste.
- **Theme: `data-theme` am `<html>`, nicht `prefers-color-scheme` im CSS.** `initTheme()` löst
  "system" vor dem ersten Rendern in JS auf und stempelt das Ergebnis als Attribut. So braucht das
  Stylesheet nur `:root` und `:root[data-theme="dark"]`, ein expliziter Nutzerwunsch schlägt die
  Systemeinstellung sauber, und ein Reload im Dark Mode blitzt nicht kurz hell auf. Alle Farben
  laufen über Tokens in `index.css`; die Dark-Palette ist ein einzelner Override-Block.
- **`localStore.js` cached geparste Werte pro Key.** `useSyncExternalStore` verlangt ein
  referenziell stabiles `getSnapshot()`; ein frisches `JSON.parse()` pro Aufruf würde eine
  Render-Schleife auslösen.

### Paket 2 — Deals aus gemessener statt behaupteter Preissenkung

- **Der Streichpreis wird für das Deal-Ranking gar nicht erst benutzt.** `list_price` ist eine vom
  Shop frei gesetzte Zahl. `GET /api/deals` vergleicht stattdessen den aktuellen Preis mit dem
  Preis, den wir vor `window_days` Tagen selbst aufgezeichnet haben. Das ist der eine Punkt, an dem
  die append-only-Preishistorie einen Vorteil ergibt, den ein reiner Preisvergleicher ohne eigene
  Historie nicht nachbauen kann.
- **Referenzpunkt = jüngster Snapshot, der mindestens `window_days` alt ist.** Nicht der Höchst-
  oder Durchschnittspreis im Fenster: Die Aussage soll wörtlich "so viel hat der Artikel vor X
  Tagen gekostet" sein und am Datum des Snapshots überprüfbar bleiben (die Karte zeigt es an).
  Varianten ohne so alten Snapshot fallen aus der Liste, statt mit einer geratenen Basis zu
  erscheinen — deshalb ist `window_days=365` bei ~35 Tagen Demo-Historie korrekterweise leer.
- **Integer-Fallstrick.** `price_cents` sind Ganzzahlen; die Rabattberechnung multipliziert
  zuerst mit `100.0`, sonst schneidet die Ganzzahldivision in SQL jede Senkung auf 0 ab.
- **Zwei Rabattbegriffe, überall nebeneinander gezeigt.** "Rabatt laut Shop" (gegen den
  Streichpreis) und "tatsächlicher Rabatt" (gegen den höchsten je von uns beobachteten Preis)
  stehen auf der Detailseite direkt nebeneinander, statt einen der beiden zu unterdrücken. Wo die
  Behauptung mindestens 5 Prozentpunkte über der Messung liegt, wird die Differenz benannt.
- **Shop-Vertrauensscore ist die Aggregation des bestehenden M7-Checks.** Der
  Streichpreis-Ehrlichkeits-Check existierte pro Artikel; `GET /api/dashboard/shop-trust` rollt
  ihn pro Shop auf. Der teure Teil (Scan über alle Snapshots) bleibt als Gruppierung in der
  Datenbank, die Aufsummierung pro Shop läuft über eine Zeile je Variante in Python.
- **`app/pricing/history.py` als reine Funktionen ohne ORM.** Die Regeln, was Tiefstpreis,
  "seit wann nicht günstiger" und tatsächlicher Rabatt bedeuten, sind ohne Datenbank
  unit-testbar (`tests/test_pricing_history.py`) — dieselbe Trennung wie bei den Normalisierern
  und Extraktoren.

## Post-MVP-Erweiterung: Paket 3 (Konten, Preisalarm, Suchagent)

Bewusste Scope-Änderung: `CLAUDE.md` und der Spec führten Nutzerkonten, Wunschlisten und
Benachrichtigungen als ausdrücklich nicht enthalten. Preisalarm und Suchagent lassen sich ohne
serverseitige Identität aber grundsätzlich nicht bauen — irgendetwas muss laufen, während der
Browser zu ist, und wissen, wohin das Ergebnis geht. Alles andere bleibt ohne Konto benutzbar.

- **Passwortlos statt Passwörter.** Login läuft über einen einmalig gültigen Magic-Link. Damit
  entfallen Passwort-Hashing, Passwort-Reset-Flow und die Haftung für gespeicherte Passwörter
  komplett — bei einer Anwendung, deren einziger Zweck Benachrichtigungen per Mail sind, ist die
  Mailadresse ohnehin der Anker.
- **Nur Hashes in der Datenbank**, für Login-Token und Session gleichermaßen. Ungesalzenes SHA-256
  ist hier korrekt und *nicht* auf Passwörter übertragbar: Die Token sind 32 Byte aus `secrets`,
  es gibt kein Wörterbuch anzugreifen und keinen Grund für eine langsame KDF, während der
  ungesalzene Hash den Lookup ein indizierter Gleichheitsvergleich bleiben lässt.
- **Cooldown von 60 Sekunden pro Adresse** beim Anfordern eines Login-Links. Ohne das wäre der
  Endpunkt ein Mail-Bombing-Werkzeug gegen beliebige Dritte. Die Antwort ist immer dieselbe,
  egal ob Konto neu, bekannt oder gerade gebremst — sonst verrät der Endpunkt, wer ein Konto hat.
- **Zwei Anti-Spam-Regeln wiegen schwerer als der Auslöser selbst** (`app/notify/rules.py`):
  Eine Wiederholungsmail setzt einen *echt niedrigeren* Preis als den zuletzt gemeldeten voraus,
  und ein Alarm ohne Zielpreis feuert nur bei einem Preis, den wir noch nie aufgezeichnet haben.
  Ohne die erste Regel schickt ein um den Zielpreis pendelnder Preis bei jedem Lauf eine Mail.
  Beide Regeln sind reine Funktionen und in `tests/test_notify_rules.py` vollständig abgedeckt.
- **Ein Suchagent ist ein gespeicherter Querystring**, exakt der String aus der Frontend-URL.
  Damit ist eine gespeicherte Suche (Paket 1) und ein Suchagent dieselbe Sache in zwei
  Speicherorten, statt zweier paralleler Filterdarstellungen. `filters_from_query_string()`
  parst ihn ohne HTTP-Request und verwirft unparsebare Einzelwerte, statt den ganzen Lauf
  abzubrechen — ein Agent kann Monate alt und sein Query von Hand editiert worden sein.
- **"Neu" heißt `variant.created_at > last_run_at`**, also dieselbe Spalte, auf der schon die
  "Neuheit"-Sortierung beruht. Ein erneuter Import eines bestehenden Angebots zählt damit nicht
  als neu (Varianten werden über `shop_id + shop_sku` gematcht, M2). `last_run_at` startet bei
  der Anlage, damit ein frischer Agent nicht den kompletten Bestand als erste Mail schickt.
- **Ohne konfiguriertes SMTP wird Mail geloggt statt versendet.** Bewusst kein stiller No-Op:
  Login-Link und Benachrichtigungstexte landen im Log, damit der komplette Ablauf ohne
  Mailserver durchspielbar bleibt. Das machte eine zweite Änderung nötig — `app/main.py`
  konfiguriert jetzt Logging auf INFO. Vorher konfigurierte *nichts* im Projekt Logging, der
  Root-Logger stand auf WARNING, und die Zeilen verschwanden spurlos (nur `logger.warning` aus
  dem Größen-Parser war sichtbar, über Pythons Last-Resort-Handler). Damit wäre die Anmeldung in
  der Entwicklung schlicht unmöglich gewesen.
- **Merkliste mit zwei austauschbaren Backends.** `watchlist.jsx` bedient dieselbe Schnittstelle
  aus localStorage (abgemeldet) oder aus dem Konto (angemeldet); `WatchButton` und die
  Merklisten-Seite wissen nicht, welches aktiv ist. Die Anmeldung übernimmt nichts automatisch —
  die Seite bietet einen einmaligen Import an. Bereits im Konto liegende Einträge behalten dabei
  ihren ursprünglichen `price_cents_at_save`: Der Wert ist ein historischer Messwert, ihn zu
  überschreiben würde den Vergleich "günstiger als beim Merken" verfälschen.
- **Nebenbei behoben:** Varianten ohne `image_url` (im Feed erlaubt, Spalte hat Default `""`)
  rendered ein `<img src="">`. Browser interpretieren das als Verweis auf die aktuelle Seite und
  laden sie als Bild erneut. Die neue Komponente `ProductImage` rendert stattdessen einen
  Platzhalter.
