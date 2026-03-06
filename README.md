# charter-shield

A Monte Carlo pricing engine for fixed-price charter aviation contracts.

## The Problem

Charter quotes are point estimates. Actual costs are distributions. A fixed-price contract that doesn't account for fuel volatility, weather delays, repositioning costs, and FBO surcharges will lose money systematically.

## How It Works

The engine decomposes trip cost into a deterministic base and four stochastic risk modules:

| Module | Models |
|--------|--------|
| `FuelRisk` | Jet-A spot price volatility (live EIA data) + FBO markup variance |
| `WeatherRisk` | Delay probability × duration × hourly rate, with seasonal/geographic multipliers |
| `DeadheadRisk` | Empty repositioning legs from aircraft home base |
| `FBOEventRisk` | Special event surcharges (Super Bowl, Daytona, etc.) |

Quote = p90 of simulated total cost × (1 + margin).

## Quick Start

pip install -e .

uvicorn skyprice.api:app --reload

curl -X POST http://localhost:8000/price \
  -H "Content-Type: application/json" \
  -d '{"origin":"KBOS","destination":"KMIA","date":"2025-06-15","aircraft":"Phenom 300","pax":4,"cargo_lbs":200}'
```

## Example Response

```json
{
  "origin": "KBOS",
  "destination": "KMIA",
  "aircraft": "Phenom 300",
  "distance_nm": 1255.1,
  "base_cost": 11500.12,
  "quote": 31250.00,
  "percentiles": {"p50": 18800, "p75": 22400, "p90": 27900, "p95": 32700, "p99": 41800},
  "risk_breakdown": {
    "FuelRisk":     {"mean": "$86",   "range": "$-650–$920"},
    "WeatherRisk":  {"mean": "$2,839","range": "$0–$8,240"},
    "DeadheadRisk": {"mean": "$4,400","range": "$0–$7,754"},
    "FBOEventRisk": {"mean": "$971",  "range": "$0–$2,874"}
  }
}
```

## Architecture

```
skyprice/
├── core.py       # Aircraft, Trip, PricingResult dataclasses
├── engine.py     # base_cost(), simulate(), payload/range validation
├── data.py       # Airport DB, distances, config, live EIA fuel prices
├── api.py        # FastAPI /price endpoint
├── backtest.py   # Historical coverage analysis
├── viz.py        # Distribution and waterfall charts
└── risks/        # Pluggable risk modules (fuel, weather, deadhead, fbo)
```

## A Note on Calibration Data

The `data/historical_trips.csv` file contains 200 synthetic trips generated from the model itself with lognormal noise. This means the backtest measures internal consistency, not real-world accuracy. The model is designed to improve as actual completed trip data is ingested — replace or augment the CSV with real actuals and re-run `backtest.py` to recalibrate.

## Configuration

All parameters are in `config.toml`. Key levers:

- `[fuel] spot_price_fallback` — fallback jet-A spot price if EIA API is unavailable
- `[fuel] fbo_markup_per_gallon` — average FBO retail markup over spot
- `[pricing] target_margin` — margin applied to p90 to produce the quote
- `[weather.seasonal_multipliers]` — per-zone monthly delay multipliers
