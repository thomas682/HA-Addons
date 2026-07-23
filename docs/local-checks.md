# Lokale Checks und manuelle Betriebsablaeufe

Vor Commit und Push wird die Dokumentationspruefung lokal ausgefuehrt:

```sh
scripts/run-local-checks.sh
```

Wenn `AGENTS.md` geaendert wurde und ein Vergleich gesichert werden soll, wird
die lokale Sicherung bewusst manuell erzeugt:

```sh
scripts/backup-agents.sh
```

Die Sicherung erzeugt nur lokale Vergleichsdateien. Sie wird nicht automatisch
committet oder gepusht.

## Issue-Status und Release-Notizen

Statuslabels und Release-Notizen werden bei Bedarf manuell im zugehoerigen
GitHub-Issue gepflegt. Vor dem Schliessen eines Issues ist genau ein
`status/*`-Label zu setzen. Ein Release-Entwurf wird nicht automatisch erzeugt;
Release-Notizen werden erst bei einem ausdruecklich beauftragten Release aus
Changelog, Version und validiertem Commit zusammengestellt.
