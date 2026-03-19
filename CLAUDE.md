# HeiaOstlandet – NM i AI 2026

## Prosjektoversikt
Repo for lag HeiaØstlandet i NM i AI 2026 (19.–22. mars). Tre oppgaver, hver i sin mappe.

## Kritiske regler (gjelder ALLE oppgaver)

1. **ALDRI kjør irreversible API-kall uten eksplisitt godkjenning fra brukeren.** Budget-kostende kall, submissions, osv.
2. **Vis plan FØRST, vent på godkjenning.** Splitt arbeid i faser: analyse → plan (vis) → execute (godkjenn).
3. **Les ALL dokumentasjon før du bygger løsninger.**
4. **Forklar hva du gjør og hva som skjedde.** Logg alltid resultater i oppgavens `lessons.md`.
5. **Kjør i batches, ikke alt på én gang.**
6. **Fokusér kun på aktiv oppgave.** Les kun filer i mappen til oppgaven du jobber med. Ikke les, analysér eller cache innhold fra de andre oppgavemappene. Dette sparer tokens og holder context-vinduet fokusert.

## Oppgaver

| Mappe | Oppgave | Status |
|-------|---------|--------|
| `astar-island/` | Astar Island – terrengprediksjon | Runde 1 ferdig (19.1 pts), venter på runde 2 |
| `tripletex/` | Tripletex: AI Accounting Agent | Ikke startet |
| `norgesgruppen/` | NorgesGruppen Data: Object Detection | Ikke startet |

## Repostruktur
```
CLAUDE.md                 # Denne filen (overordnet)
astar-island/             # Oppgave 1
  run.py                  # Hovedskript med faser
  requirements.txt
  lessons.md              # Leksjoner for denne oppgaven
  astar_island/           # Python-pakke
  docs/                   # Instruksjonsfiler per modul
tripletex/                # Oppgave 2
  lessons.md
norgesgruppen/            # Oppgave 3
  lessons.md
```

Hver oppgave har sin egen `lessons.md` med leksjoner og regler spesifikke for den oppgaven.
