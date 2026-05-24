# =====================================================
# GEMINI INGESTION TEST
# NEW SDK VERSION
# =====================================================

print("STARTING GEMINI INGESTION TEST")

# =====================================================
# IMPORTS
# =====================================================

import json

from google import genai

from legacy_config import GEMINI_API_KEY

from normalizers import normalize_data

from validators import full_validation

from duplicate_detector import (
    find_duplicates,
    has_duplicate
)

print("✅ Imports successful")

# =====================================================
# GEMINI CLIENT
# =====================================================

client = genai.Client(

    api_key=GEMINI_API_KEY
)

print("✅ Gemini client initialized")

# =====================================================
# EXISTING DATABASE TITLES
# =====================================================

existing_titles = [

    "Distichiasis vs Trichiasis confusion",

    "Papilledema vs papillitis"
]

# =====================================================
# USER INPUT
# =====================================================

USER_INPUT = """

Distichiasis vs trichiasis confusion.

I confused accessory lash row
arising from meibomian glands
with misdirected eyelashes.

Posterior to gray line.

"""

# =====================================================
# PROMPT
# =====================================================

PROMPT = f"""

You are a NEET PG medical mistake parser.

Convert the mistake into STRICT JSON.

RULES:
- RETURN JSON ONLY
- NO markdown
- NO explanations
- tags MUST be a list

Return schema:

{{
    "title": "",
    "subject": "",
    "system": "",
    "topic": "",
    "error_type": "",
    "core_concept": "",
    "why_confusing": "",
    "memory_hook": "",
    "trap": "",
    "exam_pearl": "",
    "one_liner_revision": "",
    "retest_question": "",
    "pattern_type": "",
    "tags": []
}}

Medical mistake:

{USER_INPUT}

"""

# =====================================================
# RUN GEMINI
# =====================================================

print("\n" + "=" * 60)
print("RUNNING GEMINI")
print("=" * 60)

try:

    response = client.models.generate_content(

        model="gemini-2.0-flash-lite",

        contents=PROMPT
    )

    raw_text = response.text

except Exception as e:

    print("\n🔴 GEMINI FAILED")

    print(e)

    exit()

# =====================================================
# RAW OUTPUT
# =====================================================

print("\n" + "=" * 60)
print("RAW GEMINI OUTPUT")
print("=" * 60)

print(raw_text)

# =====================================================
# JSON PARSE
# =====================================================

try:

    ai_data = json.loads(raw_text)

    print("\n✅ JSON parse success")

except Exception as e:

    print("\n🔴 JSON PARSE FAILED")

    print(e)

    exit()

# =====================================================
# NORMALIZATION
# =====================================================

cleaned = normalize_data(
    ai_data
)

print("\n" + "=" * 60)
print("NORMALIZED DATA")
print("=" * 60)

print(cleaned)

# =====================================================
# VALIDATION
# =====================================================

report = full_validation(
    cleaned
)

print("\n" + "=" * 60)
print("VALIDATION REPORT")
print("=" * 60)

for key, value in report.items():

    print(f"{key}: {value}")

# =====================================================
# DUPLICATE CHECK
# =====================================================

duplicates = find_duplicates(

    cleaned["title"],
    existing_titles,
    threshold=0.80
)

print("\n" + "=" * 60)
print("DUPLICATE CHECK")
print("=" * 60)

if len(duplicates) == 0:

    print("✅ No duplicates")

else:

    for dup in duplicates:

        print(
            f"- {dup['title']} "
            f"({dup['type']}, "
            f"{dup['similarity']})"
        )

# =====================================================
# FINAL DECISION
# =====================================================

safe = True

if not report["valid"]:

    safe = False

if has_duplicate(

    cleaned["title"],
    existing_titles,
    threshold=0.80
):

    safe = False

print("\n" + "=" * 60)
print("FINAL STATUS")
print("=" * 60)

if safe:

    print("🟢 SAFE FOR INGESTION")

else:

    print("🔴 INGESTION BLOCKED")

print("\n✅ GEMINI TEST COMPLETE")
