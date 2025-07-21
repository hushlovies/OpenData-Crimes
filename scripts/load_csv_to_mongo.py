import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import math

CSV_PATH = "data/NYPD_Complaint_Data_Historic_20250716.csv"  # adjust if needed
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "nyc_crime"
COLL_NAME = "complaints"
CHUNK_SIZE = 100_000  # adjust; 500k rows -> ~5 chunks

# Columns we keep (subset for performance)
KEEP_COLS = [
    "CMPLNT_NUM","CMPLNT_FR_DT","CMPLNT_FR_TM","CMPLNT_TO_DT","CMPLNT_TO_TM",
    "OFNS_DESC","LAW_CAT_CD","CRM_ATPT_CPTD_CD",
    "BORO_NM","ADDR_PCT_CD",
    "VIC_AGE_GROUP","VIC_SEX","VIC_RACE",
    "SUSP_AGE_GROUP","SUSP_SEX","SUSP_RACE",
    "PREM_TYP_DESC",
    "Latitude","Longitude"
]

client = MongoClient(MONGO_URI)
coll = client[DB_NAME][COLL_NAME]

# Clear existing (CAUTION!)
print("Dropping existing documents...")
coll.delete_many({})

# Read in chunks
print("Loading CSV in chunks...")
chunk_iter = pd.read_csv(
    CSV_PATH,
    usecols=lambda c: c in KEEP_COLS,  # filter on load
    chunksize=CHUNK_SIZE,
    low_memory=False
)

total_inserted = 0

for i, chunk in enumerate(chunk_iter, start=1):
    print(f"Processing chunk {i}...")

    # Normalize '(null)' -> None
    chunk = chunk.replace("(null)", None)

    # Parse date
    chunk["CMPLNT_FR_DT"] = pd.to_datetime(chunk["CMPLNT_FR_DT"], errors="coerce")

    # Drop rows w/o coords
    chunk = chunk.dropna(subset=["Latitude", "Longitude"])

    # Ensure numeric lat/lon
    chunk["Latitude"] = pd.to_numeric(chunk["Latitude"], errors="coerce")
    chunk["Longitude"] = pd.to_numeric(chunk["Longitude"], errors="coerce")
    chunk = chunk.dropna(subset=["Latitude", "Longitude"])

    # Lowercase field names for DB consistency
    chunk.columns = [c.lower() for c in chunk.columns]

    # Build docs row‑by‑row (convert row Series -> dict)
    records = []
    for doc in chunk.to_dict(orient="records"):
        # Add GeoJSON location (helps indexing & future map aggregation)
        lat = doc.get("latitude")
        lon = doc.get("longitude")
        if lat is not None and lon is not None:
            doc["location"] = {"type": "Point", "coordinates": [float(lon), float(lat)]}
        # Ensure dates are Python datetime (Mongo stores BSON datetime)
        dt = doc.get("cmplnt_fr_dt")
        if pd.notna(dt):
            if isinstance(dt, pd.Timestamp):
                doc["cmplnt_fr_dt"] = dt.to_pydatetime()
        else:
            doc["cmplnt_fr_dt"] = None
        records.append(doc)

    if records:
        coll.insert_many(records, ordered=False)
        total_inserted += len(records)
        print(f"...inserted {len(records)} docs (running total: {total_inserted})")

print(f"✅ Done. Inserted total: {total_inserted} docs.")