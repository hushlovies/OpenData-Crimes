"""
frontend/app.py

Explorateur Streamlit — Plainte NYC
- UI en français
- Filtres Victime & Suspect (sexe, âge classes, race brute)
- Plage de dates via calendrier
- Pagination stable : seul tableau change de page
- Pas d'erreur si aucun résultat (pas de StreamlitValueAboveMaxError)
- Carte = tous les points filtrés (⚠️ peut être lourd)
- Âges dans tableau : champs dérivés age_vic_approx / age_susp_approx (borne basse de la tranche)
"""

import streamlit as st
import pandas as pd
import requests
import datetime

API_BASE = "http://localhost:5000"

st.set_page_config(page_title="Visualisation interactive des plaintes enregistrées par la NYPD", layout="wide")
st.title("🔎 Visualisation interactive des plaintes enregistrées par la NYPD")

# ------------------------------------------------------------------
# Options normalisées (doivent refléter backend/normalization_maps.py)
# ------------------------------------------------------------------
SEX_STD_ORDER = ["F", "M", "U"]
AGE_STD_ORDER = ["0-17", "18-24", "25-44", "45-64", "65+", "INCONNU"]

SEX_STD_LABELS = {"F": "Femme", "M": "Homme", "U": "Inconnu"}
AGE_STD_LABELS = {
    "0-17": "0-17 ans",
    "18-24": "18-24 ans",
    "25-44": "25-44 ans",
    "45-64": "45-64 ans",
    "65+": "65 ans et +",
    "INCONNU": "Inconnu",
}

# ------------------------------------------------------------------
# Facettes (cache)
# ------------------------------------------------------------------
@st.cache_data(ttl=600)
def charger_facettes():
    r = requests.get(f"{API_BASE}/api/facettes")
    if r.status_code != 200:
        return {}
    return r.json()

facettes = charger_facettes()

def _vals(nom):
    return [f["_id"] for f in facettes.get(nom, []) if f["_id"]]

# ------------------------------------------------------------------
# Session State init
# ------------------------------------------------------------------
if "run_search" not in st.session_state:
    st.session_state.run_search = False
if "filtres" not in st.session_state:
    st.session_state.filtres = {}
if "page_actuelle" not in st.session_state:
    st.session_state.page_actuelle = 1
if "lignes_page" not in st.session_state:
    st.session_state.lignes_page = 1000
if "map_df" not in st.session_state:
    st.session_state.map_df = None
if "total_resultats" not in st.session_state:
    st.session_state.total_resultats = 0
if "total_pages" not in st.session_state:
    st.session_state.total_pages = 1

# ------------------------------------------------------------------
# Date range from state
# ------------------------------------------------------------------
def _default_date_range_from_state():
    sd = st.session_state.filtres.get("start")
    ed = st.session_state.filtres.get("end")
    if sd and ed:
        try:
            sd_dt = datetime.date.fromisoformat(sd)
            ed_dt = datetime.date.fromisoformat(ed)
            return (sd_dt, ed_dt)
        except Exception:
            return ()
    return ()

