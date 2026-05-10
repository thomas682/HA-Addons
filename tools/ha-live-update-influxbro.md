# InfluxBro HA-Live-Update per Core API

Dieser Ablauf ist der bevorzugte Weg fuer Schritt D2 aus `AGENTS.md`. Er nutzt die
Home-Assistant-Core-API statt Playwright-UI und vermeidet dadurch HA-Login- sowie
Node/Playwright-Netzwerkprobleme.

## Voraussetzungen

- `SUPERVISOR_TOKEN` ist in der Shell gesetzt.
- Der Token ist gegen `http://192.168.2.200:8123/api/config` gueltig.
- `influxbro/config.yaml` enthaelt die erwartete Zielversion.
- Das Add-on ist ueber `http://192.168.2.200:8099/api/info` erreichbar.

## Ablauf

1. Erwartete Version aus `influxbro/config.yaml` bestimmen.
2. Live-Version vor dem Update ueber `/api/info` erfassen.
3. HA-Update-Entity refreshen:

   ```bash
   curl -fsS \
     -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"entity_id":"update.influxbro_update"}' \
     http://192.168.2.200:8123/api/services/homeassistant/update_entity
   ```

4. `update.influxbro_update` pollen, bis `attributes.latest_version` der erwarteten
   Version entspricht und `state` `on` ist:

   ```bash
   curl -fsS \
     -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
     http://192.168.2.200:8123/api/states/update.influxbro_update
   ```

5. Update installieren:

   ```bash
   curl -fsS \
     -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"entity_id":"update.influxbro_update","backup":false}' \
     http://192.168.2.200:8123/api/services/update/install
   ```

6. `/api/info` pollen, bis `version` exakt der erwarteten Version entspricht:

   ```bash
   curl -fsS http://192.168.2.200:8099/api/info \
     | python3 -c "import json,sys; print(json.load(sys.stdin).get('version','unknown'))"
   ```

## Erfolgreich verifizierter Pfad

- Ausgangsversion: `1.12.586`
- Zielversion: `1.12.587`
- Refresh: `homeassistant.update_entity` fuer `update.influxbro_update`
- Installation: `update.install` fuer `update.influxbro_update` mit `backup=false`
- Ergebnis: `/api/info` meldete `1.12.587`

## Fehlerklassifizierung

- `401` auf `/api/hassio/*` ist fuer diesen Ablauf nicht relevant; dieser Pfad nutzt
  die Core-API unter `/api/services/*` und `/api/states/*`.
- Wenn `latest_version` nicht auf die erwartete Version springt, ist der Store-Refresh
  oder Repository-Index noch nicht aktuell.
- Wenn `update.install` erfolgreich antwortet, aber `/api/info` nicht aktualisiert
  wird, ist die Live-Version-Verifikation blockierend fehlgeschlagen.
- Tokens duerfen nie ausgegeben, geloggt oder in Issue-Kommentare kopiert werden.
