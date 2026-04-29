# InfluxBro (Home Assistant Add-on)

[![Addon Version](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2Fthomas682%2FHA-Addons%2Fmain%2Finfluxbro%2Fconfig.yaml&query=%24.version&prefix=v&label=Addon%20Version)](https://github.com/thomas682/HA-Addons/blob/main/influxbro/config.yaml)
[![GitHub Release](https://img.shields.io/github/v/release/thomas682/HA-Addons?sort=semver)](https://github.com/thomas682/HA-Addons/releases/latest)


[![Last Commit](https://img.shields.io/github/last-commit/thomas682/HA-Addons)](https://github.com/thomas682/HA-Addons/commits/main)
[![License](https://img.shields.io/github/license/thomas682/HA-Addons)](https://github.com/thomas682/HA-Addons/blob/main/LICENSE)

Kurze Installation:

1. Das Repository in Home Assistant hinzufuegen.

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fthomas682%2FHA-Addons)

2. Das Add-on `InfluxBro` im Add-on-Store installieren.
3. Add-on starten und optional in der Seitenleiste anzeigen.

Projekt-Doku, Screenshots und weitere Hinweise liegen unter:

- `influxbro/README.md`

## Git-Hooks fuer Versionsbump-Policy

Wenn Code-Dateien geaendert werden (`*.py`, `*.html`, `*.js`, `*.css`, `Dockerfile`, `*.sh`), muss derselbe Commit auch einen Versionsbump in `influxbro/config.yaml` enthalten.

Hook-Aktivierung lokal:

1. `git config core.hooksPath .githooks`
2. `python3 -m pip install pre-commit`
3. `pre-commit install`

Danach gilt:

- `pre-commit`: blockiert Commits mit Code-Aenderungen ohne Versionsbump in `influxbro/config.yaml`
- `.githooks/pre-push`: blockiert Pushes, wenn ein zu pushender Commit Code-Aenderungen ohne Versionsbump enthaelt
