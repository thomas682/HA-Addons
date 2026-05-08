# Pflichtbindung (ABSOLUT)

GO für genau das beschriebene Problem und prüfe anschließend ob alles tatsächlich 100% gelöst und abgeschlossen und erledigt wurden.
Beachte dabei die Agent.md zu 100% ohne Ausnahme.
Es ist verboten von den Regeln von Agent.md abzuweichen.
Sobald ein Issue aktiv begonnen wurde, ist ausschließlich dieses Issue der gültige Arbeitskontext.
Ein aktives Issue darf erst dann als abgeschlossen behandelt oder gemeldet werden, wenn für genau dieses Issue vollständig erledigt sind:

1. Umsetzung
2. relevante QA
3. Sicherheitsprüfung falls nötig
4. Versionsbump falls nötig
5. CHANGELOG/MANUAL falls nötig
6. Commit
7. Push
8. GitHub-Issue auf done gesetzt und geschlossen
9. Abschlusssignal
10. erst danach Queue-/Restprüfung

Bis dahin ist VERBOTEN:- auf ein anderes Issue umzuschalten- einen früheren Abschlusszustand wiederzuverwenden- eine Abschlussmeldung zu erzeugen- einen globalen Fertigzustand zu behaupten- andere offene Issues zu prüfen oder zu berichten, außer ein echter Blocker verhindert die Weiterarbeit am aktiven Issue.

Jede substanzielle Status- oder Abschlussmeldung muss die aktive Issue-Nummer referenzieren.
Wenn die aktive Issue-Nummer nicht eindeutig ist oder die obigen Punkte nicht vollständig erfüllt sind, ist eine Abschlussmeldung verboten
