# charter-shield

A Monte Carlo pricing engine for fixed-price private jet charter contracts.

## The Problem

Charter operators quote fixed prices but bear variable costs. A Phenom 300 from Boston to Miami in January looks like an $11,400 flight at the hourly rate — but after repositioning, winter weather delays, and FBO event surcharges, the actual cost can exceed $29,000. Most operators price by gut feel. This engine prices by simulation.

## How It Works

The engine decomposes trip cost into a deterministic base plus four stochastic risk modules, runs 10,000 Monte Carlo scenarios, and quotes at the 90th percentile plus margin.

| Module | Models |
|--------|--------|
| **FuelRisk** | Jet-A spot price volatility (live EIA data), FBO markup variance, burn quantity variance |
| **WeatherRisk** | Delay probability × duration × hourly rate, with seasonal and geographic multipliers |
| **DeadheadRisk** | Empty repositioning legs from aircraft home base (hourly rate + fuel) |
| **FBOEventRisk** | Date-aware event surcharges — 12 windows including March Madness, Super Bowl, holidays |

**Pricing formula**: `quote = p90(simulated_costs) × (1 + margin)`

Adding a new risk factor is one new file implementing `sample(trip, rng) -> float`. Zero changes to the engine.

## Example

```
Base flight: 2.6 hrs at $3,200/hr block rate = $11,402.
Fuel variance adds ~$6 on average.
Weather delays adds ~$698 on average.
FBO/ground handling adds ~$923 on average.
Deadhead repositioning adds ~$8,042 on average.
90th-percentile total cost: $26,174.
Final quote (p90 + 12% margin): $29,315.
```

## Visualizations

Six built-in charts for executive presentations — waterfall breakdown, cost distribution, fuel sensitivity, fleet comparison, seasonal calendar with event annotations, and plain-English narrative.

![Risk Waterfall](data/results/risk_waterfall.png)

## Architecture

```
skyprice/
├── core.py           # Aircraft, Trip, PricingResult
├── engine.py         # base_cost(), simulate(), validation
├── data.py           # Airport DB, config, live EIA fuel prices
├── viz.py            # Charts + narrate()
├── backtest.py       # Historical coverage analysis
└── risks/            # Pluggable risk modules
    ├── fuel.py, weather.py, fbo.py, deadhead.py
```

## Quick Start

pip install -e .
python -m skyprice --origin KBOS --dest KMIA --aircraft "Phenom 300" --date 2025-01-15

## Calibration

`data/historical_trips.csv` contains 198 synthetic trips where actuals are drawn from the simulated distribution with noise. The backtest measures internal consistency, not real-world accuracy. Replace with actual completed trip data and re-run `backtest.py` to calibrate against reality.

## CI

Pytest + 80% coverage gate on core engine. Runs on every push to `main`.

## License

MIT
