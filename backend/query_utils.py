"""
Construction des requêtes MongoDB à partir des paramètres URL (request.args).

Paramètres acceptés (tous optionnels) :
- borough=...
- ofns_desc=...
- law_cat_cd=...
- crm_atpt_cptd_cd=...
- vic_sex=F,M,U  (normalisé)
- vic_age=0-17,25-44 (normalisé)
- vic_race=...
- susp_sex=...   (normalisé)
- susp_age=...   (normalisé)
- susp_race=...
- start=YYYY-MM-DD
- end=YYYY-MM-DD
- q= texte (recherche plein texte)

NOTE: Ce module ne modifie pas les données ; il construit seulement le filtre.
"""

from datetime import datetime
from normalization_maps import SEX_STD_TO_RAW, AGE_STD_TO_RAW


def _csv(v):
    if not v:
        return None
    return [s.strip().upper() for s in v.split(",") if s.strip()]


def _expand(mapping: dict, std_list):
    """Mappe des valeurs standardisées (ex: ['F','U']) vers toutes
    les valeurs brutes possibles dans la base."""
    if not std_list:
        return []
    raw = []
    for s in std_list:
        raw += mapping.get(s, [])
    # dédoublonner
    out = []
    seen = set()
    for v in raw:
        key = v if v is not None else "__NONE__"
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def _filter_in(field: str, raw_vals):
    """Construit filtre {field: {$in: [...]}} (si valeurs)."""
    if not raw_vals:
        return None
    return {field: {"$in": raw_vals}}


def build_query(args):
    structured_filters = []

    # ---------------- Base ----------------
    b = _csv(args.get("borough"))
    if b:
        structured_filters.append({"boro_nm": {"$in": b}})

    o = _csv(args.get("ofns_desc"))
    if o:
        structured_filters.append({"ofns_desc": {"$in": o}})

    l = _csv(args.get("law_cat_cd"))
    if l:
        structured_filters.append({"law_cat_cd": {"$in": l}})

    ca = _csv(args.get("crm_atpt_cptd_cd"))
    if ca:
        structured_filters.append({"crm_atpt_cptd_cd": {"$in": ca}})

    # ---------------- Victime ----------------
    vs_std = _csv(args.get("vic_sex"))  # F/M/U
    if vs_std:
        raw = _expand(SEX_STD_TO_RAW, vs_std)
        f = _filter_in("vic_sex", raw)
        if f: structured_filters.append(f)

    va_std = _csv(args.get("vic_age"))  # 0-17, 18-24...
    if va_std:
        raw = _expand(AGE_STD_TO_RAW, va_std)
        f = _filter_in("vic_age_group", raw)
        if f: structured_filters.append(f)

    vr = _csv(args.get("vic_race"))
    if vr:
        structured_filters.append({"vic_race": {"$in": vr}})

    # ---------------- Suspect ----------------
    ss_std = _csv(args.get("susp_sex"))
    if ss_std:
        raw = _expand(SEX_STD_TO_RAW, ss_std)
        f = _filter_in("susp_sex", raw)
        if f: structured_filters.append(f)

    sa_std = _csv(args.get("susp_age"))
    if sa_std:
        raw = _expand(AGE_STD_TO_RAW, sa_std)
        f = _filter_in("susp_age_group", raw)
        if f: structured_filters.append(f)

    sr = _csv(args.get("susp_race"))
    if sr:
        structured_filters.append({"susp_race": {"$in": sr}})

    # ---------------- Dates ----------------
    start = args.get("start")
    end = args.get("end")
    if start and end:
        try:
            sd = datetime.strptime(start, "%Y-%m-%d")
            ed = datetime.strptime(end, "%Y-%m-%d")
            structured_filters.append({
                "cmplnt_fr_dt": {"$gte": sd, "$lte": ed}
            })
        except Exception:
            pass

    # ---------------- Texte (recherche libre via $regex) ----------------
    q_text = args.get("q", "").strip()
    if q_text:
        regex_filter = {"$regex": q_text, "$options": "i"}
        structured_filters.append({
            "$or": [
                {"ofns_desc": regex_filter},
                {"prem_typ_desc": regex_filter},
                {"boro_nm": regex_filter}
            ]
        })

    # ---------------- Final Query ----------------
    if structured_filters:
        return {"$and": structured_filters}
    else:
        return {}