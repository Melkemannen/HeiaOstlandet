# Analyse-modul (`astar_island/analysis/`)

## Oversikt
Gratis analyse av initial states og simulate-resultater. Ingen API-kall, ingen budsjett-kostnad.

## Filer

### `initial_state.py`
- `analyze_initial_state(state, seed_idx)` – Analyser terrengfordeling og settlements for ett seed
- `find_dynamic_regions(initial_data, radius=8)` – Identifiser celler som sannsynligvis endrer seg

**Dynamiske celler:** Landceller innen `radius` av en settlement (ikke fjell/hav).
**Statiske celler:** Mountain (5) og Ocean (10) – endrer seg aldri.

### `observations.py`
- `collect_observations(query_results, seed_index, ...)` – Samle per-celle observasjoner fra simulate-data
- `compute_global_frequencies(observations)` – Globale frekvenser for fallback-prior

## Viktig
- Initial state er GRATIS – bruk det maksimalt for analyse
- Settlements fra initial state gir posisjon, has_port, alive
- Simulate-response gir også settlement-stats (population, food, wealth, defense, owner_id) – bruk disse!
- Observasjoner er (y, x)-indeksert, ikke (x, y)
