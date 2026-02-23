# Changelog

Alle nennenswerten Aenderungen an diesem Repository werden in dieser Datei dokumentiert.
Home Assistant erkennt Updates ueber `influxbro/config.yaml:version`.

Das Format orientiert sich an "Keep a Changelog" (kurz gehalten).

## 1.1.2f - 2026-02-23

### Added

- Konfig-UI: Button "influx.yaml suchen" (keine automatische Suche beim Start).
- API: `GET ./api/find_influx_yaml` zum Finden einer `influx.yaml` unter `/config`.

### Changed

- Konfig-UI: Button "yaml Daten einlesen" liest YAML erst nach explizitem Klick ein.
- Konfig-UI: Button "Influx Verbindung testen" (Umbenennung) testet die Verbindung per API.

### Fixed

- `load_cfg()`/`save_cfg()` Logik korrigiert, damit Runtime-Konfig sauber geladen/gespeichert wird.
- YAML-Parsing robuster: Home-Assistant YAML Tags wie `!secret` werden ueber `secrets.yaml` aufgeloest.

## 1.1.2g - 2026-02-23

### Added

- `influxbro/requirements.txt` fuer reproduzierbare Abhaengigkeiten.
- `pyproject.toml` (ruff/black Defaults) und `.pre-commit-config.yaml`.

### Changed

- `influxbro/Dockerfile` installiert Dependencies aus `influxbro/requirements.txt`.
- `README.md` an aktuelle Ordnerstruktur (`influxbro/`) und aktuellen Flow angepasst.
- `influxbro/app/app.py` unterstuetzt optional `CONFIG_DIR`/`DATA_DIR` env overrides (Default: `/config`, `/data`).

## 1.1.2h - 2026-02-23

### Fixed

- `.pre-commit-config.yaml` korrigiert (gueltiges YAML).
- `README.md` tatsaechlich aktualisiert (Ordnernamen + kurzer Dev-Abschnitt).

## 1.1.2i - 2026-02-23

### Added

- pytest Grundgeruest: `tests/`, `pytest.ini`, `requirements-dev.txt`.
- API Smoke Tests fuer YAML-Flow und `/api/test` (mit Mocks, ohne echte InfluxDB).

## 1.1.2j - 2026-02-23

### Added

- UI zeigt Add-on Version jetzt auch in der Konfiguration an.
- Kleine Hilfetexte unter den relevanten Eingabefeldern (Config + Delete-Bestaetigung).
