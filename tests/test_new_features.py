import numpy as np
from datetime import date
from skyprice.core import Aircraft, Trip
from skyprice.risks.fuel import FuelRisk
from skyprice.risks.weather import WeatherRisk
from skyprice.risks.deadhead import DeadheadRisk
from skyprice.engine import simulate, base_cost
from skyprice.data import distance_nm, generate_historical_trips

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
    f = FuelRisk(base_price=6.25, volatility=0.25, flowage_range=(0.10,0.30), into_plane_range=(1.25,1.50))
    samples = [f.sample(_trip(), rng) for _ in range(20000)]
    assert abs(np.mean(samples)) < 30, f"FuelRisk mean delta should be ~0, got {np.mean(samples):.1f}"

def test_fuel_burn_volatility_increases_spread():
    t = _trip()
    rng1, rng2 = np.random.default_rng(42), np.random.default_rng(42)
    calm = FuelRisk(base_price=6.25, volatility=0.25, burn_volatility=0.0)
    stormy = FuelRisk(base_price=6.25, volatility=0.25, burn_volatility=0.10,
                      airport_zones={"KBOS": "winter_heavy"}, seasonal_multipliers={"winter_heavy": [2.5]*12})
    s_calm = [calm.sample(t, rng1) for _ in range(10000)]
    s_stormy = [stormy.sample(t, rng2) for _ in range(10000)]
    assert np.std(s_stormy) > np.std(s_calm), "Burn volatility should increase spread"

def test_weather_seasonal_multiplier_winter():
    zones = {"KBOS": "winter_heavy", "KMIA": "mild"}
    mults = {"winter_heavy": [2.5,2.5,1.5,1.5,0.8,0.8,0.7,0.7,0.8,0.8,2.0,2.0], "mild": [0.8]*12}
    w = WeatherRisk(delay_prob=0.20, mean_delay_hrs=1.0, delay_std=0.1, seasonal_multipliers=mults, airport_zones=zones)
    t_jan = _trip()
    t_jul = Trip(t_jan.origin, t_jan.destination, date(2025,7,15), t_jan.aircraft, t_jan.pax_count, t_jan.cargo_weight_lbs, t_jan.distance_nm)
    assert w._effective_delay_prob(t_jan) > w._effective_delay_prob(t_jul)

def test_deadhead_includes_fuel():
    rng = np.random.default_rng(0)
    dh = DeadheadRisk(sell_prob=0.0, fuel_price_per_gal=7.825)
    t = _trip()
    cost = dh.sample(t, rng)
    repo_nm = distance_nm("KBOS", "KBOS") + distance_nm("KMIA", "KBOS")
    hourly_only = (repo_nm / t.aircraft.cruise_ktas) * t.aircraft.hourly_rate
    assert cost > hourly_only, "Deadhead cost should include fuel on top of hourly rate"

def test_fbo_event_prob_returns_max():
    from skyprice.risks.fbo import _event_prob
    assert _event_prob(date(2025, 12, 27), 0.25) == 0.70
    assert _event_prob(date(2025, 12, 25), 0.25) == 0.65
    assert _event_prob(date(2026, 1, 1), 0.25) == 1.00
    assert _event_prob(date(2025, 6, 10), 0.25) == 0.25

def test_risk_distributions_populated():
    r = simulate(_trip(), [FuelRisk(), WeatherRisk(), DeadheadRisk()], n=1000)
    assert set(r.risk_distributions.keys()) == {"FuelRisk", "WeatherRisk", "DeadheadRisk"}
    assert all(k in r.risk_distributions["WeatherRisk"] for k in ["mean","p10","p90"])

def test_risk_distributions_ordered():
    r = simulate(_trip(), [FuelRisk(), WeatherRisk(), DeadheadRisk()], n=1000)
    for v in r.risk_distributions.values(): assert v["p10"] <= v["mean"] <= v["p90"]

def test_generate_historical_trips():
    ac_lookup = {"Phenom 300": _phenom()}
    modules = [FuelRisk(), WeatherRisk(), DeadheadRisk()]
    df = generate_historical_trips(ac_lookup, modules, n=6)
    assert len(df) == 6
    assert list(df.columns) == ["origin","destination","date","aircraft","pax","cargo_lbs","distance_nm","actual_cost"]
    assert all(df.apply(lambda r: r.distance_nm <= ac_lookup[r.aircraft].max_range_nm(), axis=1))
