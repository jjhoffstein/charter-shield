# charter-shield

A Monte Carlo pricing engine for fixed-price private jet charter contracts.

## The Problem

Charter operators quote fixed prices but bear variable costs. A Phenom 300 from Boston to Miami in January looks like an $11,500 flight at the hourly rate — but after repositioning, winter weather delays, and FBO event surcharges, the actual cost can exceed $26,000. Most operators price by gut feel. This engine prices by simulation.

## How It Works

The engine decomposes trip cost into a deterministic base plus four stochastic risk modules, runs 10,000 Monte Carlo scenarios, and quotes at the 90th percentile plus margin.

| Module | Models |
|--------|--------|
| `FuelRisk` | Jet-A spot price volatility (live EIA data) + FBO markup variance |
| `WeatherRisk` | Delay probability × duration × hourly rate, with seasonal and geographic multipliers |
| `DeadheadRisk` | Empty repositioning legs from aircraft home base |
| `FBOEventRisk` | Date-aware special event surcharges (March Madness, Super Bowl, Daytona, holidays) |

**Pricing formula**: `quote = p90(simulated_costs) × (1 + margin)`

## Example Output

```
Base flight: 2.6 hrs at $3,200/hr block rate = $11,402.
Fuel variance adds ~$87 on average.
Weather delays adds ~$759 on average.
FBO/ground handling adds ~$1,024 on average.
Deadhead repositioning adds ~$5,890 on average.
90th-percentile total cost: $23,684.
Final quote (p90 + 12% margin): $26,526.
```

## Visualizations

The engine includes five built-in charts for executive presentations:

- **`plot_waterfall()`** — Risk-adjusted pricing waterfall with p10–p90 error bars per module
- **`plot_distribution()`** — Full cost distribution with percentile markers
- **`plot_fuel_sensitivity()`** — Quote response to jet-A price at $2.50 / $3.50 / $4.50 per gallon
- **`plot_fleet_comparison()`** — Side-by-side G-IV vs Citation XLS+ vs Phenom 300 economics
- **`plot_seasonal_calendar()`** — Stacked monthly breakdown showing weather and FBO event risk by month, with event annotations (March Madness, Super Bowl, etc.)
- **`narrate()`** — Plain-English quote summary for non-technical audiences

## Architecture

```
skyprice/
├── core.py         # Aircraft, Trip, PricingResult
├── engine.py       # base_cost(), simulate(), payload/range validation
├── data.py         # Airport DB, distances, config, live EIA fuel prices
├── viz.py          # All charts + narrate()
├── backtest.py     # Historical coverage analysis
├── api.py          # FastAPI /price endpoint
├── cli.py          # CLI entry point
└── risks/
    ├── base.py     # RiskModule ABC
    ├── fuel.py     # Jet-A price volatility
    ├── weather.py  # Seasonal/geographic delay model
    ├── fbo.py      # Date-aware event surcharges with EVENT_WINDOWS calendar
    └── deadhead.py # Empty leg repositioning cost
```

## Adding a New Risk Module

Adding a new risk factor (e.g. international overflight fees) requires one new file implementing `sample(trip, rng) -> float` and `describe() -> dict`. Zero changes to the engine.

## Fleet

| Aircraft | Hourly Rate | Fuel Burn | Cruise | Range | Max Pax | Home Base |
|----------|-------------|-----------|--------|-------|---------|-----------|
| Gulfstream G-IV | $8,500/hr | 280 gph | 480 ktas | 4,370 nm | 12 | KMIA |
| Citation XLS+ | $4,200/hr | 190 gph | 430 ktas | 2,150 nm | 8 | KORD |
| Phenom 300 | $3,200/hr | 150 gph | 420 ktas | 1,850 nm | 6 | KBOS |

## Date-Aware FBO Event Risk

The `FBOEventRisk` module scales event probability based on known high-traffic windows:

| Window | Event | Probability |
|--------|-------|-------------|
| Jan 1–2 | New Year's Day | 1.00 |
| Jan 31–Feb 3 | Super Bowl | 0.85 |
| Feb 15–23 | Daytona 500 | 0.70 |
| Mar 13–Apr 7 | March Madness | 0.90 |
| Nov 27–30 | Thanksgiving | 0.60 |
| Dec 20–31 | Holiday Season | 0.65 |

Baseline event probability outside these windows: 0.25.

## Configuration

All parameters live in `config.toml`:

- `[fuel] spot_price_fallback` — fallback jet-A spot price if EIA API is unavailable
- `[fuel] fbo_markup_per_gallon` — average FBO retail markup over spot
- `[pricing] target_margin` — margin applied to p90 (default 12%)
- `[weather.seasonal_multipliers]` — per-zone monthly delay multipliers
- `[simulation] n_iterations` — Monte Carlo sample count (default 10,000)

## Quick Start

```bash
pip install -e .
python -m skyprice --origin KBOS --dest KMIA --aircraft "Phenom 300" --date 2025-01-15
```

Or via API:

```bash
uvicorn skyprice.api:app --reload
curl -X POST http://localhost:8000/price \
  -H "Content-Type: application/json" \
  -d '{"origin":"KBOS","destination":"KMIA","date":"2025-01-15","aircraft":"Phenom 300","pax":4,"cargo_lbs":200}'
```

## A Note on Calibration Data

`data/historical_trips.csv` contains 198 synthetic trips where actuals are drawn from the simulated distribution with added noise. The backtest measures internal consistency, not real-world accuracy. Replace or augment with actual completed trip data and re-run `backtest.py` to recalibrate against reality.

## CI

Pytest + 80% coverage gate on `skyprice/core.py`, `engine.py`, `data.py`, and `risks/`. Runs on every push to `main`.

## License

MIT