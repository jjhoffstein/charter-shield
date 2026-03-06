from skyprice.core import Aircraft, Trip, PricingResult, haversine_nm
from datetime import date

def test_haversine_bos_mia():
    d = haversine_nm(42.3656, -71.0096, 25.7959, -80.2870)
    assert 1090 < d < 1100

def test_haversine_zero():
    assert haversine_nm(0, 0, 0, 0) == 0.0

def test_aircraft():
    ac = Aircraft("Test", 8500, 4370, 24000, 280, 480, "KBOS", max_pax=12)
    assert ac.hourly_rate == 8500

def test_trip():
    ac = Aircraft("Gulfstream G-IV", 8500, 4370, 24000, 280, 480, "KBOS", max_pax=12)
    t = Trip("KBOS", "KMIA", date(2026, 1, 1), ac, 8, 800, 1095.0)
    assert t.distance_nm == 1095.0
    assert t.pax_count == 8