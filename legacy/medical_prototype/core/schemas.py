# =====================================================
# SCHEMAS
# FINAL PRODUCTION VERSION
# =====================================================

# =====================================================
# REQUIRED KEYS
# =====================================================

REQUIRED_KEYS = [

    "title",
    "subject",
    "system",
    "topic",
    "error_type",

    "core_concept",
    "why_confusing",
    "memory_hook",
    "trap",
    "exam_pearl",

    "one_liner_revision",
    "retest_question",

    "pattern_type",
    "tags"
]

# =====================================================
# OPTIONAL KEYS
# =====================================================

OPTIONAL_KEYS = [

    "subtopic",

    "image_diagnosis",

    "differentials",

    "classic_finding",

    "ai_note",

    "source",

    "difficulty"
]

# =====================================================
# CRITICAL KEYS
# =====================================================

CRITICAL_KEYS = [

    "title",

    "subject",

    "core_concept"
]

# =====================================================
# REJECT IF EMPTY
# =====================================================

REJECT_IF_EMPTY = [

    "title",

    "core_concept"
]

# =====================================================
# VALID SUBJECTS
# =====================================================

VALID_SUBJECTS = [

    "Anatomy",

    "Physiology",

    "Biochemistry",

    "Pathology",

    "Pharmacology",

    "Microbiology",

    "Forensic Medicine",

    "Community Medicine (PSM)",

    "Ophthalmology",

    "Otorhinolaryngology (ENT)",

    "Medicine",

    "Surgery",

    "Obstetrics & Gynecology",

    "Pediatrics",

    "Orthopedics",

    "Dermatology",

    "Psychiatry",

    "Anesthesiology",

    "Radiology"
]

# =====================================================
# VALID SYSTEMS
# =====================================================

VALID_SYSTEMS = [

    "CVS",

    "CNS",

    "RS",

    "GIT",

    "Renal",

    "Endocrine",

    "Hematology",

    "MSK",

    "Derm",

    "Ophthal",

    "ENT",

    "Neuro",

    "Repro",

    "Eye",

    "Cardiovascular",

    "Respiratory",

    "Neurology",

    "Skin"
]

# =====================================================
# VALID ERROR TYPES
# =====================================================

VALID_ERROR_TYPES = [

    "Misread question / stem",

    "Overlooked keyword (except/most/least/NOT)",

    "Confused similar concepts",

    "Incorrect elimination strategy",

    "Calculation / unit error",

    "Did not recall fact/formula",

    "Applied wrong rule/threshold (cutoff values)",

    "Image/graph interpretation error",

    "Time pressure / rushed guess",

    "Image Confusion",

    "Conceptual",

    "Silly Mistake",

    "Recall Failure",

    "Integration Failure",

    "Guessing",

    "Revision Gap"
]

# =====================================================
# VALID PATTERN TYPES
# =====================================================

VALID_PATTERN_TYPES = [

    "ECG",

    "Fundus",

    "Histopathology",

    "Radiology",

    "Dermatology",

    "Gross Specimen",

    "Clinical Spotter"
]

# =====================================================
# VALID TAGS
# =====================================================

VALID_TAGS = [

    "high-yield",

    "image-based",

    "confusion",

    "PYQ",

    "integrated",

    "rapid-recall",

    "spotter",

    "revision",

    "conceptual",

    "clinical"
]

# =====================================================
# MAX TEXT LENGTHS
# =====================================================

MAX_TEXT_LENGTHS = {

    "title": 120,

    "topic": 100,

    "subtopic": 100,

    "core_concept": 2000,

    "why_confusing": 1000,

    "memory_hook": 500,

    "trap": 1000,

    "exam_pearl": 1000,

    "classic_finding": 1000,

    "differentials": 1000,

    "one_liner_revision": 300,

    "retest_question": 1000,

    "ai_note": 1000
}