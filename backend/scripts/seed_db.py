"""
Seed Database — Generate 225 microgrids (15×15) over Bengaluru
and insert seed plans. Run once.
"""

import os
import sys
import numpy as np

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

GRID_DEG = 0.009  # ~1km in degrees
LAT_START, LNG_START = 12.89, 77.54

# Known flood-prone areas in Bengaluru
FLOOD_PRONE = [
    (12.920, 12.945, 77.610, 77.640),  # Koramangala
    (12.905, 12.925, 77.600, 77.625),  # BTM Layout
    (12.930, 12.950, 77.595, 77.615),  # Ejipura
]


def is_flood_prone(lat: float, lng: float) -> bool:
    for lat_min, lat_max, lng_min, lng_max in FLOOD_PRONE:
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return True
    return False


def generate_microgrids() -> list:
    np.random.seed(42)
    grids = []

    for i in range(15):
        for j in range(15):
            lat = LAT_START + i * GRID_DEG
            lng = LNG_START + j * GRID_DEG
            clat = lat + GRID_DEG / 2
            clng = lng + GRID_DEG / 2

            flood = (
                0.80
                if is_flood_prone(clat, clng)
                else round(np.random.uniform(0.10, 0.50), 2)
            )
            heat = round(np.random.uniform(0.30, 0.75), 2)
            aqi = round(np.random.uniform(80, 220), 1)
            traffic = round(np.random.uniform(0.30, 0.80), 2)
            social = round(np.random.uniform(0.10, 0.40), 2)
            composite = round(
                flood * 0.35
                + heat * 0.20
                + (aqi / 400) * 0.20
                + traffic * 0.15
                + social * 0.10,
                3,
            )

            grids.append(
                {
                    "id": f"BLR_{i:02d}_{j:02d}",
                    "city": "Bengaluru",
                    "center_lat": round(clat, 6),
                    "center_lng": round(clng, 6),
                    "flood_risk": flood,
                    "heat_index": heat,
                    "aqi_avg": aqi,
                    "traffic_risk": traffic,
                    "social_risk": social,
                    "composite_risk": composite,
                }
            )

    return grids


def seed_plans(db):
    """Upsert the 3 insurance plans."""
    plans = [
        {
            "id": "basic",
            "name": "Incometrix Basic",
            "weekly_premium_base": 49,
            "max_weekly_payout": 1500,
            "coverage_pct": 0.60,
            "description": "New workers, low-risk zones",
            "features": '["60% income coverage","₹1,500 max/week","3 trigger types"]',
        },
        {
            "id": "plus",
            "name": "Incometrix Plus",
            "weekly_premium_base": 79,
            "max_weekly_payout": 2500,
            "coverage_pct": 0.70,
            "description": "Regular workers, medium-risk zones",
            "features": '["70% income coverage","₹2,500 max/week","All 7 trigger types","Priority support"]',
        },
        {
            "id": "pro",
            "name": "Incometrix Pro",
            "weekly_premium_base": 129,
            "max_weekly_payout": 4000,
            "coverage_pct": 0.80,
            "description": "Full-time workers, high-risk zones",
            "features": '["80% income coverage","₹4,000 max/week","All triggers + cyclone","Fastest payouts","ISS fast-track"]',
        },
    ]
    db.table("plans").upsert(plans).execute()
    print(f"  ✅ {len(plans)} plans upserted")


def seed_microgrids(db):
    """Generate and insert 225 microgrids."""
    grids = generate_microgrids()
    # Insert in batches
    batch_size = 50
    for i in range(0, len(grids), batch_size):
        batch = grids[i : i + batch_size]
        db.table("microgrids").upsert(batch).execute()
    print(f"  ✅ {len(grids)} microgrids seeded")


def create_postgis_function(db):
    """Create PostGIS lookup function."""
    sql = """
    CREATE OR REPLACE FUNCTION find_grid_by_point(p_lat FLOAT, p_lng FLOAT)
    RETURNS TABLE(
        id VARCHAR, city VARCHAR, center_lat FLOAT, center_lng FLOAT,
        flood_risk FLOAT, heat_index FLOAT, aqi_avg FLOAT,
        traffic_risk FLOAT, social_risk FLOAT, composite_risk FLOAT
    ) AS $$
    SELECT id, city, center_lat, center_lng,
           flood_risk, heat_index, aqi_avg,
           traffic_risk, social_risk, composite_risk
    FROM microgrids
    WHERE ST_Contains(
        grid_polygon,
        ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)
    )
    LIMIT 1;
    $$ LANGUAGE sql;
    """
    try:
        db.rpc("exec_sql", {"query": sql}).execute()
        print("  ✅ PostGIS function created")
    except Exception as e:
        print(f"  ⚠️  PostGIS function creation skipped (may already exist or PostGIS not enabled): {e}")


if __name__ == "__main__":
    if not SUPABASE_URL or SUPABASE_URL == "https://xxxx.supabase.co":
        print("❌ Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env first!")
        sys.exit(1)

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("🌱 Seeding Incometrix AI database...")
    seed_plans(db)
    seed_microgrids(db)
    create_postgis_function(db)
    print("\n✅ Database seeding complete!")
