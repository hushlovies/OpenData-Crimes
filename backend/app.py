"""
API Flask en français pour l'Explorateur de Criminalité NYC.
"""

from flask import Flask, request, jsonify
from pymongo import MongoClient
from math import ceil
from query_utils import build_query

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "nyc_crime"
COLL_NAME = "complaints"

MAX_PAGE_SIZE = 10000  # Sécurité pagination

app = Flask(__name__)
client = MongoClient(MONGO_URI)
coll = client[DB_NAME][COLL_NAME]


# ------------------------------------------------------------
# Facettes : valeurs distinctes pour alimenter les filtres UI
# ------------------------------------------------------------
@app.route("/api/facettes")
def api_facettes():
    def agg(field, limit=None):
        pipeline = [
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        if limit:
            pipeline.append({"$limit": limit})
        return list(coll.aggregate(pipeline))

    facettes = {
        "boro_nm": agg("boro_nm"),
        "law_cat_cd": agg("law_cat_cd"),
        "crm_atpt_cptd_cd": agg("crm_atpt_cptd_cd"),
        # Victime (brut)
        "vic_race": agg("vic_race"),
        "vic_sex": agg("vic_sex"),
        "vic_age_group": agg("vic_age_group"),
        # Suspect (brut)
        "susp_race": agg("susp_race"),
        "susp_sex": agg("susp_sex"),
        "susp_age_group": agg("susp_age_group"),
        # Infractions
        "ofns_desc": agg("ofns_desc", limit=100),
    }
    return jsonify(facettes)


# ------------------------------------------------------------
# Recherche paginée (table)
# ------------------------------------------------------------
@app.route("/api/recherche")
def api_recherche():
    args = request.args
    q = build_query(args)

    page = int(float(args.get("page", 1)))
    page_size = int(float(args.get("page_size", 1000)))
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    if page_size <= 0:
        page_size = 1000
    skip = (page - 1) * page_size

    mode = args.get("mode", "table")

    if mode == "carte":
        projection = {
            "_id": 0,
            "latitude": 1,
            "longitude": 1,
            "boro_nm": 1,
            "ofns_desc": 1,
            "cmplnt_fr_dt": 1,
        }
    elif mode == "table":
        projection = {
            "_id": 0,
            "cmplnt_num": 1,
            "cmplnt_fr_dt": 1, "cmplnt_fr_tm": 1,
            "boro_nm": 1, "ofns_desc": 1, "law_cat_cd": 1,
            "crm_atpt_cptd_cd": 1,
            "vic_age_group": 1, "vic_sex": 1, "vic_race": 1,
            "susp_age_group": 1, "susp_sex": 1, "susp_race": 1,
            "prem_typ_desc": 1,
            "latitude": 1, "longitude": 1,
        }
    else:
        projection = None

    total = coll.count_documents(q)

    cursor = coll.find(q, projection).skip(skip).limit(page_size)
    docs = list(cursor)

    total_pages = ceil(total / page_size) if page_size else 1

    return jsonify({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "mode": mode,
        "data": docs,
    })


# ------------------------------------------------------------
# Carte : tous les points filtrés (⚠️ perfs selon volume)
#    Optionnel: ?sample=N pour limiter
# ------------------------------------------------------------
@app.route("/api/carte")
def api_carte():
    args = request.args
    q = build_query(args)

    sample = args.get("sample")
    projection = {
        "_id": 0,
        "latitude": 1,
        "longitude": 1,
        "boro_nm": 1,
        "ofns_desc": 1,
        "cmplnt_fr_dt": 1,
    }

    if sample:
        try:
            s = int(sample)
            if s > 0:
                pipeline = [
                    {"$match": q},
                    {"$sample": {"size": s}},
                    {"$project": projection},
                ]
                docs = list(coll.aggregate(pipeline))
                return jsonify(docs)
        except Exception:
            pass

    # Full
    docs = list(coll.find(q, projection))
    return jsonify(docs)


if __name__ == "__main__":
    # host=0.0.0.0 pour accès réseau
    app.run(host="0.0.0.0", port=5000, debug=True)
