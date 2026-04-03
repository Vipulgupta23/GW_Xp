-- Incometrix AI — Populate microgrid polygons and recreate PostGIS lookup
-- Run this in Supabase SQL Editor after seeding microgrids.

CREATE EXTENSION IF NOT EXISTS postgis;

grid_coords AS (
  SELECT
    m.id,
    m.city,
    c.grid_origin_lat + split_part(m.id, '_', 2)::int * c.grid_step_deg AS cell_lat,
    c.grid_origin_lng + split_part(m.id, '_', 3)::int * c.grid_step_deg AS cell_lng,
    c.grid_step_deg
  FROM microgrids m
  JOIN supported_cities c ON c.name = m.city
)
UPDATE microgrids AS m
SET grid_polygon = ST_MakeEnvelope(
  g.cell_lng,
  g.cell_lat,
  g.cell_lng + g.grid_step_deg,
  g.cell_lat + g.grid_step_deg,
  4326
)
FROM grid_coords g
WHERE m.id = g.id;

CREATE INDEX IF NOT EXISTS idx_microgrids_geo ON microgrids USING GIST(grid_polygon);

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
WHERE grid_polygon IS NOT NULL
  AND ST_Contains(
    grid_polygon,
    ST_SetSRID(ST_MakePoint(p_lng, p_lat), 4326)
  )
LIMIT 1;
$$ LANGUAGE sql STABLE;
