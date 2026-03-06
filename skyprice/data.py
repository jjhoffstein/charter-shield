import tomllib, pandas as pd
from skyprice.core import haversine_nm

_airports = None

def load_airports(path="data/airports.csv"):
    "Load airport database and index by ICAO code"
    global _airports
    if _airports is None: _airports = pd.read_csv(path).set_index("icao")
    return _airports

def get_airport(icao):
    "Look up airport by ICAO code"
    db = load_airports()
    assert icao in db.index, f"Unknown airport: {icao}. Available: {list(db.index)}"
    return db.loc[icao]

def distance_nm(origin, dest):
    "Compute great-circle distance between two ICAO codes"
    a, b = get_airport(origin), get_airport(dest)
    return haversine_nm(a.lat, a.lon, b.lat, b.lon)

def load_config(path="config.toml"):
    "Load configuration from TOML file"
    with open(path, "rb") as f: return tomllib.load(f)

def build_risk_modules(cfg=None):
    "Build risk modules from config"
    if cfg is None: cfg = load_config()
    from skyprice.risks.fuel import FuelRisk
    from skyprice.risks.weather import WeatherRisk
    from skyprice.risks.fbo import FBOEventRisk
    from skyprice.risks.deadhead import DeadheadRisk
    fc = cfg["fuel"]
    return [
        FuelRisk(fc["base_price_per_gallon"], fc["volatility_pct"], tuple(fc["flowage_fee_range"]), tuple(fc["into_plane_fee_range"])),
        WeatherRisk(delay_prob=0.15, mean_delay_hrs=1.0, delay_std=0.8),
        FBOEventRisk(event_prob=0.20),
        DeadheadRisk(sell_prob=cfg["deadhead"]["sell_probability_default"])]
