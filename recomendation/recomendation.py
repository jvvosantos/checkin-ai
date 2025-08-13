from fastapi import FastAPI, Query
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import math
import os
from pydantic import BaseModel


app = FastAPI()

host = "170.78.97.36"
port = 5400
dbname = "checkin"
user = "MF_admin"
password = "proj_proj"

conn_str = f"dbname={dbname} user={user} password={password} host={host} port={port}"
conn = psycopg2.connect(conn_str)

# DB_URL = os.getenv("0.0.0.0:5432", "dbname=postgres user=postgres password=mysecretpassword host=localhost")
# conn = psycopg2.connect(DB_URL)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))


@app.get("/restaurants/search")
def search_restaurants(
    query: Optional[str] = None,
    features: Optional[List[str]] = Query(None),
    min_rating: float = 0,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    limit: int = 5
):
    print(query)
    sql = """
    SELECT id, name, description, category, address, rating, total_reviews, price_range, features, latitude, longitude
    FROM venues
    WHERE rating >= %s
    """
    params = [min_rating]

    if query:
        sql += """
          AND (
              name ILIKE %s OR
              features ILIKE %s OR
              description ILIKE %s OR
              category ILIKE %s
          )
        """
        for _ in range(4):
            params.append(f"%{query}%")

    if features:
        for f in features:
            sql += " AND features ILIKE %s"
            params.append(f"%{f}%")

    sql += " ORDER BY rating DESC, total_reviews DESC LIMIT %s"
    params.append(limit)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        results = cur.fetchall()

    # Distance filter & sort
    if lat is not None and lon is not None:
        for r in results:
            if r["latitude"] is not None and r["longitude"] is not None:
                r["distance_km"] = round(haversine(lat, lon, float(r["latitude"]), float(r["longitude"])), 2)
            else:
                r["distance_km"] = None

        if max_distance_km is not None:
            results = [r for r in results if r["distance_km"] is not None and r["distance_km"] <= max_distance_km]

        results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else float("inf")))

    return results

class RecommendationRequest(BaseModel):
    query: Optional[str] = None
    features: Optional[List[str]] = None
    min_rating: float = 0
    lat: Optional[float] = None
    lon: Optional[float] = None
    max_distance_km: Optional[float] = None
    limit: int = 5

@app.post("/recommendations")
def recommendations(req: RecommendationRequest):
    print(req.query)
    results = search_restaurants(
        query=req.query,
        features=req.features,
        min_rating=req.min_rating,
        lat=req.lat,
        lon=req.lon,
        max_distance_km=req.max_distance_km,
        limit=req.limit,
    )
    return results

@app.get("/")
def read_root():
    return {"Hello": "World"}