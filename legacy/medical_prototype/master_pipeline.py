# =====================================================
# MASTER PIPELINE
# CONTINUOUS AI → NOTION INGESTION ENGINE
# =====================================================

print("STARTING MASTER PIPELINE")

# =====================================================
# IMPORTS
# =====================================================

import json

from groq import Groq

from config import (

    GROQ_API_KEY
)

from core.prompt_builder import (

    build_prompt
)

from core.normalizers import (

    normalize_data
)

from core.validators import (

    full_validation
)

from core.duplicate_detector import (

    find_duplicates

)

from notion_ingest import (

    create_notion_page
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

from core.notion_fetcher import (

    fetch_existing_titles
)

existing_titles = fetch_existing_titles()

print(f"✅ Loaded {len(existing_titles)} existing titles")


# =====================================================
# CONTINUOUS INGESTION LOOP
# =====================================================

while True:

    print("\n" + "=" * 60)
    print("PASTE QUESTION / MISTAKE")
    print("PRESS ENTER TWICE TO SUBMIT")
    print("TYPE EXIT TO CLOSE")
    print("=" * 60)

    lines = []

    empty_count = 0

    # =================================================
    # MULTILINE INPUT
    # =================================================

    while True:

        line = input()

        # =============================================
        # EXIT PROGRAM
        # =============================================

        if line.strip().lower() == "exit":

            print("\n👋 CLOSING PIPELINE")

            exit()

        # =============================================
        # DOUBLE ENTER DETECTION
        # =============================================

        if line.strip() == "":

            empty_count += 1

        else:

            empty_count = 0

        if empty_count >= 2:

            break

        lines.append(line)

    USER_INPUT = "\n".join(lines).strip()

    # =================================================
    # EMPTY INPUT SAFETY
    # =================================================

    if USER_INPUT == "":

        print("\n⚠ EMPTY INPUT")

        continue

    print("\n✅ INPUT RECEIVED")

    # =================================================
    # BUILD PROMPT
    # =================================================

    PROMPT = build_prompt(
        USER_INPUT
    )

    print("✅ Prompt built")

    # =================================================
    # RUN GROQ
    # =================================================

    print("\n" + "=" * 60)
    print("RUNNING GROQ")
    print("=" * 60)

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

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

        continue

    # =================================================
    # CLEAN JSON
    # =================================================

    raw_text = raw_text.replace(
        "```json",
        ""
    )

    raw_text = raw_text.replace(
        "```",
        ""
    ).strip()

    # =================================================
    # RAW AI OUTPUT
    # =================================================

    print("\n" + "=" * 60)
    print("RAW AI OUTPUT")
    print("=" * 60)

    print(raw_text)

    # =================================================
    # PARSE JSON
    # =================================================

    try:

        ai_data = json.loads(
            raw_text
        )

        print("\n✅ JSON parsed")

    except Exception as e:

        print("\n🔴 JSON PARSE FAILED")

        print(e)

        continue

    # =================================================
    # NORMALIZATION
    # =================================================

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

    # =================================================
    # VALIDATION
    # =================================================

    report = full_validation(
        cleaned
    )

    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)

    for key, value in report.items():

        print(f"{key}: {value}")

    # =================================================
    # DUPLICATE CHECK
    # =================================================

    duplicates = find_duplicates(

        cleaned["title"],

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

    # =================================================
    # FINAL SAFETY CHECK
    # =================================================

    safe = True

    if not report["valid"]:

        safe = False

    # =================================================
    # OPTIONAL STRICT DUPLICATE BLOCK
    # =================================================

    STRICT_DUPLICATE_BLOCK = False

    # =============================================
    # BLOCK ONLY EXACT DUPLICATES
    # =============================================

    for dup in duplicates:

        if dup["type"] == "exact":

            safe = False

            print(

                "\n🚫 EXACT DUPLICATE BLOCKED"
            )

            break
    # =================================================
    # FINAL STATUS
    # =================================================

    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    if safe:

        print("🟢 SAFE FOR INGESTION")

    else:

        print("🔴 INGESTION BLOCKED")

        continue

    # =================================================
    # RUN NOTION INGESTION
    # =================================================

    print("\n" + "=" * 60)
    print("RUNNING NOTION INGESTION")
    print("=" * 60)

    result = create_notion_page(
        cleaned
    )

    if result:

        print("\n✅ FULL PIPELINE COMPLETE")

        # =============================================
        # REFRESH DUPLICATE MEMORY
        # =============================================

        existing_titles.append(

            cleaned["title"]
        )

        print(

            f"✅ Added to duplicate memory: "

            f"{cleaned['title']}"
        )

    else:

        print("\n🔴 NOTION INGEST FAILED")

    # =================================================
    # FINAL CLEAN JSON
    # =================================================

    print("\n" + "=" * 60)
    print("FINAL CLEAN JSON")
    print("=" * 60)

    print(

        json.dumps(

            cleaned,

            indent=4
        )
    )

    # =================================================
    # READY FOR NEXT INPUT
    # =================================================

    print("\n🔄 READY FOR NEXT INPUT")
    
