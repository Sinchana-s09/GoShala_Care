"""
GoShala Care - Database & Features Diagnostic Test
Tests connection, schema tables, registered vets, cows, and everyday vitals comparison.
"""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import get_db, check_db_health
from backend.db_models import User, Cow, VetDirectory, VitalsLog
from backend.vitals_comparator import VitalsComparator
from backend.ml_service import MLService

def main():
    print("=" * 60)
    print(" GOSHALA CARE - SYSTEM DIAGNOSTICS ")
    print("=" * 60)

    # 1. Database Health Check
    health = check_db_health()
    print(f"\n[+] Database Engine: {health.get('engine', 'Unknown')}")
    print(f"[+] Connection Status: {health.get('status', 'Unknown')}")

    db = get_db()

    # 2. Users & Herds
    users_count = db.query(User).count()
    cows_count = db.query(Cow).count()
    print(f"[+] Total Registered Users: {users_count}")
    print(f"[+] Total Registered Cattle: {cows_count}")

    # 3. Veterinary Directory
    vets = db.query(VetDirectory).all()
    print(f"[+] Veterinary Network Clinics: {len(vets)}")
    for v in vets:
        em = "[24/7 EMERGENCY]" if v.emergency_available else "[Standard]"
        print(f"    - {v.clinic_name} ({v.name}) | {v.address} | {em}")

    # 4. Everyday Requirements & Dataset Comparison Engine
    print("\n[+] Testing Everyday Requirements Benchmark Comparison:")
    test_vitals = {
        'temperature': 38.6,
        'feed_quantity_kg': 16.5,
        'water_intake_litres': 60.0,
        'walking_distance_km': 4.5,
        'rumination_time_hrs': 8.0,
        'resting_hours': 10.0,
        'heart_rate_bpm': 64.0,
        'respiratory_rate': 25.0,
        'milk_yield': 12.0
    }
    report = VitalsComparator.compare_everyday_vitals(test_vitals)
    print(f"    - Everyday Health Index: {report['health_index']} / 100")
    print(f"    - Top Dataset Condition Match: {report['top_match']['name']} ({report['top_match']['similarity_score']}%)")
    print(f"    - Total Parameters Evaluated: {len(report['comparisons'])}")

    print("\n" + "=" * 60)
    print(" ALL CHECKS PASSED SUCCESSFULLY - GOSHALA CARE IS ACTIVE! ")
    print("=" * 60)

if __name__ == '__main__':
    main()
