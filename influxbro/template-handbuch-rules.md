# Handbuch- und Dokumentationsspruenge

> Stand: 2026-05-09 · Sprache: Deutsch · Gilt fuer alle Handbuchbuttons, Tooltip-Doku-Buttons, F1-Hilfe und interne Dokumentationsdialoge.

## 1. Herkunft und Pflichtbindung

Diese Datei buendelt die aus `AGENTS.md` in die spezifische Handbuch-Regeldatei transferierten UI-/Template-Grundregeln und ergaenzt sie um verbindliche Handbuch-Navigationsregeln.

Aus `AGENTS.md` transferierte Grundregeln fuer Handbuch-UI:

- Templates bleiben selbststaendig; es gibt keinen Build-Schritt.
- Relative, Ingress-kompatible URLs sind Pflicht. Interne API-/Asset-Pfade muessen relativ bleiben, z. B. `./api/...`.
- JavaScript bleibt einfach, ohne Framework, mit kleinen Funktionen und expliziten DOM-Lookups.
- Vor Handbuch-/Dokumentations-UI-Aenderungen muessen `influxbro/Template.md` sowie die jeweils betroffenen Spezialregeln gelesen und beachtet werden.
- Dialogbasierte Handbuch-Viewer muessen `influxbro/template-dialog-rules.md` befolgen.
- Tooltip-Doku-Aufrufe muessen `influxbro/template-tooltips-rules.md` befolgen.
- Picker-/Support-Referenzen muessen `influxbro/template-picker-rules.md` befolgen.
- Jede sichtbare Handbuch-UI-Komponente braucht stabile `data-ui` und `data-ib-pickkey`.
- Dynamisch erzeugte Handbuch-Buttons, Dialoge, Toolbar-Aktionen und Fallback-Hinweise muessen `data-ui` und `data-ib-pickkey` beim Erzeugen setzen.

## 2. Zentraler Resolver

- Alle Handbuchaufrufe muessen ueber einen zentralen Doc-Resolver laufen.
- Direkte Einzel-Implementierungen wie `window.open('./manual?q=...')` sind fuer Handbuchbuttons und Tooltip-Doku-Buttons verboten.
- Der Resolver akzeptiert mindestens diese Quellwerte:
  - `data-doc-key`
  - `data-ui`
  - `data-ib-pickkey`
  - Dialogname (`data-dialog-name`)
  - Dialog-Trigger (`data-dialog-trigger`)
  - Tooltip-Key
- Der Resolver liefert ein Zielobjekt mit:
  - stabiler Ziel-ID (`doc`)
  - internem Anchor (`anchor`)
  - lesbarem Titel (`title`)
  - Suchfallback (`query`)
  - optionalem externem GitHub-Fallback (`github`)

## 3. Zielgenauigkeit

- Bekannte Keys muessen auf stabile Handbuchziele springen, nicht nur auf eine Volltextsuche.
- Ein bekanntes Ziel gilt erst als stabil, wenn der Anchor im gerenderten Handbuch existiert oder durch die Handbuchseite als Alias bereitgestellt wird.
- Der Parameter `?doc=<key>` ist der kanonische interne Deep-Link fuer Handbuchspruenge.
- `?q=<text>` ist nur Fallback fuer unbekannte oder noch nicht inventarisierte Keys.
- Unbekannte Keys muessen eine klare Fallback-Behandlung haben: Suche nach dem Key oder einem abgeleiteten Suchtext plus Hinweis im Handbuchdialog.

## 4. Ingress und Oeffnungsverhalten

- Primaerziel fuer Handbuchbuttons ist ein integrierter Handbuchdialog innerhalb der App.
- Neue Tabs sind nur sekundaere Aktionen, z. B. `Im Handbuch oeffnen` oder `Auf GitHub ansehen`.
- Handbuchbuttons duerfen nicht standardmaessig einen neuen HA-Ingress-Tab oeffnen, weil direkte Ingress-URLs 401-Fehler verursachen koennen.
- Interne Handbuch-URLs muessen relativ sein, z. B. `./manual?doc=<key>#<anchor>`.
- GitHub darf nur Fallback oder Zusatzaktion sein, weil GitHub-Inhalte von der lokal installierten Add-on-Version abweichen koennen.

## 5. Handbuchdialog

- Der integrierte Handbuchdialog muss dem Dialogstandard folgen.
- Pflichtstruktur:
  - Kopf mit Titel `Handbuch`
  - fachliche Kurzbeschreibung
  - iframe oder integrierter Inhaltsbereich im gleichen Origin-/Ingress-Kontext
  - Footer mit Aktionen `Im Handbuch oeffnen`, optional `Auf GitHub ansehen`, `Schliessen`
- Der Dialog muss per Tastatur bedienbar sein und bei `F1` denselben Resolver nutzen wie der sichtbare Handbuchbutton.
- Der Dialog darf externe Inhalte nicht als Primaerinhalt laden.

## 6. Bilder und Assets

- Bilder im Handbuch muessen weiter ueber die interne Asset-Route funktionieren.
- Relative Markdown-Bilder werden intern ueber `./api/manual_asset?path=...` geladen.
- Der integrierte Handbuchdialog muss dieselbe interne Handbuchseite verwenden, damit Bilder, Links und Ingress-Kontext unveraendert funktionieren.
- GitHub-Bildpfade duerfen interne Bildpfade nicht ersetzen.

## 7. Fallback-Kette

Resolver-Fallback in dieser Reihenfolge:

1. Exakter bekannter `docKey` mit stabilem Anchor
2. Alias-Key mit stabilem Anchor
3. Interne Suche (`?q=<Suchtext>`)
4. Handbuch-Startseite mit sichtbarem Hinweis, dass kein exakter Eintrag existiert
5. Optionaler GitHub-Link als externe Zusatzaktion

## 8. Tests

Bei Aenderungen an Handbuchbuttons, Handbuchdialogen oder Manual-Deep-Links sind mindestens zu pruefen:

- `AGENTS.md` verweist auf `influxbro/template-handbuch-rules.md`.
- `template-handbuch-rules.md` enthaelt die transferierten Grundregeln und die Resolver-Regeln.
- Dialog-Handbuchbutton, Tooltip-Doku-Button und `F1` verwenden denselben Resolver.
- Ein bekannter Key wie `dashboard_selection.btn_measurement_profile_runtime_info` springt zu einem exakten Anchor.
- Ein unbekannter Key faellt kontrolliert auf Suche zurueck.
- Bilder im Handbuch werden weiterhin ueber `./api/manual_asset?path=...` gerendert.
- Ein lokaler UI-Smoke-Test bestaetigt, dass der Handbuchdialog ohne 401 im Ingress-kompatiblen relativen Pfad laedt.
