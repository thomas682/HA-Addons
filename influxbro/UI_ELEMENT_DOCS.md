# UI Element Documentation Inventory

Diese Datei sammelt maschinell und manuell nachvollziehbare Erkenntnisse fuer Tooltip- und Handbuchtexte. Sie ist als redaktionelle Arbeitsliste gedacht und kann erweitert werden.

Ermittlungslogik:

- stabile Referenz aus `data-ui` und `data-ib-pickkey`
- sichtbarer Button-/Labeltext, `aria-label`, `title` und Placeholder
- umgebende Section, Tabellenkopf, Statusfeld und Nachbartexte
- bekannte JS-Handler, Dialognamen, API-Aufrufe und bisherige Issue-/Tombstone-Kommentare

## Dashboard / Ausreisser

### dashboard_outliers.btn_autobreite

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.btn_autobreite`
- Kurztext: Passt die Spaltenbreiten der Ausreisser-Tabelle automatisch an den Inhalt an.
- Langtext: Dieser Button misst die sichtbaren Inhalte der Ausreisser-Tabelle und setzt die Spaltenbreiten so, dass Zeit, Wert, Aenderung, Ausreissergrund und Raw-Kontext moeglichst gut lesbar sind. Nutze ihn nach Analyse, Filterwechsel oder wenn manuelle Spaltenbreiten die Tabelle unuebersichtlich machen.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: Toolbar `dashboard_outliers.row_table_actions`, Tabellen-ID `raw_outlier_tbl`, SVG-Autobreiten-Icon, Tabellen-Helper.

### dashboard_outliers.btn_fensterbreite

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.btn_fensterbreite`
- Kurztext: Verteilt die Ausreisser-Tabelle auf die verfuegbare Fensterbreite.
- Langtext: Dieser Button richtet die Tabellenbreite am aktuellen Anzeigebereich aus. Das ist hilfreich nach Zoom-, Sidebar- oder Fensterbreiten-Aenderungen, damit die Ausreisser-Tabelle den sichtbaren Platz nutzt und horizontales Scrollen reduziert wird.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: Toolbar, Fensterbreiten-Icon, Tabellen-Layout-Controls.

### dashboard_outliers.btn_spalten

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.btn_spalten`
- Kurztext: Oeffnet die Auswahl zum Ein- und Ausblenden von Tabellenspalten.
- Langtext: Mit diesem Button blendest du Spalten der Ausreisser-Tabelle gezielt ein oder aus. So kannst du dich auf Zeit, Wert, Aenderung, Ausreissergrund oder Raw-Kontext konzentrieren, ohne die Analyse selbst neu zu starten.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: `data-table-colvis="raw_outlier_tbl"`, sichtbarer Text `Spalten`, Tabellenkopf.

### dashboard_outliers.chk_umbruch

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.chk_umbruch`
- Kurztext: Schaltet Zeilenumbruch in der Ausreisser-Tabelle ein oder aus.
- Langtext: Diese Checkbox entscheidet, ob lange Inhalte mehrzeilig dargestellt werden. Eingeschaltet verbessert sie die Lesbarkeit langer Aenderungs- oder Kontexttexte; ausgeschaltet bleibt die Tabelle kompakter und eignet sich fuer einen schnellen Ueberblick.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: sichtbarer Labeltext `Umbruch`, Tabellen-Toolbar, Tabellen-Layout-State.

### dashboard_outliers.chk_spaltenfilter

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.chk_spaltenfilter`
- Kurztext: Blendet spaltenbezogene Filterfelder fuer die Ausreisser-Tabelle ein oder aus.
- Langtext: Diese Checkbox aktiviert Filter direkt an den Spalten. Damit kannst du Treffer nach Zeit, Wert, Aenderung, Ausreissergrund oder Raw-Kontext eingrenzen, ohne die zugrunde liegenden Analyseergebnisse zu veraendern.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: sichtbarer Labeltext `Spaltenfilter`, Tabellenkopf, Filter-Datalist `raw_outlier_reason_options`.

### dashboard_outliers.btn_kopieren

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.btn_kopieren`
- Kurztext: Kopiert die aktuelle Ausreisser-Liste in die Zwischenablage.
- Langtext: Dieser Button kopiert die sichtbaren Ausreisserdaten als Text fuer Diagnose, Dokumentation oder Support. Pruefe vor dem Teilen, ob Messwertnamen, Zeitraeume oder andere Betriebsdaten enthalten sind, die nicht weitergegeben werden sollen.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: Copy-SVG, bestehender Tooltip-Text, Ausreisser-Tabelle.

