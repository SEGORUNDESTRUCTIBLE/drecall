# =====================================================
# GROQ INGESTION ENGINE
# FINAL CORRECTED PRODUCTION VERSION
# =====================================================

print("STARTING GROQ INGESTION")

# =====================================================
# IMPORTS
# =====================================================

import json

from groq import Groq

from legacy_config import GROQ_API_KEY

from legacy_core.prompt_builder import (
    build_prompt
)

from legacy_core.normalizers import (
    normalize_data
)

from legacy_core.validators import (
    full_validation
)

from legacy_core.duplicate_detector import (
    find_duplicates
)

print("✅ Imports successful")

# =====================================================
# GROQ CLIENT
# =====================================================

client = Groq(

    api_key=GROQ_API_KEY
)

print("✅ Groq initialized")

# =====================================================
# EXISTING TITLES
# =====================================================

existing_titles = [

    "Distichiasis vs Trichiasis confusion",

    "Papilledema vs papillitis"
]

# =====================================================
# USER INPUT
# =====================================================

USER_INPUT = '''

Distichiasis vs trichiasis confusion.

I confused accessory lash row
arising from meibomian glands
with misdirected eyelashes.

Posterior to gray line.

'''

# =====================================================
# BUILD PROMPT
# =====================================================

PROMPT = build_prompt(
    USER_INPUT
)

print("✅ Prompt built")

# =====================================================
# RUN GROQ
# =====================================================

print("\n" + "=" * 60)
print("RUNNING GROQ")
print("=" * 60)

try:

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        temperature=0.2,

        max_tokens=1200,

        timeout=60,

        messages=[

            {
                "role": "user",

                "content": PROMPT
            }
        ]
    )

    raw_text = (
        response
        .choices[0]
        .message
        .content
    )

except Exception as e:

    print("\n🔴 GROQ FAILED")

    print(e)

    exit()

# =====================================================
# CLEAN RAW TEXT
# =====================================================

raw_text = raw_text.replace(
    "```json",
    ""
)

raw_text = raw_text.replace(
    "```",
    ""
)

raw_text = raw_text.strip()

json_start = raw_text.find("{")

json_end = raw_text.rfind("}")

if json_start != -1 and json_end != -1:

    raw_text = raw_text[
        json_start : json_end + 1
    ]

# =====================================================
# EMPTY RESPONSE SAFETY
# =====================================================

if raw_text == "":

    print("\n🔴 EMPTY AI RESPONSE")

    exit()

# =====================================================
# RAW AI OUTPUT
# =====================================================

print("\n" + "=" * 60)
print("RAW AI OUTPUT")
print("=" * 60)

print(raw_text)

# =====================================================
# PARSE JSON
# =====================================================

try:

    ai_data = json.loads(
        raw_text
    )

    print("\n✅ JSON parsed")

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

print(

    json.dumps(

        cleaned,

        indent=4
    )
)

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
# SAFETY FLAG
# =====================================================

safe = True

# =====================================================
# VALIDATION BLOCK
# =====================================================

if not report["valid"]:

    safe = False

# =====================================================
# EMPTY TITLE BLOCK
# =====================================================

if cleaned.get("title", "") == "":

    print("\n🔴 EMPTY TITLE")

    safe = False

# =====================================================
# DUPLICATE CHECK
# =====================================================

duplicates = find_duplicates(

    cleaned.get("title", ""),

    existing_titles
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

        # =============================================
        # ONLY BLOCK EXACT DUPLICATES
        # =============================================

        if dup["type"] == "exact":

            safe = False

# =====================================================
# FINAL RESULT
# =====================================================

print("\n" + "=" * 60)
print("FINAL STATUS")
print("=" * 60)

if safe:

    print("🟢 SAFE FOR INGESTION")

else:

    print("🔴 INGESTION BLOCKED")

# =====================================================
# FINAL CLEAN JSON
# =====================================================

print("\n" + "=" * 60)
print("FINAL CLEAN JSON")
print("=" * 60)

print(

    json.dumps(

        cleaned,

        indent=4
    )
)

print("\n✅ INGESTION TEST COMPLETE")