# ------------------------------------------------------------------
# Formulaire Sidebar
# ------------------------------------------------------------------
with st.sidebar.form("filtres_form"):
    st.header("Filtres principaux")

    q_text = st.text_input(
        "Recherche (mot-clé : type d'infraction, lieu…)",
        value=st.session_state.filtres.get("q", "")
    )

    boroughs = st.multiselect(
        "Borough(s)",
        _vals("boro_nm"),
        default=st.session_state.filtres.get("borough", "").split(",") if st.session_state.filtres.get("borough") else []
    )

    ofns = st.multiselect(
        "Infraction (top 100)",
        _vals("ofns_desc"),
        default=st.session_state.filtres.get("ofns_desc", "").split(",") if st.session_state.filtres.get("ofns_desc") else []
    )

    law_cats = st.multiselect(
        "Catégorie légale",
        _vals("law_cat_cd"),
        default=st.session_state.filtres.get("law_cat_cd", "").split(",") if st.session_state.filtres.get("law_cat_cd") else []
    )

    crm_status = st.multiselect(
        "Statut de l'affaire",
        _vals("crm_atpt_cptd_cd"),
        default=st.session_state.filtres.get("crm_atpt_cptd_cd", "").split(",") if st.session_state.filtres.get("crm_atpt_cptd_cd") else []
    )

    # --- Victime ---
    st.markdown("### Victime")
    vic_sex_std_default = st.session_state.filtres.get("vic_sex", "").split(",") if st.session_state.filtres.get("vic_sex") else []
    vic_sex_std = st.multiselect(
        "Sexe victime",
        options=SEX_STD_ORDER,
        format_func=lambda x: SEX_STD_LABELS[x],
        default=vic_sex_std_default,
    )

    vic_age_std_default = st.session_state.filtres.get("vic_age", "").split(",") if st.session_state.filtres.get("vic_age") else []
    vic_age_std = st.multiselect(
        "Âge victime (classes)",
        options=AGE_STD_ORDER,
        format_func=lambda x: AGE_STD_LABELS[x],
        default=vic_age_std_default,
    )

    vic_race_default = st.session_state.filtres.get("vic_race", "").split(",") if st.session_state.filtres.get("vic_race") else []
    vic_race = st.multiselect(
        "Origine victime (brut)",
        _vals("vic_race"),
        default=vic_race_default,
    )

    # --- Suspect ---
    with st.expander("Filtres suspect (optionnel)"):
        susp_sex_std_default = st.session_state.filtres.get("susp_sex", "").split(",") if st.session_state.filtres.get("susp_sex") else []
        susp_sex_std = st.multiselect(
            "Sexe suspect",
            options=SEX_STD_ORDER,
            format_func=lambda x: SEX_STD_LABELS[x],
            default=susp_sex_std_default,
        )

        susp_age_std_default = st.session_state.filtres.get("susp_age", "").split(",") if st.session_state.filtres.get("susp_age") else []
        susp_age_std = st.multiselect(
            "Âge suspect (classes)",
            options=AGE_STD_ORDER,
            format_func=lambda x: AGE_STD_LABELS[x],
            default=susp_age_std_default,
        )

        susp_race_default = st.session_state.filtres.get("susp_race", "").split(",") if st.session_state.filtres.get("susp_race") else []
        susp_race = st.multiselect(
            "Origine suspect (brut)",
            _vals("susp_race"),  # backend fournit facette suspect
            default=susp_race_default,
        )

    # --- Dates ---
    st.markdown("---")
    date_range = st.date_input(
        "Période (début & fin)",
        value=_default_date_range_from_state(),
        format="YYYY-MM-DD",
        help="Choisis un intervalle. Laisse vide pour ignorer."
    )

    # Interprétation
    sd = ed = None
    if isinstance(date_range, (list, tuple)):
        if len(date_range) == 2:
            sd, ed = date_range
        elif len(date_range) == 1:
            sd = ed = date_range[0]

    # --- Pagination table ---
    st.markdown("---")
    lignes_page = st.number_input(
        "Lignes par page (tableau)",
        min_value=100,
        max_value=10000,
        value=int(st.session_state.lignes_page),
        step=100,
    )

    soumis = st.form_submit_button("Rechercher")

# ------------------------------------------------------------------
# Construire params envoyés à l'API
# ------------------------------------------------------------------
def _build_params():
    p = {}
    if q_text.strip():
        p["q"] = q_text.strip()
    if boroughs:
        p["borough"] = ",".join(boroughs)
    if ofns:
        p["ofns_desc"] = ",".join(ofns)
    if law_cats:
        p["law_cat_cd"] = ",".join(law_cats)
    if crm_status:
        p["crm_atpt_cptd_cd"] = ",".join(crm_status)

    # Victime normalisée
    if vic_sex_std:
        p["vic_sex"] = ",".join(vic_sex_std)
    if vic_age_std:
        p["vic_age"] = ",".join(vic_age_std)
    if vic_race:
        p["vic_race"] = ",".join(vic_race)

    # Suspect normalisée
    if susp_sex_std:
        p["susp_sex"] = ",".join(susp_sex_std)
    if susp_age_std:
        p["susp_age"] = ",".join(susp_age_std)
    if susp_race:
        p["susp_race"] = ",".join(susp_race)

    if sd and ed:
        p["start"] = sd.strftime("%Y-%m-%d")
        p["end"] = ed.strftime("%Y-%m-%d")

    return p