### dashboard_outliers.btn_zeile_kopieren

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.btn_zeile_kopieren`
- Kurztext: Kopiert die aktuell markierte Ausreisser-Zeile.
- Langtext: Dieser Button kopiert nur den ausgewaehlten Treffer inklusive Zeit, Wert, Aenderungsinformation, Ausreissergrund und Raw-Kontext. Er ist geeignet, wenn ein einzelner Befund im Support oder in Notizen nachvollziehbar dokumentiert werden soll.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: sichtbarer Text `Zeile kopieren`, Tabellen-Selektion, Copy-Aktion.

### dashboard_outliers.btn_ignorieren

- Menuepunkt: Dashboard
- Section: Ausreisser
- Pickkey: `dashboard_outliers.btn_ignorieren`
- Kurztext: Markiert den ausgewaehlten Ausreisser als bewusst ignoriert.
- Langtext: Dieser Button setzt den Arbeitsstatus des selektierten Treffers auf ignoriert. Verwende ihn, wenn ein auffaelliger Wert fachlich plausibel ist oder nicht repariert werden soll. Ignorierte Treffer bleiben nachvollziehbar und koennen spaeter wieder eingeblendet werden.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: sichtbarer Text `ignorieren`, Gegenaktion `nicht mehr ignorieren`, Ausreisser-Status.

### dialog_raw_outlier_params.input_gap_seconds

- Menuepunkt: Dashboard
- Section: Ausreisser-Parameter Dialog
- Pickkey: `dialog_raw_outlier_params.input_gap_seconds`
- Kurztext: Legt den maximal erlaubten Abstand zwischen Messpunkten fuer Messwertluecken fest.
- Langtext: Dieses Eingabefeld bestimmt, ab welcher Zeitdifferenz zwischen zwei Rohdatenpunkten eine Messwertluecke als Ausreisser erkannt wird. Leer bedeutet, dass der Standardwert aus den Einstellungen verwendet wird. Kleine Werte finden mehr Luecken, koennen aber bei selten messenden Sensoren zu vielen Treffern fuehren.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: Label `Messwertluecke: Max Abstand (s)`, Placeholder, Analyse-Strategie `time_gap`.

## Picker / Ergebnisdialog

### picker_result.btn_close

- Menuepunkt: Globaler Picker
- Section: Picker-Ergebnisdialog
- Pickkey: `picker_result.btn_close`
- Kurztext: Schliesst den Picker-Ergebnisdialog.
- Langtext: Dieser Button beendet nur die Anzeige des zuletzt erzeugten Picker- oder Super-Picker-Ergebnisses. Der bereits kopierte Pick-Text bleibt in der Zwischenablage, sofern der Browser das Kopieren erlaubt hat.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: Picker-Ergebnisdialog, Kopierstatus, Close-Button.

### picker_result.btn_wrap

- Menuepunkt: Globaler Picker
- Section: Picker-Ergebnisdialog
- Pickkey: `picker_result.btn_wrap`
- Kurztext: Schaltet den Zeilenumbruch im Picker-Ergebnisdialog ein oder aus.
- Langtext: Dieser Button steuert, ob lange Pick-Referenzen und Multi-Pick-Karten umbrechen duerfen. Mit Umbruch sind lange Referenzen vollstaendig sichtbar; ohne Umbruch bleibt die Darstellung kompakt und nutzt horizontales Scrollen bzw. Ellipsen.
- Handbuch-Anker: `dashboard-ui-steuerelemente`
- Kontextquellen: neuer Umbruch-Button, Einzelausgabe `picker_result.text`, Multi-Pick-Karten.
