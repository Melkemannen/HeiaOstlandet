# Query Planning-modul (`astar_island/query_planning/`)

## Oversikt
Planlegger hvilke viewports (15x15) som skal observeres og i hvilken rekkefølge. Produserer en liste med query-dicts – utfører INGEN API-kall.

## Strategi (v1: coverage-first)
- 9 viewports per seed i 3x3 grid: posisjonene (0,0), (0,13), (0,25), (13,0), ... (25,25)
- Overlapp i sone 13-14 og 25-27 gir multiple observasjoner der
- 9 × 5 seeds = 45 queries for full kartdekning
- Resterende 5 queries → repeat-observasjoner på settlement-tette viewports

## Forbedringspotensial
1. **Depth over breadth**: Færre unike viewports, flere repeats for bedre statistikk
2. **Smart plassering**: Senter viewports rundt settlement-clustere, ikke uniform grid
3. **Adaptiv**: Kjør noen queries → analyser → juster plassering for resten
4. **Per-seed differensiering**: Seeds med mange settlements trenger mer oppmerksomhet

## Bruk
```python
queries = plan_viewports(initial_data_list, total_budget=50)
# Returnerer liste med dicts: {seed_index, viewport_x, viewport_y, viewport_w, viewport_h, reason}
```

VIS ALLTID planen til brukeren og vent på godkjenning før utførelse.
