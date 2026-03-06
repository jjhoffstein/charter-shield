import tomllib, pandas as pd, numpy as np
from datetime import date
from pathlib import Path
from skyprice.core import haversine_nm

_ROOT = Path(__file__).parent.parent
_airports_cache = {}

def load_airports(path=None):
    "Load airport database and index by ICAO code"
    p = Path(path) if path else _ROOT / "data/airports.csv"
    key = str(p.resolve())
    if key not in _airports_cache: _airports_cache[key] = pd.read_csv(p).set_index("icao")
    return _airports_cache[key]

def get_airport(icao):
    "Look up airport by ICAO code"
    db = load_airports()
    assert icao in db.index, f"Unknown airport: {icao}. Available: {list(db.index)}"
    return db.loc[icao]

def distance_nm(origin, dest):
    "Compute great-circle distance between two ICAO codes"
    a, b = get_airport(origin), get_airport(dest)
    return haversine_nm(a.lat, a.lon, b.lat, b.lon)

def load_config(path=None):
    "Load configuration from TOML file"
    p = Path(path) if path else _ROOT / "config.toml"
    with open(p, "rb") as f: return tomllib.load(f)

def airport_zones(airports_df=None):
    "Build ICAO -> weather_zone lookup dict"
    if airports_df is None: airports_df = load_airports()
    return airports_df["weather_zone"].to_dict()

def build_risk_modules(cfg=None, eia_key=None):
    "Build risk modules from config, optionally fetching live jet-A spot price"
    if cfg is None: cfg = load_config()
    from skyprice.risks.fuel import FuelRisk
    from skyprice.risks.weather import WeatherRisk
    from skyprice.risks.fbo import FBOEventRisk
    from skyprice.risks.deadhead import DeadheadRisk
    fc, wc, ec, dc = cfg["fuel"], cfg["weather"], cfg["fbo_events"], cfg["deadhead"]
    spot = fetch_jeta_spot(eia_key, fc["spot_price_fallback"]) if eia_key else fc["spot_price_fallback"]
    base_price = spot + fc["fbo_markup_per_gallon"]
    qpg = base_price + np.mean(fc["flowage_fee_range"]) + np.mean(fc["into_plane_fee_range"])
    fee_ranges = dict(
        mega=(ec["mega_fee_range"][0],     ec["mega_fee_range"][1],     ec["mega_prob"]),
        major=(ec["major_fee_range"][0],   ec["major_fee_range"][1],    ec["major_prob"]),
        local=(ec["local_fee_range"][0],   ec["local_fee_range"][1],    ec["local_prob"]),
        standard=(ec["standard_fee_range"][0], ec["standard_fee_range"][1], ec["standard_prob"]))
    return [
        FuelRisk(base_price, fc["volatility_pct"], tuple(fc["flowage_fee_range"]), tuple(fc["into_plane_fee_range"])),
        WeatherRisk(wc["delay_prob"], wc["mean_delay_hrs"], wc["delay_std"],
                    seasonal_multipliers=wc.get("seasonal_multipliers"), airport_zones=airport_zones(),
                    operator_cost_fraction=wc["operator_cost_fraction"]),
        FBOEventRisk(ec["event_prob"], fee_ranges),
        DeadheadRisk(dc["sell_probability_default"], qpg)]

def fetch_jeta_spot(api_key, fallback=2.50):
    "Fetch latest weekly jet-A spot price from EIA; returns fallback on failure"
    import httpx
    try:
        r = httpx.get("https://api.eia.gov/v2/petroleum/pri/spt/data/",
            params={"api_key": api_key, "frequency": "weekly", "data[]": "value",
                    "facets[product][]": "EPJK", "sort[0][column]": "period",
                    "sort[0][direction]": "desc", "length": 1}, timeout=10.0)
        return float(r.json()["response"]["data"][0]["value"])
    except Exception: return fallback

def generate_historical_trips(ac_lookup, modules, n=200, seed=42):
    "Generate synthetic historical trips with lognormal noise around p50 for backtesting"
    from skyprice.core import Trip
    from skyprice.engine import simulate
    rng = np.random.default_rng(seed)
    icaos = load_airports().index.tolist()
    rows, per_ac = [], n // len(ac_lookup)
    for name, ac in ac_lookup.items():
        pairs = [(o, d) for o in icaos for d in icaos if o != d and distance_nm(o, d) <= ac.max_range_nm()]
        for _ in range(per_ac):
            o, d = pairs[rng.integers(len(pairs))]
            dist = distance_nm(o, d)
            pax = int(rng.integers(1, ac.max_pax + 1))
            cargo = round(float(rng.uniform(0, 300)), 1)
            dt = date(2024, int(rng.integers(1, 13)), int(rng.integers(1, 28)))
            res = simulate(Trip(o, d, dt, ac, pax, cargo, dist), modules, n=1000, seed=int(rng.integers(1_000_000)))
            actual = float(rng.choice(res.distribution))
            rows.append(dict(origin=o, destination=d, date=dt, aircraft=name, pax=pax, cargo_lbs=cargo, distance_nm=dist, actual_cost=round(actual, 2)))
    return pd.DataFrame(rows)
