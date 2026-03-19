# Astar Island – Instruksjoner for Claude

## Oppgaveoversikt
Prediker sannsynlighetsfordelinger for terrengtyper på et 40x40 grid etter 50 år med Norse-sivilisasjonssimulering.

## Kritiske regler
1. **ALDRI kjør simulate- eller submit-kall uten eksplisitt godkjenning.** 50 queries per runde.
2. **Vis plan FØRST, vent på godkjenning.** Faser: analyse (gratis) → plan (vis) → execute (godkjenn).
3. **Kjør i batches.** F.eks. 5-10 queries → vis resultater → juster → fortsett.

## Prosjektstruktur
```
run.py                    # Hovedskript med faser
astar_island/
  config.py               # Konstanter og terrain-mapping
  api/client.py           # HTTP-klient med rate limiting
  analysis/
    initial_state.py      # Analyser initial states (gratis)
    observations.py       # Aggreger simulate-resultater
  query_planning/
    planner.py            # Viewport-planlegging
  prediction/
    priors.py             # Prior-sannsynligheter
    builder.py            # Bygg sannsynlighetsfordelinger
    submit.py             # Validering og innsending
  data/cache.py           # Lagring til disk
docs/                     # Instruksjonsfiler per modul
```

## Terrengklasser (6 stk)
0=Empty, 1=Settlement, 2=Port, 3=Ruin, 4=Forest, 5=Mountain

Terrengkoder → klasser: Ocean(10)→0, Plains(11)→0, Empty(0)→0

## Statiske regler
- Mountain (5) og Ocean (10) endrer seg ALDRI
- Kanten av kartet (hele rammen) er alltid Ocean
- Minimum sannsynlighet per klasse: 0.01 (aldri 0.0)
- Scoring: entropy-weighted KL divergence

## API
- Base: https://api.ainm.no/astar-island/
- Rate limits: simulate 5/s, submit 2/s
- Submit overskriver – siste innsending teller

## Runde 1 lærdom (19.1 pts, #73/117)
- Settlement-ekspansjon er en ROMLIG prosess (store sammenhengende klynger), ikke uavhengige per-celle sannsynligheter
- 1 observasjon per celle er utilstrekkelig — trenger multiple samples
- Se lessons.md for full post-mortem
