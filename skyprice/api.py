from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from datetime import date
from skyprice.core import Aircraft, Trip
from skyprice.engine import simulate
from skyprice.data import build_risk_modules, distance_nm, load_config, get_airport
from skyprice.backtest import AC_LOOKUP
import os

app = FastAPI(title="charter-shield", description="Risk-adjusted charter pricing engine")
_modules = None

def get_modules():
    global _modules
    if _modules is None: _modules = build_risk_modules(eia_key=os.environ.get("EIA_API_KEY"))
    return _modules

class PriceRequest(BaseModel):
    origin: str
    destination: str
    date: date
    aircraft: str
    pax: int
    cargo_lbs: float = 0.0

    @field_validator("aircraft")
    @classmethod
    def valid_aircraft(cls, v):
        if v not in AC_LOOKUP: raise ValueError(f"Unknown aircraft. Choose from: {list(AC_LOOKUP.keys())}")
        return v

    @field_validator("origin", "destination")
    @classmethod
    def valid_airport(cls, v):
        get_airport(v)
        return v

class PriceResponse(BaseModel):
    origin: str; destination: str; aircraft: str; distance_nm: float
    base_cost: float; quote: float; percentiles: dict; risk_breakdown: dict

@app.post("/price", response_model=PriceResponse)
def price(req: PriceRequest):
    ac = AC_LOOKUP[req.aircraft]
    dist = distance_nm(req.origin, req.destination)
    t = Trip(req.origin, req.destination, req.date, ac, req.pax, req.cargo_lbs, dist)
    cfg = load_config()
    res = simulate(t, get_modules(), n=cfg["simulation"]["n_iterations"],
                   seed=cfg["simulation"]["seed"], margin=cfg["pricing"]["target_margin"])
    breakdown = {k: dict(mean=f"${v['mean']:,.0f}", range=f"${v['p10']:,.0f}–${v['p90']:,.0f}")
                 for k, v in res.risk_distributions.items()}
    return PriceResponse(origin=req.origin, destination=req.destination, aircraft=req.aircraft,
                         distance_nm=round(dist,1), base_cost=round(res.base_cost,2),
                         quote=round(res.total,2), percentiles=res.percentiles, risk_breakdown=breakdown)

@app.get("/aircraft")
def list_aircraft(): return list(AC_LOOKUP.keys())

@app.get("/airports")
def list_airports():
    from skyprice.data import load_airports
    return load_airports().reset_index()[["icao","region"]].to_dict(orient="records")
