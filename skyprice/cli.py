import sys
from datetime import date
from skyprice.core import Aircraft, Trip
from skyprice.risks.fuel import FuelRisk
from skyprice.risks.weather import WeatherRisk
from skyprice.risks.fbo import FBOEventRisk
from skyprice.risks.deadhead import DeadheadRisk
from skyprice.engine import simulate

AIRCRAFT = dict(
    heavy=Aircraft("Gulfstream G-IV", 8500, 4370, 24000, 280),
    mid=Aircraft("Citation XLS+", 4200, 931, 12500, 190),
    light=Aircraft("Phenom 300", 3200, 581, 8500, 150))

def main():
    if len(sys.argv) < 4:
        print("Usage: python -m skyprice ORIGIN DEST DATE [--aircraft heavy|mid|light] [--pax N] [--cargo LBS]")
        sys.exit(1)
    origin, dest, dt = sys.argv[1], sys.argv[2], date.fromisoformat(sys.argv[3])
    args = {sys.argv[i].lstrip("-"): sys.argv[i+1] for i in range(4, len(sys.argv)-1, 2)}
    ac = AIRCRAFT[args.get("aircraft", "heavy")]
    pax, cargo = int(args.get("pax", 45)), float(args.get("cargo", 13000))
    from skyprice.core import haversine_nm
    dist = float(args.get("distance", 0)) or 1095.0
    trip = Trip(origin, dest, dt, ac, pax, cargo, dist)
    result = simulate(trip, [FuelRisk(), WeatherRisk(), FBOEventRisk(), DeadheadRisk()])
    print(f"\n{'='*50}")
    print(f"  CHARTER PRICE QUOTE: {origin} → {dest}")
    print(f"  {ac.name} | {dt} | {pax} pax")
    print(f"{'='*50}")
    print(f"  Base Cost:        ${result.base_cost:>12,.0f}")
    for k, v in result.risk_premiums.items(): print(f"  {k+':':20s}${v:>12,.0f}")
    print(f"{'─'*50}")
    for k, v in result.percentiles.items(): print(f"  {k}:                ${v:>12,.0f}")
    print(f"{'='*50}")
    print(f"  RECOMMENDED QUOTE: ${result.total:>12,.0f}")
    print(f"  (p90 + 12% margin)")
    print(f"{'='*50}\n")

if __name__ == "__main__": main()
