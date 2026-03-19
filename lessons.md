# Leksjoner Lært – Astar Island (NMiAI 2026)

Oppdateres etter HVER korreksjon eller overraskelse.
Gjennomgå denne filen ved starten av hver økt.

---

## [2026-03-19] KRITISK: Kjørte irreversible API-kall uten brukerens godkjenning

**Problem:** Claude kjørte hele scriptet (50 simulate-queries + 5 submit-kall) uten å stoppe og be om godkjenning. Brukte opp hele query-budsjettet (50/50) i én kjøring.

**Lærdom:** API-kall mot konkurranse-endepunkter er IRREVERSIBLE handlinger med begrenset budsjett.

**Regel:**
1. ALDRI kjør simulate- eller submit-kall uten eksplisitt godkjenning
2. Vis alltid en plan FØRST
3. Splitt i faser: analyse (gratis) → plan (vis) → execute (godkjenn)
4. Kjør i batches, ikke alt på én gang

---

## [2026-03-19] Manglet full dokumentasjon før kjøring

**Problem:** Hadde ikke sim.pdf, sim2.pdf, sim3.pdf før scriptet ble kjørt.

**Regel:** Les ALL dokumentasjon → lag plan → vis plan → vent på godkjenning → implementer.

---

## [2026-03-19] Runde 1 – Observasjoner

**Hva ble gjort:**
- 45 coverage-queries (9 per seed, 3x3 grid) + 5 repeat-queries
- Bygde priors + observasjoner → sannsynlighetsfordelinger
- Submittet alle 5 seeds

**Observasjoner:**
- Empty: ~62-63%, Settlement: ~12-17%, Forest: ~17-21%
- Port: ~1-1.5%, Ruin: ~1-1.6%, Mountain: ~1-3%
- Settlements ekspanderer kraftig (30→200+ celler over 50 år)
- Stokastisk variasjon mellom kjøringer

**Svakheter:**
1. Bare 1 observasjon per celle for de fleste celler
2. Priors ikke informert av simuleringsmekanikk
3. Brukte ikke settlement-stats (population, food, wealth, defense)

---

## [2026-03-19] Forbedringer til neste runde

1. Multiple observasjoner > coverage bredde
2. Bruk settlement-stats for stabilitetsvurdering
3. Modellbasert prediksjon basert på sim-mekanikk
4. Iterativ forbedring med batches
5. Hent analysis-endepunkt etter runden lukker for å lære av feil
