import numpy as np
from skyprice.core import PricingResult

def simulate(trip, risk_modules, n=10_000, seed=42, margin=0.12):
    "Run Monte Carlo simulation across all risk modules"
    rng = np.random.default_rng(seed)
    flight_hours = trip.distance_nm / 450
    base_cost = flight_hours * trip.aircraft.hourly_rate
    risk_samples = {type(m).__name__: np.array([m.sample(trip, rng) for _ in range(n)]) for m in risk_modules}
    total_risk = sum(risk_samples.values())
    total_cost = base_cost + total_risk
    pcts = [0.50, 0.75, 0.90, 0.95, 0.99]
    percentiles = {f"p{int(p*100)}": np.percentile(total_cost, p*100) for p in pcts}
    premiums = {k: float(np.mean(v)) for k, v in risk_samples.items()}
    return PricingResult(
        base_cost=base_cost, risk_premiums=premiums,
        total=float(percentiles["p90"] * (1 + margin)),
        percentiles={k: float(v) for k, v in percentiles.items()},
        distribution=total_cost.tolist())
