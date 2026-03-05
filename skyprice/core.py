from dataclasses import dataclass, field
from datetime import date
from math import radians, sin, cos, asin, sqrt

@dataclass
class Aircraft:
    "Charter aircraft with operating characteristics"
    name: str; hourly_rate: float; fuel_capacity_gal: float; max_payload_lbs: float; fuel_burn_gph: float

@dataclass
class FBO:
    "Fixed-base operator facility"
    icao: str; name: str; base_landing_fee: float; base_ramp_fee: float; fuel_flowage_fee: float; event_calendar: dict = field(default_factory=dict)

@dataclass
class Trip:
    "A single charter leg"
    origin: str; destination: str; date: date; aircraft: Aircraft; pax_count: int; cargo_weight_lbs: float; distance_nm: float = 0.0

@dataclass
class PricingResult:
    "Output of Monte Carlo pricing simulation"
    base_cost: float; risk_premiums: dict; total: float; percentiles: dict; distribution: list

def haversine_nm(lat1, lon1, lat2, lon2):
    "Great-circle distance in nautical miles between two lat/lon points"
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * 3440.065 * asin(sqrt(a))
