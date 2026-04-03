"""
Seed Database — Generate multi-city grid geometry bootstrap and seed plans. Run once.
"""

import os
import sys
# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

GRID_DEG = 0.009  # ~1km in degrees

CITIES = {
    "Bengaluru": {"prefix": "BLR", "lat_start": 12.89, "lng_start": 77.54, "rows": 15, "cols": 15},
    "Mumbai": {"prefix": "MUM", "lat_start": 18.92, "lng_start": 72.82, "rows": 8, "cols": 8},
    "Delhi NCR": {"prefix": "DEL", "lat_start": 28.50, "lng_start": 77.05, "rows": 8, "cols": 8},
    "Chennai": {"prefix": "CHE", "lat_start": 12.95, "lng_start": 80.17, "rows": 8, "cols": 8},
    "Hyderabad": {"prefix": "HYD", "lat_start": 17.31, "lng_start": 78.39, "rows": 8, "cols": 8},
}

def generate_microgrids() -> list:
    grids = []

    for city, meta in CITIES.items():
        for i in range(meta["rows"]):
            for j in range(meta["cols"]):
                lat = meta["lat_start"] + i * GRID_DEG
                lng = meta["lng_start"] + j * GRID_DEG
                clat = lat + GRID_DEG / 2
                clng = lng + GRID_DEG / 2

                grids.append(
                    {
                        "id": f"{meta['prefix']}_{i:02d}_{j:02d}",
                        "city": city,
                        "center_lat": round(clat, 6),
                        "center_lng": round(clng, 6),
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
    """Generate and insert seeded multi-city microgrids."""
    grids = generate_microgrids()
    # Insert in batches
    batch_size = 50
    for i in range(0, len(grids), batch_size):
        batch = grids[i : i + batch_size]
        db.table("microgrids").upsert(batch).execute()
    print(f"  ✅ {len(grids)} microgrids seeded")


if __name__ == "__main__":
    if not SUPABASE_URL or SUPABASE_URL == "https://xxxx.supabase.co":
        print("❌ Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env first!")
        sys.exit(1)

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("🌱 Seeding Incometrix AI database...")
    seed_plans(db)
    seed_microgrids(db)
    print(
        "  ℹ️  Run backend/scripts/populate_microgrid_polygons.sql in Supabase SQL Editor "
        "to populate grid_polygon and recreate find_grid_by_point."
    )
    print("\n✅ Database seeding complete!")
