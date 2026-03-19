# Prediksjon-modul (`astar_island/prediction/`)

## Oversikt
Bygger H×W×6 sannsynlighetstensorer som predikerer terrengtype per celle etter 50 års simulering.

## Filer

### `priors.py`
Prior-sannsynligheter basert på initial state for UOBSERVERTE celler:
- Mountain (5) → 100% Mountain (statisk)
- Ocean (10) / border → 100% Empty (statisk)
- Empty/Plains nær settlement → høyere sjanse for Settlement, Port
- Forest langt fra settlement → 85% Forest
- Settlement → blanding, mest Settlement
- Port → blanding, mest Port

### `builder.py`
Kombinerer observasjoner + priors:
- **Multiple observasjoner**: Empirisk frekvens + Bayesian smoothing
- **Én observasjon**: Observasjon med usikkerhets-blending (α=0.15)
- **Uobservert**: Prior + 15% global frekvens-blending for dynamiske celler

### `submit.py`
- `validate_prediction(pred, h, w)` – Sjekk shape, sum=1, min≥0.01
- `normalize_prediction(pred)` – Enforce minimum floor, renormaliser
- `submit_predictions(client, ...)` – Send inn alle seeds

## Scoring
`score = max(0, min(100, 100 * exp(-3 * weighted_kl)))`
- Entropy-vektet KL-divergens: celler med høy entropi (usikre) vektes mer
- ALDRI sett sannsynlighet til 0.0 – bruk MIN_PROB=0.01
- Bedre å være litt usikker (flat fordeling) enn helt feil (spiss feil)

## Forbedringspotensial
1. Bruk settlement-stats for å modellere vekst/kollaps
2. Modeller sim-mekanikk: vekst → konflikt → handel → vinter → miljø
3. Monte Carlo-estimater fra multiple observasjoner
