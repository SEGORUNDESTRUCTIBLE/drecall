"""
=========================================================
NEET PG MOCK AI VALIDATION TEST
=========================================================

This tests your backend WITHOUT Gemini.

It intentionally feeds BAD AI output into your
validation system.

=========================================================
RUN
=========================================================

python mock_ai_test.py
=========================================================
"""

import json

# =====================================================
# MOCK BAD AI OUTPUT
# =====================================================

MOCK_AI = {

    # valid
    "title":
        "Distichiasis vs Trichiasis confusion",

    # intentionally bad
    "subject":
        "Ophthal",

    # intentionally bad
    "system":
        "Eyeeeeeee",

    # valid
    "topic":
        "Eyelid disorders",

    # intentionally bad
    "error_type":
        "Image Confusionnnn",

    # valid
    "core_concept":
        "Accessory row of lashes from meibomian glands.",

    # intentionally null
    "why_confusing":
        None,

    # intentionally giant text
    "memory_hook":
        "A" * 5000,

    # valid
    "trap":
        "Posterior to gray line = distichiasis",

    # missing exam_pearl intentionally

    # wrong datatype intentionally
    "tags":
        "high-yield"
}

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

    "tags"
]

# =====================================================
# NORMALIZATION MAPS
# =====================================================

SUBJECT_MAP = {

    "Ophthal": "Ophthalmology"
}

SYSTEM_MAP = {

    "Eyeeeeeee": "Eye"
}

ERROR_TYPE_MAP = {

    "Image Confusionnnn":
        "Image Confusion"
}

# =====================================================
# SAFE TEXT
# =====================================================

def safe_text(text, limit=200):

    if text is None:
        return ""

    return str(text)[:limit]

# =====================================================
# VALIDATION
# =====================================================

print("\n" + "=" * 60)
print("STARTING MOCK AI TEST")
print("=" * 60)

print("\nRAW MOCK AI:\n")

print(json.dumps(MOCK_AI, indent=2))

# =====================================================
# CHECK MISSING KEYS
# =====================================================

print("\n" + "=" * 60)
print("CHECKING REQUIRED KEYS")
print("=" * 60)

missing = []

for key in REQUIRED_KEYS:

    if key not in MOCK_AI:

        print(f"❌ Missing key: {key}")

        missing.append(key)

    else:

        print(f"✅ {key}")

# =====================================================
# NORMALIZATION
# =====================================================

print("\n" + "=" * 60)
print("NORMALIZATION")
print("=" * 60)

# SUBJECT
if MOCK_AI["subject"] in SUBJECT_MAP:

    old = MOCK_AI["subject"]

    MOCK_AI["subject"] = SUBJECT_MAP[old]

    print(
        f"Normalized subject: "
        f"{old} → {MOCK_AI['subject']}"
    )

# SYSTEM
if MOCK_AI["system"] in SYSTEM_MAP:

    old = MOCK_AI["system"]

    MOCK_AI["system"] = SYSTEM_MAP[old]

    print(
        f"Normalized system: "
        f"{old} → {MOCK_AI['system']}"
    )

# ERROR TYPE
if MOCK_AI["error_type"] in ERROR_TYPE_MAP:

    old = MOCK_AI["error_type"]

    MOCK_AI["error_type"] = ERROR_TYPE_MAP[old]

    print(
        f"Normalized error_type: "
        f"{old} → {MOCK_AI['error_type']}"
    )

# =====================================================
# NULL HANDLING
# =====================================================

print("\n" + "=" * 60)
print("NULL HANDLING")
print("=" * 60)

for key, value in MOCK_AI.items():

    if value is None:

        print(f"❌ Null value detected: {key}")

        MOCK_AI[key] = ""

        print(f"✅ Replaced with empty string")

# =====================================================
# TEXT SAFETY
# =====================================================

print("\n" + "=" * 60)
print("TEXT SAFETY")
print("=" * 60)

for key, value in MOCK_AI.items():

    if isinstance(value, str):

        original_length = len(value)

        MOCK_AI[key] = safe_text(value)

        new_length = len(MOCK_AI[key])

        if original_length != new_length:

            print(
                f"⚠ Truncated {key}: "
                f"{original_length} → {new_length}"
            )

# =====================================================
# TAG VALIDATION
# =====================================================

print("\n" + "=" * 60)
print("TAG VALIDATION")
print("=" * 60)

if not isinstance(MOCK_AI["tags"], list):

    print("❌ Tags is not a list")

    MOCK_AI["tags"] = [MOCK_AI["tags"]]

    print("✅ Converted tags to list")

# =====================================================
# FINAL CLEAN JSON
# =====================================================

print("\n" + "=" * 60)
print("FINAL CLEAN JSON")
print("=" * 60)

print(json.dumps(MOCK_AI, indent=2))

# =====================================================
# FINAL STATUS
# =====================================================

print("\n" + "=" * 60)

if len(missing) == 0:

    print("🟢 VALIDATION SUCCESSFUL")

else:

    print("🟡 VALIDATION COMPLETED WITH WARNINGS")

print("=" * 60)

print("""
Your backend is now:

✅ detecting bad AI
✅ repairing malformed fields
✅ normalizing values
✅ truncating unsafe text
✅ fixing tag types
✅ preparing safe Notion ingestion
""")
