import numpy as np
from datetime import date
from skyprice.core import Aircraft, Trip
from skyprice.risks.fuel import FuelRisk
from skyprice.risks.weather import WeatherRisk
from skyprice.risks.fbo import FBOEventRisk
from skyprice.risks.deadhead import DeadheadRisk
from skyprice.engine import simulate

def _make_trip():
    ac = Aircraft("Gulfstream G-IV", 8500, 4370, 24000, 280, 480, "KMIA", max_pax=12)
    return Trip("KBOS", "KMIA", date(2026, 11, 15), ac, 8, 800, 1095.0)

def test_simulate_deterministic():
    t = _make_trip()
    modules = [FuelRisk(), WeatherRisk(), FBOEventRisk(), DeadheadRisk()]
    r1 = simulate(t, modules, seed=42)
    r2 = simulate(t, modules, seed=42)
    assert r1.total == r2.total

def test_simulate_has_all_risk_keys():
    t = _make_trip()
    modules = [FuelRisk(), WeatherRisk(), FBOEventRisk(), DeadheadRisk()]
    r = simulate(t, modules)
    assert set(r.risk_premiums.keys()) == {"FuelRisk", "WeatherRisk", "FBOEventRisk", "DeadheadRisk"}

def test_simulate_total_exceeds_base():
    t = _make_trip()
    r = simulate(t, [FuelRisk(), WeatherRisk(), FBOEventRisk(), DeadheadRisk()])
    assert r.total > r.base_cost

def test_simulate_percentiles_ordered():
    t = _make_trip()
    r = simulate(t, [FuelRisk(), WeatherRisk(), FBOEventRisk(), DeadheadRisk()])
    assert r.percentiles["p50"] <= r.percentiles["p75"] <= r.percentiles["p90"] <= r.percentiles["p95"] <= r.percentiles["p99"]

def test_pax_validation():
    ac = Aircraft("Phenom 300", 3200, 581, 8500, 150, 420, "KBOS", max_pax=6)
    t = Trip("KBOS", "KMIA", date(2026, 1, 1), ac, 9, 200, 1095.0)
    try: simulate(t, [FuelRisk()]); assert False, "should have raised"
    except ValueError as e: assert "pax" in str(e)