# ------------------------------------------------------------------
# Soumission
# ------------------------------------------------------------------
if soumis:
    st.session_state.filtres = _build_params()
    st.session_state.lignes_page = int(lignes_page)
    st.session_state.page_actuelle = 1
    st.session_state.run_search = True
    st.session_state.map_df = None  # Forcer reload carte

# ------------------------------------------------------------------
# API calls
# ------------------------------------------------------------------
def api_recherche_table(filtres: dict, page: int, page_size: int):
    params = filtres.copy()
    params["page"] = page
    params["page_size"] = page_size
    params["mode"] = "table"
    r = requests.get(f"{API_BASE}/api/recherche", params=params)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False)
def api_carte_full_cached(filtres: dict):
    params = filtres.copy()
    r = requests.get(f"{API_BASE}/api/carte", params=params)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data)
    if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
        df = df.dropna(subset=["latitude", "longitude"])
        df["lat"] = df["latitude"].astype(float)
        df["lon"] = df["longitude"].astype(float)
    return df

# ------------------------------------------------------------------
# Fonctions d'aide pour approx âge (front)
# ------------------------------------------------------------------
def approx_from_group(series):
    """Convertit une Series de groupes d'âge en âge approx (borne basse)."""
    mapping = {
        "<18": 0, "18-24": 18, "25-44": 25, "45-64": 45,
        "65+": 65, "65-": 65, "UNKNOWN": None, "": None
    }
    return series.map(lambda v: mapping.get(str(v).upper() if v is not None else "UNKNOWN", None))

# ------------------------------------------------------------------
# Affichage résultats
# ------------------------------------------------------------------
if st.session_state.run_search:
    filtres = st.session_state.filtres
    page = st.session_state.page_actuelle
    page_size = st.session_state.lignes_page

    # Table (page courante)
    try:
        payload = api_recherche_table(filtres, page, page_size)
    except Exception as e:
        st.error(f"Erreur API /recherche : {e}")
        st.stop()

    total = payload["total"]
    total_pages = payload["total_pages"]
    st.session_state.total_resultats = total
    st.session_state.total_pages = total_pages

    # Carte (full)
    if st.session_state.map_df is None:
        try:
            df_map = api_carte_full_cached(filtres)
        except Exception as e:
            st.error(f"Erreur API /carte : {e}")
            df_map = pd.DataFrame()
        st.session_state.map_df = df_map
    else:
        df_map = st.session_state.map_df

    st.subheader(f"Total des cas correspondants : {total:,}")
    if df_map.empty:
        st.warning("Aucune donnée géolocalisable (ou aucun résultat).")
    else:
        if len(df_map) > 100_000:
            st.caption(f"⚠️ {len(df_map):,} points à afficher — cela peut ralentir le navigateur.")
        st.map(df_map[["lat", "lon"]])

    # Tableau
    st.markdown("---")
    st.subheader("Tableau des cas")

    if total == 0:
        st.info("Aucun résultat pour les filtres sélectionnés.")
    else:
        st.write(f"Page {page} / {total_pages} — Lignes/page : {page_size}")

        df_table = pd.DataFrame(payload["data"])

        # Ajouter colonnes âge approx
        if "vic_age_group" in df_table.columns:
            df_table["age_vic_approx"] = approx_from_group(df_table["vic_age_group"])
        if "susp_age_group" in df_table.columns:
            df_table["age_susp_approx"] = approx_from_group(df_table["susp_age_group"])

        # Option: masquer les colonnes group si tu préfères
        # cols_drop = ["vic_age_group","susp_age_group"]
        # df_table = df_table.drop(columns=[c for c in cols_drop if c in df_table.columns])

        st.dataframe(df_table, use_container_width=True)

        # Pagination (uniquement si >1 page)
        if total_pages > 1:
            col_prev, col_page, col_next = st.columns([1,2,1])
            with col_prev:
                if st.button("⬅ Précédent", disabled=page <= 1):
                    st.session_state.page_actuelle = page - 1
                    st.rerun()
            with col_page:
                page_val = st.number_input(
                    "Aller à la page",
                    min_value=1,
                    max_value=total_pages,
                    value=page,
                    step=1,
                    key="page_input_number"
                )
                if page_val != page:
                    st.session_state.page_actuelle = page_val
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡", disabled=page >= total_pages):
                    st.session_state.page_actuelle = page + 1
                    st.rerun()

else:
    st.info("Configure des filtres puis clique **Rechercher** dans la barre latérale.")
