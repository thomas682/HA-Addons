---

# InfluxBro - Home Assistant Add-on

InfluxBro ist ein Home Assistant Ingress Add-on, mit dem du InfluxDB (v1/v2) Daten direkt in HA durchsuchen, auswerten, sichern und bei Bedarf gezielt korrigieren kannst - ohne Grafana oder Influx Data Explorer.

## Was kann das Add-on?

- Messwerte nach `_measurement`, `friendly_name` und `entity_id` filtern
- Graph + Punktliste (Tabelle) im gleichen Zeitraum (Zoom optional fuer Tabelle)
- Ausreisser-/Fehlersuche (NULL/0/Grenzen/Counter-Spruenge)
- Punktliste: Werte bearbeiten/ueberschreiben (opt-in, mit Sicherheitsbestaetigung)
- Backup/Restore fuer einen einzelnen Messwert
- Statistikseite, Logs-Viewer, Background-Jobs (anzeigen + abbrechen)

## Screenshots

![Uebersicht](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/uebersicht.png)

![Einstellungen](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/Einstellungen.png)

![Backup](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/Backup.png)

![Restore](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/Restore.png)

![Logs](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/LOG.png)

![Jobs](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/Jobs.png)

![Statistik](https://raw.githubusercontent.com/thomas682/HA-Addons/refs/heads/main/influxbro/images/Statistik.png)

## Installation in Home Assistant

1) Repository hinzufuegen

- Home Assistant: `Einstellungen -> Add-ons -> Add-on Store`
- Oben rechts: `... -> Repositories`
- Repository-URL: `https://github.com/thomas682/HA-Addons`

2) Add-on installieren und starten

- Add-on `InfluxBro` auswaehlen
- `Installieren` -> `Starten`
- Optional: `In Seitenleiste anzeigen` aktivieren

3) Web UI oeffnen

- Im Add-on: `Open Web UI` (Ingress)

4) InfluxDB konfigurieren

- In InfluxBro: `Einstellungen`
- Zugangsdaten setzen (v1/v2) oder YAML Import nutzen
- `Influx Verbindung testen` -> `Speichern`

## Sicherheit

- Schreiben/Loeschen ist standardmaessig deaktiviert und muss in den Einstellungen explizit aktiviert werden.
- Zusaetzlich ist eine manuelle Bestaetigung per `delete_confirm_phrase` erforderlich (Add-on Option).

## License

MIT License - siehe `license`.
