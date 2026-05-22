# =====================================================
# NORMALIZERS
# FINAL PRODUCTION VERSION
# STRICT SCHEMA-COMPATIBLE
# =====================================================

# =====================================================
# SUBJECT MAP
# =====================================================

SUBJECT_MAP = {

    "ophthal":
        "Ophthalmology",

    "ophthalmology":
        "Ophthalmology",

    "ocular":
        "Ophthalmology",

    "eye":
        "Ophthalmology",

    "med":
        "Medicine",

    "medicine":
        "Medicine",

    "surgery":
        "Surgery",

    "ent":
        "Otorhinolaryngology (ENT)",

    "derma":
        "Dermatology",

    "dermatology":
        "Dermatology",

    "radio":
        "Radiology",

    "radiology":
        "Radiology",

    "path":
        "Pathology",

    "pathology":
        "Pathology",

    "pharma":
        "Pharmacology",

    "pharmacology":
        "Pharmacology",

    "micro":
        "Microbiology",

    "microbiology":
        "Microbiology",

    "anat":
        "Anatomy",

    "anatomy":
        "Anatomy",

    "physio":
        "Physiology",

    "physiology":
        "Physiology",

    "biochem":
        "Biochemistry",

    "biochemistry":
        "Biochemistry",

    "psm":
        "Community Medicine (PSM)"
}

# =====================================================
# SYSTEM MAP
# =====================================================

SYSTEM_MAP = {

    "ophthal":
        "Eye",

    "eye":
        "Eye",

    "ocular":
        "Eye",

    "cvs":
        "CVS",

    "cardio":
        "CVS",

    "heart":
        "CVS",

    "cns":
        "CNS",

    "brain":
        "CNS",

    "neuro":
        "Neuro",

    "resp":
        "RS",

    "lung":
        "RS",

    "git":
        "GIT",

    "gastro":
        "GIT",

    "renal":
        "Renal",

    "kidney":
        "Renal",

    "endo":
        "Endocrine",

    "skin":
        "Skin",

    "ent":
        "ENT"
}

# =====================================================
# ERROR TYPE MAP
# =====================================================

ERROR_TYPE_MAP = {

    "guess":
        "Guessing",

    "guessing":
        "Guessing",

    "image confusion":
        "Image Confusion",

    "image/graph interpretation error":
        "Image/graph interpretation error",

    "confused similar concepts":
        "Confused similar concepts",

    "confused similar concept":
        "Confused similar concepts",

    "conceptual":
        "Conceptual",

    "recall failure":
        "Recall Failure",

    "integration failure":
        "Integration Failure",

    "revision gap":
        "Revision Gap",

    "silly mistake":
        "Silly Mistake",

    "misread question / stem":
        "Misread question / stem",

    "time pressure / rushed guess":
        "Time pressure / rushed guess",

    "incorrect elimination strategy":
        "Incorrect elimination strategy",

    "did not recall fact/formula":
        "Did not recall fact/formula",

    "calculation / unit error":
        "Calculation / unit error",

    "applied wrong rule/threshold (cutoff values)":
        "Applied wrong rule/threshold (cutoff values)",

    "overlooked keyword (except/most/least/not)":
        "Overlooked keyword (except/most/least/NOT)"
}

# =====================================================
# PATTERN TYPE MAP
# =====================================================

PATTERN_TYPE_MAP = {

    "ecg":
        "ECG",

    "fundus":
        "Fundus",

    "histopathology":
        "Histopathology",

    "radiology":
        "Radiology",

    "dermatology":
        "Dermatology",

    "gross specimen":
        "Gross Specimen",

    "clinical spotter":
        "Clinical Spotter",

    "spotter":
        "Clinical Spotter"
}

# =====================================================
# VALID TAGS
# =====================================================

VALID_TAGS = {

    "high-yield",

    "image-based",

    "confusion",

    "pyq",

    "integrated",

    "rapid-recall",

    "spotter",

    "revision",

    "conceptual",

    "clinical"
}

# =====================================================
# NORMALIZE SUBJECT
# =====================================================

def normalize_subject(value):

    if value is None:

        return ""

    cleaned = (
        str(value)
        .strip()
        .lower()
    )

    return SUBJECT_MAP.get(
        cleaned,
        value
    )

# =====================================================
# NORMALIZE SYSTEM
# =====================================================

def normalize_system(value):

    if value is None:

        return ""

    cleaned = (
        str(value)
        .strip()
        .lower()
    )

    return SYSTEM_MAP.get(
        cleaned,
        value
    )

# =====================================================
# NORMALIZE ERROR TYPE
# =====================================================

def normalize_error_type(value):

    if value is None:

        return ""

    cleaned = (
        str(value)
        .strip()
        .lower()
    )

    return ERROR_TYPE_MAP.get(
        cleaned,
        value
    )

# =====================================================
# NORMALIZE PATTERN TYPE
# =====================================================

def normalize_pattern_type(value):

    if value is None:

        return ""

    cleaned = (
        str(value)
        .strip()
        .lower()
    )

    return PATTERN_TYPE_MAP.get(
        cleaned,
        value
    )

# =====================================================
# NORMALIZE TAGS
# =====================================================

def normalize_tags(tags):

    if not isinstance(tags, list):

        return []

    cleaned_tags = []

    for tag in tags:

        if tag is None:

            continue

        cleaned = (
            str(tag)
            .strip()
            .lower()
        )

        if cleaned in VALID_TAGS:

            cleaned_tags.append(cleaned)

    # remove duplicates
    return list(dict.fromkeys(cleaned_tags))

# =====================================================
# NORMALIZE FULL DATA
# =====================================================

def normalize_data(data):

    if not isinstance(data, dict):

        return {}

    # =================================================
    # SUBJECT
    # =================================================

    if "subject" in data:

        data["subject"] = normalize_subject(
            data["subject"]
        )

    # =================================================
    # SYSTEM
    # =================================================

    if "system" in data:

        data["system"] = normalize_system(
            data["system"]
        )

    # =================================================
    # ERROR TYPE
    # =================================================

    if "error_type" in data:

        data["error_type"] = (
            normalize_error_type(
                data["error_type"]
            )
        )

    # =================================================
    # PATTERN TYPE
    # =================================================

    if "pattern_type" in data:

        data["pattern_type"] = (
            normalize_pattern_type(
                data["pattern_type"]
            )
        )

    # =================================================
    # TAGS
    # =================================================

    if "tags" in data:

        data["tags"] = normalize_tags(
            data["tags"]
        )

    return data