# API-modul (`astar_island/api/`)

## Oversikt
HTTP-klient for Astar Island REST API. Håndterer autentisering, rate limiting og alle endepunkter.

## Endepunkter

### Gratis (read-only, ingen budsjett-kostnad)
| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| `get_rounds()` | GET /rounds | Alle runder |
| `get_active_round()` | GET /rounds | Finn aktiv runde |
| `get_round_details(id)` | GET /rounds/{id} | Initial states for alle seeds |
| `get_budget()` | GET /budget | Gjenstående queries |
| `get_my_rounds()` | GET /my-rounds | Scores og rank |
| `get_my_predictions(id)` | GET /my-predictions/{id} | Innsendte prediksjoner |
| `get_analysis(id, seed)` | GET /analysis/{id}/{seed} | Post-runde analyse (kun etter runden) |
| `get_leaderboard()` | GET /leaderboard | Offentlig leaderboard |

### Budsjett-kostende (KREVER GODKJENNING)
| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| `simulate(...)` | POST /simulate | 1 query fra budsjettet (50/runde) |
| `submit(...)` | POST /submit | Overskriver tidligere innsending |

## Rate limits
- `simulate`: max 5 req/s → 220ms delay mellom kall
- `submit`: max 2 req/s → 550ms delay mellom kall

## Regler
- SJEKK budsjett (get_budget) FØR du kjører simulate
- ALDRI kall simulate/submit uten brukerens godkjenning
- Ved 429 (rate limit): vent 5 sekunder, prøv igjen
