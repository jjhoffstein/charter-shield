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
    return [
        FuelRisk(base_price, fc["volatility_pct"], tuple(fc["flowage_fee_range"]), tuple(fc["into_plane_fee_range"])),
        WeatherRisk(wc["delay_prob"], wc["mean_delay_hrs"], wc["delay_std"],
                    seasonal_multipliers=wc.get("seasonal_multipliers"), airport_zones=airport_zones()),
        FBOEventRisk(ec["event_prob"]),
        DeadheadRisk(dc["sell_probability_default"])]

def fetch_jeta_spot(api_key, fallback=2.50):
    "Fetch latest weekly jet-A spot price from EIA; returns fallback on failure"
    import httpx
    try:
        r = httpx.get('https://api.eia.gov/v2/petroleum/pri/spt/data/',
            params={'api_key': api_key, 'frequency': 'weekly', 'data[]': 'value',
                    'facets[product][]': 'EPJK', 'sort[0][column]': 'period',
                    'sort[0][direction]': 'desc', 'length': 1}, timeout=10.0)
        return float(r.json()['response']['data'][0]['value'])
    except Exception: return fallback
