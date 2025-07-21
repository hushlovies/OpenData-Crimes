from pymongo import MongoClient, TEXT, ASCENDING, GEOSPHERE

# 1. Connect to your MongoDB instance
client = MongoClient("mongodb://localhost:27017/")  # Replace with your URI if needed

# 2. Select the database and collection
db = client["nyc_crime"]
collection = db["complaints"]

# 3. Create indexes
indexes = [
    ("boro_nm", ASCENDING),
    ("cmplnt_fr_dt", ASCENDING),
    ("law_cat_cd", ASCENDING),
    ("vic_age_group", ASCENDING),
    ("vic_sex", ASCENDING),
    ("vic_race", ASCENDING),
    ("ofns_desc", ASCENDING),
    ([("ofns_desc", TEXT), ("prem_typ_desc", TEXT)], None),  # Text index
    ("location", GEOSPHERE)  # Geospatial index
]

for index in indexes:
    if isinstance(index[0], list):  # for compound text index
        collection.create_index(index[0])
    else:
        collection.create_index([(index[0], index[1])])

print("✅ Indexes created successfully.")
