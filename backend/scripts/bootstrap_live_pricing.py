"""
Bootstrap live pricing registry for top 20 cities and canonical microgrids.
Run after live_pricing_schema.sql.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

GRID_STEP = 0.009

TOP_20_CITIES = [
    {"slug": "bengaluru", "name": "Bengaluru", "state": "Karnataka", "grid_prefix": "BLR", "center_lat": 12.9716, "center_lng": 77.5946, "lat_min": 12.80, "lat_max": 13.20, "lng_min": 77.40, "lng_max": 77.80, "grid_origin_lat": 12.89, "grid_origin_lng": 77.54, "grid_rows": 15, "grid_cols": 15},
    {"slug": "mumbai", "name": "Mumbai", "state": "Maharashtra", "grid_prefix": "MUM", "center_lat": 19.0760, "center_lng": 72.8777, "lat_min": 18.80, "lat_max": 19.40, "lng_min": 72.70, "lng_max": 73.10, "grid_origin_lat": 18.92, "grid_origin_lng": 72.82, "grid_rows": 8, "grid_cols": 8},
    {"slug": "delhi-ncr", "name": "Delhi NCR", "state": "Delhi", "grid_prefix": "DEL", "center_lat": 28.6139, "center_lng": 77.2090, "lat_min": 28.40, "lat_max": 28.90, "lng_min": 76.90, "lng_max": 77.50, "grid_origin_lat": 28.50, "grid_origin_lng": 77.05, "grid_rows": 8, "grid_cols": 8},
    {"slug": "chennai", "name": "Chennai", "state": "Tamil Nadu", "grid_prefix": "CHE", "center_lat": 13.0827, "center_lng": 80.2707, "lat_min": 12.70, "lat_max": 13.30, "lng_min": 80.00, "lng_max": 80.40, "grid_origin_lat": 12.95, "grid_origin_lng": 80.17, "grid_rows": 8, "grid_cols": 8},
    {"slug": "hyderabad", "name": "Hyderabad", "state": "Telangana", "grid_prefix": "HYD", "center_lat": 17.3850, "center_lng": 78.4867, "lat_min": 17.20, "lat_max": 17.70, "lng_min": 78.20, "lng_max": 78.70, "grid_origin_lat": 17.31, "grid_origin_lng": 78.39, "grid_rows": 8, "grid_cols": 8},
    {"slug": "pune", "name": "Pune", "state": "Maharashtra", "grid_prefix": "PUN", "center_lat": 18.5204, "center_lng": 73.8567, "lat_min": 18.35, "lat_max": 18.70, "lng_min": 73.70, "lng_max": 74.05, "grid_origin_lat": 18.41, "grid_origin_lng": 73.77, "grid_rows": 8, "grid_cols": 8},
    {"slug": "kolkata", "name": "Kolkata", "state": "West Bengal", "grid_prefix": "KOL", "center_lat": 22.5726, "center_lng": 88.3639, "lat_min": 22.45, "lat_max": 22.75, "lng_min": 88.20, "lng_max": 88.50, "grid_origin_lat": 22.48, "grid_origin_lng": 88.24, "grid_rows": 8, "grid_cols": 8},
    {"slug": "ahmedabad", "name": "Ahmedabad", "state": "Gujarat", "grid_prefix": "AHM", "center_lat": 23.0225, "center_lng": 72.5714, "lat_min": 22.90, "lat_max": 23.20, "lng_min": 72.45, "lng_max": 72.75, "grid_origin_lat": 22.95, "grid_origin_lng": 72.47, "grid_rows": 8, "grid_cols": 8},
    {"slug": "jaipur", "name": "Jaipur", "state": "Rajasthan", "grid_prefix": "JAI", "center_lat": 26.9124, "center_lng": 75.7873, "lat_min": 26.75, "lat_max": 27.05, "lng_min": 75.65, "lng_max": 75.95, "grid_origin_lat": 26.78, "grid_origin_lng": 75.67, "grid_rows": 8, "grid_cols": 8},
    {"slug": "lucknow", "name": "Lucknow", "state": "Uttar Pradesh", "grid_prefix": "LKO", "center_lat": 26.8467, "center_lng": 80.9462, "lat_min": 26.70, "lat_max": 27.00, "lng_min": 80.80, "lng_max": 81.08, "grid_origin_lat": 26.73, "grid_origin_lng": 80.82, "grid_rows": 8, "grid_cols": 8},
    {"slug": "surat", "name": "Surat", "state": "Gujarat", "grid_prefix": "SUR", "center_lat": 21.1702, "center_lng": 72.8311, "lat_min": 21.05, "lat_max": 21.30, "lng_min": 72.70, "lng_max": 72.98, "grid_origin_lat": 21.08, "grid_origin_lng": 72.72, "grid_rows": 8, "grid_cols": 8},
    {"slug": "kochi", "name": "Kochi", "state": "Kerala", "grid_prefix": "KOC", "center_lat": 9.9312, "center_lng": 76.2673, "lat_min": 9.82, "lat_max": 10.05, "lng_min": 76.15, "lng_max": 76.40, "grid_origin_lat": 9.84, "grid_origin_lng": 76.17, "grid_rows": 8, "grid_cols": 8},
    {"slug": "indore", "name": "Indore", "state": "Madhya Pradesh", "grid_prefix": "IND", "center_lat": 22.7196, "center_lng": 75.8577, "lat_min": 22.60, "lat_max": 22.85, "lng_min": 75.72, "lng_max": 76.00, "grid_origin_lat": 22.62, "grid_origin_lng": 75.74, "grid_rows": 8, "grid_cols": 8},
    {"slug": "chandigarh", "name": "Chandigarh", "state": "Chandigarh", "grid_prefix": "CHD", "center_lat": 30.7333, "center_lng": 76.7794, "lat_min": 30.65, "lat_max": 30.82, "lng_min": 76.68, "lng_max": 76.88, "grid_origin_lat": 30.66, "grid_origin_lng": 76.69, "grid_rows": 8, "grid_cols": 8},
    {"slug": "bhubaneswar", "name": "Bhubaneswar", "state": "Odisha", "grid_prefix": "BHU", "center_lat": 20.2961, "center_lng": 85.8245, "lat_min": 20.20, "lat_max": 20.40, "lng_min": 85.72, "lng_max": 85.95, "grid_origin_lat": 20.21, "grid_origin_lng": 85.73, "grid_rows": 8, "grid_cols": 8},
    {"slug": "patna", "name": "Patna", "state": "Bihar", "grid_prefix": "PAT", "center_lat": 25.5941, "center_lng": 85.1376, "lat_min": 25.48, "lat_max": 25.72, "lng_min": 85.00, "lng_max": 85.26, "grid_origin_lat": 25.50, "grid_origin_lng": 85.02, "grid_rows": 8, "grid_cols": 8},
    {"slug": "coimbatore", "name": "Coimbatore", "state": "Tamil Nadu", "grid_prefix": "CBE", "center_lat": 11.0168, "center_lng": 76.9558, "lat_min": 10.90, "lat_max": 11.15, "lng_min": 76.82, "lng_max": 77.08, "grid_origin_lat": 10.92, "grid_origin_lng": 76.84, "grid_rows": 8, "grid_cols": 8},
    {"slug": "nagpur", "name": "Nagpur", "state": "Maharashtra", "grid_prefix": "NAG", "center_lat": 21.1458, "center_lng": 79.0882, "lat_min": 21.03, "lat_max": 21.28, "lng_min": 78.96, "lng_max": 79.22, "grid_origin_lat": 21.05, "grid_origin_lng": 78.98, "grid_rows": 8, "grid_cols": 8},
    {"slug": "visakhapatnam", "name": "Visakhapatnam", "state": "Andhra Pradesh", "grid_prefix": "VSK", "center_lat": 17.6868, "center_lng": 83.2185, "lat_min": 17.56, "lat_max": 17.82, "lng_min": 83.08, "lng_max": 83.36, "grid_origin_lat": 17.58, "grid_origin_lng": 83.10, "grid_rows": 8, "grid_cols": 8},
    {"slug": "bhopal", "name": "Bhopal", "state": "Madhya Pradesh", "grid_prefix": "BHO", "center_lat": 23.2599, "center_lng": 77.4126, "lat_min": 23.15, "lat_max": 23.36, "lng_min": 77.28, "lng_max": 77.55, "grid_origin_lat": 23.16, "grid_origin_lng": 77.29, "grid_rows": 8, "grid_cols": 8},
]

DEFAULT_PRICING_CONFIG = {
    "version": "live_v1",
    "base_multiplier": 0.86,
    "zone_multiplier_scale": 0.74,
    "minimum_premium": 19.0,
    "feature_bounds": {
        "heat_index_min": 24.0,
        "heat_index_max": 60.0,
        "aqi_max": 400.0,
        "rainfall_daily_max": 120.0,
        "rainfall_short_max": 60.0,
    },
    "feature_weights": {
        "flood_risk": 0.30,
        "heat_index_norm": 0.16,
        "aqi_norm": 0.18,
        "traffic_risk": 0.14,
        "rainfall_7d_norm": 0.12,
        "seasonal_signal": 0.10,
    },
    "seasonal_factor": {
        "base": 0.92,
        "rainfall_weight": 0.24,
        "heat_weight": 0.16,
        "aqi_weight": 0.08,
        "max": 1.35,
    },
    "iss_discount": {"base": 0.70, "span": 0.30},
    "persona_factors": {"hustler": 1.08, "stabilizer": 0.97, "opportunist": 1.04},
    "persona_labels": {
        "hustler": "Hustler",
        "stabilizer": "Stabilizer",
        "opportunist": "Opportunist",
    },
    "zone_labels": {
        "bands": [
            {"max": 0.30, "label": "Low Risk"},
            {"max": 0.55, "label": "Medium Risk"},
            {"max": 0.80, "label": "High Risk"},
            {"max": 1.0, "label": "Severe Risk"},
        ]
    },
    "season_labels": {
        "calm_max": 0.22,
        "calm_label": "Stable Conditions",
    },
    "iss_labels": {
        "bands": [
            {"max": 35, "label": "Low"},
            {"max": 70, "label": "Medium"},
            {"max": 100, "label": "High"},
        ]
    },
    "history_window_rows": 72,
    "ml": {
        "enabled": True,
        "blend_weight": 0.65,
        "min_multiplier": 0.72,
        "max_multiplier": 1.65,
        "historical_flood_blend": 0.08,
    },
    "waterlogging_credit": {
        "safe_threshold": 0.18,
        "elevated_threshold": 0.55,
        "current_flood_guard": 0.30,
        "safe_credit": 2.0,
        "high_risk_surcharge": 3.0,
    },
    "coverage_hours": {
        "base_by_plan": {"basic": 32, "plus": 44, "pro": 56},
        "bonus_cap_by_plan": {"basic": 6, "plus": 10, "pro": 14},
        "risk_hour_thresholds": {"rain_3h": 4.0, "temp": 35.0},
        "max_predictive_hours": 24,
    },
    "freshness_minutes": {"weather": 20, "aqi": 20, "traffic": 15, "quote": 30},
    "traffic_profile": {
        "slots": [
            {"start": 0, "end": 7, "value": 0.22},
            {"start": 7, "end": 10, "value": 0.74},
            {"start": 10, "end": 16, "value": 0.46},
            {"start": 16, "end": 21, "value": 0.82},
            {"start": 21, "end": 24, "value": 0.38},
        ],
        "rain_weight": 0.22,
        "heat_weight": 0.08,
        "aqi_weight": 0.05,
        "max": 1.0,
    },
    "flood_formula": {
        "rain_6h_weight": 0.62,
        "rainfall_7d_weight": 0.38,
        "max": 1.0,
    },
}


def generate_microgrids():
    grids = []
    for city in TOP_20_CITIES:
        for i in range(city["grid_rows"]):
            for j in range(city["grid_cols"]):
                lat = city["grid_origin_lat"] + i * GRID_STEP
                lng = city["grid_origin_lng"] + j * GRID_STEP
                grids.append(
                    {
                        "id": f"{city['grid_prefix']}_{i:02d}_{j:02d}",
                        "city": city["name"],
                        "center_lat": round(lat + GRID_STEP / 2, 6),
                        "center_lng": round(lng + GRID_STEP / 2, 6),
                    }
                )
    return grids


if __name__ == "__main__":
    if not SUPABASE_URL or SUPABASE_URL == "https://xxxx.supabase.co":
        print("❌ Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env first!")
        sys.exit(1)

    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    cities = [{**city, "grid_step_deg": GRID_STEP, "pricing_enabled": True, "feature_status": "pending"} for city in TOP_20_CITIES]
    db.table("supported_cities").upsert(cities).execute()
    print(f"✅ Upserted {len(cities)} supported cities")

    grids = generate_microgrids()
    batch_size = 100
    for i in range(0, len(grids), batch_size):
        db.table("microgrids").upsert(grids[i : i + batch_size]).execute()
    print(f"✅ Upserted {len(grids)} grid geometries")

    db.table("pricing_config_versions").update({"is_active": False}).neq("version", "").execute()
    db.table("pricing_config_versions").upsert(
        {
            "version": DEFAULT_PRICING_CONFIG["version"],
            "is_active": True,
            "config": json.dumps(DEFAULT_PRICING_CONFIG),
        }
    ).execute()
    print("✅ Activated live pricing config")
    print("ℹ️ Run backend/scripts/populate_microgrid_polygons.sql after bootstrap.")
