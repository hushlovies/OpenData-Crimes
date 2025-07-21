"""
Mappings de normalisation pour sexe et âges (victime & suspect).
Utilisés par query_utils pour traduire les choix UI (F/M/U, 0-17, etc.)
en valeurs brutes présentes dans la base NYPD.
"""

# --- Sexe ---
SEX_STD_TO_RAW = {
    "F": ["F", "FEMALE", "FEM"],
    "M": ["M", "MALE"],
    "U": ["U", "UNK", "UNKNOWN", "X", "", None],  # inconnus regroupés
}

# --- Âges ---
# Valeurs brutes NYPD: "<18","18-24","25-44","45-64","65+","UNKNOWN"
AGE_STD_TO_RAW = {
    "0-17": ["<18"],
    "18-24": ["18-24"],
    "25-44": ["25-44"],
    "45-64": ["45-64"],
    "65+":   ["65+", "65-"],  # parfois variations
    "INCONNU": ["UNKNOWN", "", None],
    # alias possible:
    "80+": ["65+", "65-"],
}

# Ordres & libellés (facultatif, utilisé côté front)
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
    "80+": "80 ans et + (≈65+)",
}


# ------------------------------------------------------------------
# Conversion tranche -> bornes numériques + âge approx (borne basse)
# ------------------------------------------------------------------
def parse_age_group_to_bounds(label: str):
    """Retourne (min_age, max_age, approx_age) pour un label d'âge NYPD."""
    if not label:
        return (None, None, None)
    l = str(label).strip().upper()
    if l == "<18":
        return (0, 17, 0)
    if l == "18-24":
        return (18, 24, 18)
    if l == "25-44":
        return (25, 44, 25)
    if l == "45-64":
        return (45, 64, 45)
    if l in ("65+", "65-"):
        return (65, None, 65)
    if l in ("UNKNOWN", ""):
        return (None, None, None)
    # fallback: tente split
    if "-" in l:
        try:
            a, b = l.split("-", 1)
            a = int(a)
            b = int(b)
            return (a, b, a)
        except Exception:
            pass
    return (None, None, None)
