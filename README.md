---

# InfluxBro – Home Assistant Add-on

Custom Home Assistant Add-on zur direkten Analyse und Verwaltung von InfluxDB-Daten – ohne Grafana oder Influx Data Explorer.

---

## Funktionen

* Unterstützung für InfluxDB v1 und v2
* Auswahl nach:

  * Measurement
  * Field
  * `entity_id`
  * `friendly_name`
* Zeitfilter: 24h, Woche, Monat, Jahr
* Anzeige als:

  * Tabelle
  * Mini-Graph
* Statistikübersicht:

  * Anzahl der Messwerte
  * Ältester Messwert
  * Neuester Messwert
  * Minimalwert
  * Maximalwert
* Optionale Löschfunktion mit Sicherheitsbestätigung

---

# Installation über Gitea Repository

## 1️⃣ Repository in Home Assistant hinzufügen

In Home Assistant:

```
Einstellungen → Add-ons → Add-on Store
```

Oben rechts:

```
⋮ → Repositories
```

Dann Repository-URL eintragen:

```
http://stirling.localdomain:7070/thomas/influx_browser_addons
```

Falls `stirling.localdomain` nicht erreichbar ist, stattdessen die IP-Adresse verwenden:

```
http://192.168.x.x:7070/thomas/influx_browser_addons
```

---

# 🔐 Wichtiger Hinweis zur Authentifizierung (Git Clone Fehler)

Falls folgende Fehlermeldung erscheint:

```
fatal: could not read Username for 'http://...'
```

Dann verlangt Gitea eine Anmeldung. Home Assistant kann jedoch keine interaktive Login-Abfrage durchführen.

## Lösung A (empfohlen im LAN): Repository öffentlich machen

In Gitea:

```
Repository → Settings → Visibility → Public
```

Danach funktioniert der Zugriff ohne Login.

---

## Lösung B: Access Token verwenden

1. In Gitea:

   ```
   Settings → Applications → Generate New Token
   ```

   Scope: `repository read`

2. Repository-URL in HA so eintragen:

```
http://USERNAME:TOKEN@stirling.localdomain:7070/thomas/influx_browser_addons
```

Beispiel:

```
http://thomas:ghp_xxxxxxxxx@192.168.x.x:7070/thomas/influx_browser_addons
```

⚠ Falls der Token Sonderzeichen enthält, muss er URL-encodiert werden.

---

# 2️⃣ Add-on installieren

Nach dem Hinzufügen erscheint das Repository im Add-on Store.

Dann:

* Add-on auswählen
* Installieren
* Konfigurieren
* Starten

---

# Repository-Struktur

```
repository.yaml
influxbro/
  config.yaml
  Dockerfile
  run.sh
  app/
```

---

# Update-Prozess

Home Assistant erkennt Updates ausschließlich über die Versionsnummer im Add-on.

## Schritt 1 – Version erhöhen

In:

```
influxbro/config.yaml
```

z. B.:

```yaml
version: "0.5.0"
```

Bei jeder Änderung muss die Version erhöht werden:

```
0.5.1
0.6.0
1.0.0
```

Ohne Versionsänderung erkennt HA kein Update.

---

## Schritt 2 – Änderungen committen & pushen

In Gitea:

* Änderungen speichern
* Commit erstellen
* Push durchführen

---

## Schritt 3 – Update in Home Assistant durchführen

In HA:

```
Einstellungen → Add-ons → Add-on Store
```

Dann:

```
⋮ → Check for updates
```

Wenn die Version höher ist, erscheint beim Add-on:

```
Update verfügbar
```

Update anklicken → Installieren → Neustarten.

---

# Wichtige Hinweise

* Der `slug` im `influxbro/config.yaml` darf nicht verändert werden.
* Die Ordnerstruktur darf nicht verändert werden.
* `repository.yaml` muss im Root des Repositories liegen.
* Home Assistant muss das Repository im Netzwerk erreichen können.
* Falls Hostnamen nicht aufgelöst werden, IP-Adresse verwenden.

---

# Sicherheitshinweis

Die Löschfunktion ist standardmäßig deaktiviert.
Zur Aktivierung muss in der Add-on-Konfiguration explizit:

```yaml
allow_delete: true
```

gesetzt werden.

Zusätzlich ist eine manuelle Bestätigung in der UI erforderlich.

---

# Architekturüberblick

* Ingress Add-on (läuft innerhalb von Home Assistant)
* Kommunikation direkt mit InfluxDB API
* Persistente Konfiguration im Add-on Datenverzeichnis (`/data/influx_browser_config.json`)
* Kein externer Port notwendig

---

Wenn du möchtest, kann ich dir zusätzlich noch einen Abschnitt zu:

* Versionsstrategie (SemVer)
* Release-Workflow mit Git-Tags
* Branching-Strategie für Test/Stable-Versionen

einbauen, damit dein Repo sauber wartbar bleibt.

---

## Lokale Entwicklung (kurz)

### Docker Build/Run

```bash
docker build -t influxbro:dev ./influxbro
```

```bash
mkdir -p .local-data
cat > .local-data/options.json <<'JSON'
{ "version": "dev", "allow_delete": false, "delete_confirm_phrase": "DELETE" }
JSON

docker run --rm -p 8099:8099 \
  -v "$PWD/.local-data:/data" \
  -v "$PWD:/repo:ro" \
  influxbro:dev
```

### YAML Import in der UI

In der Konfiguration gibt es zwei Schritte:
1) `influx.yaml suchen` (findet die Datei unter `/config` und fuellt den Pfad)
2) `yaml Daten einlesen` (traegt die Werte in die Felder ein; erst mit `Speichern` wird persistiert)

Danach: `Influx Verbindung testen`.
