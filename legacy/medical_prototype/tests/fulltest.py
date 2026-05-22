# =====================================================
# FULL SYSTEM RE-TEST
# FINAL PRE-GEMINI VALIDATION
# =====================================================

print("STARTING FINAL SYSTEM TEST")

# =====================================================
# IMPORTS
# =====================================================

from normalizers import normalize_data

print("✅ normalizers imported")

from validators import full_validation

print("✅ validators imported")

from duplicate_detector import (
    find_duplicates,
    has_duplicate
)

print("✅ duplicate detector imported")

# =====================================================
# EXISTING DATABASE TITLES
# =====================================================

existing_titles = [

    "Distichiasis vs Trichiasis confusion",

    "Papilledema vs papillitis",

    "Horner syndrome lesion localization",

    "Retinal artery occlusion",

    "Third nerve palsy localization"
]

# =====================================================
# TEST CASES
# =====================================================

TEST_CASES = [

    # =================================================
    # SHOULD PASS
    # =================================================

    {

        "name":
            "SAFE VALID INPUT",

        "expected":
            "SAFE",

        "data": {

            "title":
                "Wilson disease MRI findings",

            "subject":
                "medicine",

            "system":
                "cns",

            "topic":
                "basal ganglia",

            "error_type":
                "guess",

            "core_concept":
                "Copper accumulation.",

            "why_confusing":
                "Can mimic hepatic disease.",

            "memory_hook":
                "Face of giant panda.",

            "trap":
                "Low ceruloplasmin.",

            "exam_pearl":
                "Kayser Fleischer ring.",

            "one_liner_revision":
                "Wilson affects liver + CNS.",

            "retest_question":
                "Most common MRI finding?",

            "pattern_type":
                "Image Based",

            "tags": [

                "high-yield",
                "revision"
            ]
        }
    },

    # =================================================
    # MISSING CORE CONCEPT
    # =================================================

    {

        "name":
            "MISSING CORE CONCEPT",

        "expected":
            "BLOCK",

        "data": {

            "title":
                "Papilledema confusion",

            "subject":
                "ophthal",

            "system":
                "eye",

            "topic":
                "fundus",

            "error_type":
                "guess",

            "why_confusing":
                "Disc edema confusion.",

            "memory_hook":
                "Blurred margins.",

            "trap":
                "Visual acuity preserved.",

            "exam_pearl":
                "Raised ICP.",

            "one_liner_revision":
                "Papilledema = raised ICP.",

            "retest_question":
                "Which condition preserves VA initially?",

            "pattern_type":
                "Image Based",

            "tags": [

                "high-yield"
            ]
        }
    },

    # =================================================
    # INVALID SUBJECT
    # =================================================

    {

        "name":
            "INVALID SUBJECT",

        "expected":
            "BLOCK",

        "data": {

            "title":
                "Retinal artery occlusion",

            "subject":
                "randomsubject",

            "system":
                "eye",

            "topic":
                "retina",

            "error_type":
                "guess",

            "core_concept":
                "Cherry red spot.",

            "why_confusing":
                "Can confuse with CRVO.",

            "memory_hook":
                "Pale retina.",

            "trap":
                "Sudden painless loss.",

            "exam_pearl":
                "Emergency.",

            "one_liner_revision":
                "CRAO = pale retina.",

            "retest_question":
                "Most common embolic source?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [

                "high-yield"
            ]
        }
    },

    # =================================================
    # EXACT DUPLICATE
    # =================================================

    {

        "name":
            "EXACT DUPLICATE",

        "expected":
            "BLOCK",

        "data": {

            "title":
                "Distichiasis vs Trichiasis confusion",

            "subject":
                "ophthal",

            "system":
                "eye",

            "topic":
                "eyelid",

            "error_type":
                "guess",

            "core_concept":
                "Extra lash row.",

            "why_confusing":
                "Looks similar.",

            "memory_hook":
                "Distich = double.",

            "trap":
                "Posterior to gray line.",

            "exam_pearl":
                "Image based.",

            "one_liner_revision":
                "Meibomian gland origin.",

            "retest_question":
                "Posterior lashes?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [

                "high-yield"
            ]
        }
    }
]

# =====================================================
# START TESTING
# =====================================================

print("\n" + "=" * 60)
print("RUNNING FINAL BACKEND TEST")
print("=" * 60)

passed = 0
blocked = 0

# =====================================================
# LOOP TESTS
# =====================================================

for i, test in enumerate(TEST_CASES):

    print("\n" + "-" * 60)

    print(f"TEST {i+1}: {test['name']}")

    print("-" * 60)

    raw_data = test["data"]

    # =================================================
    # NORMALIZATION
    # =================================================

    cleaned = normalize_data(
        raw_data
    )

    # =================================================
    # VALIDATION
    # =================================================

    report = full_validation(
        cleaned
    )

    # =================================================
    # DUPLICATE CHECK
    # =================================================

    duplicates = find_duplicates(

        cleaned["title"],
        existing_titles,
        threshold=0.80
    )

    # =================================================
    # FINAL DECISION
    # =================================================

    safe = True

    if not report["valid"]:

        safe = False

    if has_duplicate(

        cleaned["title"],
        existing_titles,
        threshold=0.80
    ):

        safe = False

    # =================================================
    # OUTPUT
    # =================================================

    print("\nNORMALIZED DATA:")

    print(cleaned)

    print("\nVALIDATION REPORT:")

    for key, value in report.items():

        print(f"{key}: {value}")

    print("\nDUPLICATE CHECK:")

    if len(duplicates) == 0:

        print("✅ No duplicates")

    else:

        for dup in duplicates:

            print(

                f"- {dup['title']} "
                f"({dup['type']}, "
                f"{dup['similarity']})"
            )

    print("\nFINAL STATUS:")

    if safe:

        print("🟢 SAFE FOR INGESTION")

        passed += 1

    else:

        print("🔴 INGESTION BLOCKED")

        blocked += 1

    # =================================================
    # EXPECTATION CHECK
    # =================================================

    expected = test["expected"]

    actual = "SAFE" if safe else "BLOCK"

    print(f"\nEXPECTED: {expected}")

    print(f"ACTUAL: {actual}")

    if expected == actual:

        print("✅ TEST PASSED")

    else:

        print("❌ TEST FAILED")

# =====================================================
# FINAL SUMMARY
# =====================================================

print("\n" + "=" * 60)
print("FINAL SYSTEM SUMMARY")
print("=" * 60)

print(f"\nSAFE TESTS: {passed}")

print(f"BLOCKED TESTS: {blocked}")

print("\n✅ PRE-GEMINI BACKEND VALIDATION COMPLETE")
