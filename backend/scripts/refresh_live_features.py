"""
Refresh live pricing features for all enabled city grids or active-worker grids.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.database import get_supabase
from app.services.pricing_feature_service import refresh_grid_features
from app.utils.microgrid_utils import get_city_by_name


async def main():
    db = get_supabase()
    grids = db.table("microgrids").select("*").limit(5000).execute().data or []
    refreshed = 0
    skipped = 0
    for grid in grids:
        city_meta = get_city_by_name(grid.get("city", ""))
        if not city_meta or not city_meta.get("pricing_enabled", True):
            skipped += 1
            continue
        try:
            await refresh_grid_features(grid, city_meta, force=True)
            refreshed += 1
        except Exception as e:
            skipped += 1
            print(f"⚠️  Skipped {grid['id']}: {e}")
    print(f"✅ Refreshed {refreshed} grids, skipped {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
