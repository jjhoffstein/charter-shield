import numpy as np
from datetime import date
from skyprice.core import Aircraft, Trip
from skyprice.risks.fuel import FuelRisk
from skyprice.risks.weather import WeatherRisk
from skyprice.risks.deadhead import DeadheadRisk
from skyprice.engine import simulate, base_cost
from skyprice.data import distance_nm

def _phenom(home="KBOS"): return Aircraft("Phenom 300", 3200, 581, 8500, 150, 420, home, max_pax=6)
def _trip(orig="KBOS", dest="KMIA", ac=None): return Trip(orig, dest, date(2025,1,15), ac or _phenom(), 2, 100, distance_nm(orig, dest))

def test_cruise_ktas_used_in_base_cost():
    fast = Aircraft("Phenom 300", 3200, 581, 8500, 150, 500, "KBOS", max_pax=6)
    slow = Aircraft("Phenom 300", 3200, 581, 8500, 150, 300, "KBOS", max_pax=6)
    t_fast = Trip("KBOS", "KMIA", date(2025,1,15), fast, 2, 100, 1095.0)
    t_slow = Trip("KBOS", "KMIA", date(2025,1,15), slow, 2, 100, 1095.0)
    assert base_cost(t_fast) < base_cost(t_slow)

def test_deadhead_uses_home_base():
    rng = np.random.default_rng(0)
    near = DeadheadRisk(sell_prob=0.0)
    t_near = _trip(ac=_phenom(home="KBOS"))
    t_far  = _trip(ac=_phenom(home="KLAX"))
    assert near.sample(t_far, rng) > near.sample(t_near, np.random.default_rng(0))

def test_fuel_risk_delta_centered_on_zero():
    rng = np.random.default_rng(42)
    f = FuelRisk(base_price=6.50, volatility=0.01, flowage_range=(0.20,0.20), into_plane_range=(1.375,1.375))
    samples = [f.sample(_trip(), rng) for _ in range(5000)]
    assert abs(np.mean(samples)) < 50

def test_weather_seasonal_multiplier_winter():
    zones = {"KBOS": "winter_heavy", "KMIA": "mild"}
    mults = {"winter_heavy": [2.5,2.5,1.5,1.5,0.8,0.8,0.7,0.7,0.8,0.8,2.0,2.0], "mild": [0.8]*12}
    w = WeatherRisk(delay_prob=0.20, mean_delay_hrs=1.0, delay_std=0.1, seasonal_multipliers=mults, airport_zones=zones)
    t_jan = _trip()
    t_jul = Trip(t_jan.origin, t_jan.destination, date(2025,7,15), t_jan.aircraft, t_jan.pax_count, t_jan.cargo_weight_lbs, t_jan.distance_nm)
    assert w._effective_delay_prob(t_jan) > w._effective_delay_prob(t_jul)

def test_risk_distributions_populated():
    r = simulate(_trip(), [FuelRisk(), WeatherRisk(), DeadheadRisk()], n=1000)
    assert set(r.risk_distributions.keys()) == {"FuelRisk", "WeatherRisk", "DeadheadRisk"}
    assert all(k in r.risk_distributions["WeatherRisk"] for k in ["mean","p10","p90"])

def test_risk_distributions_ordered():
    r = simulate(_trip(), [FuelRisk(), WeatherRisk(), DeadheadRisk()], n=1000)
    for v in r.risk_distributions.values(): assert v["p10"] <= v["mean"] or v["p10"] <= v["p90"]