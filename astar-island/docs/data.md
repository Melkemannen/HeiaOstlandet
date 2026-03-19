# Data-modul (`astar_island/data/`)

## Oversikt
Lagring og lasting av query-data til disk. Viktig for å kunne re-analysere uten å bruke queries.

## Filer

### `cache.py`
- `save_query_results(round_id, results)` – Lagre simulate-resultater til JSON
- `load_query_results(path)` – Last fra disk
- `save_round_details(round_id, details)` – Lagre initial states og rundeinfo

## Lagringssti
`cached_data/` (i prosjektrot, gitignored)

## Filformat
- `queries_{round_id}_{timestamp}.json` – Simulate-resultater
- `round_{round_id}.json` – Rundedetaljer med initial states

## Viktig
- ALLTID cache query-resultater etter utførelse
- Bruk `--cached` flag i run.py for å re-analysere uten nye queries
- Cached data muliggjør iterativ forbedring av prediksjonslogikken
