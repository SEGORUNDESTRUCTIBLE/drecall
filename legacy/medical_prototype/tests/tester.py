# =====================================================
# RAPID VALIDATION STRESS TEST
# =====================================================

from validators import full_validation

# =====================================================
# TEST CASES
# =====================================================

TEST_CASES = [

    # =================================================
    # PERFECT INPUT
    # =================================================

    {
        "name": "PERFECT INPUT",

        "data": {

            "title":
                "Distichiasis vs Trichiasis confusion",

            "subject":
                "Ophthalmology",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "core_concept":
                "Extra row of lashes posterior to gray line.",

            "why_confusing":
                "Confused with trichiasis.",

            "memory_hook":
                "DOUBLE lashes = distichiasis",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Associated with meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "Which disorder arises from meibomian glands?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [
                "high-yield",
                "image-based"
            ]
        }
    },

    # =================================================
    # EMPTY TITLE
    # =================================================

    {
        "name": "EMPTY TITLE",

        "data": {

            "title": "",

            "subject":
                "Ophthalmology",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "core_concept":
                "Extra row of lashes.",

            "why_confusing":
                "Confusion with trichiasis.",

            "memory_hook":
                "DOUBLE lashes",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "What arises from meibomian glands?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [
                "high-yield"
            ]
        }
    },

    # =================================================
    # MISSING CORE CONCEPT
    # =================================================

    {
        "name": "MISSING CORE CONCEPT",

        "data": {

            "title":
                "Distichiasis confusion",

            "subject":
                "Ophthalmology",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "why_confusing":
                "Confused with trichiasis.",

            "memory_hook":
                "DOUBLE lashes",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "What arises from meibomian glands?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [
                "high-yield"
            ]
        }
    },

    # =================================================
    # INVALID SUBJECT
    # =================================================

    {
        "name": "INVALID SUBJECT",

        "data": {

            "title":
                "Distichiasis confusion",

            "subject":
                "Ophthalologyyyyy",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "core_concept":
                "Extra row of lashes.",

            "why_confusing":
                "Confused with trichiasis.",

            "memory_hook":
                "DOUBLE lashes",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "What arises from meibomian glands?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [
                "high-yield"
            ]
        }
    },

    # =================================================
    # INVALID PATTERN TYPE
    # =================================================

    {
        "name": "INVALID PATTERN TYPE",

        "data": {

            "title":
                "Distichiasis confusion",

            "subject":
                "Ophthalmology",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "core_concept":
                "Extra row of lashes.",

            "why_confusing":
                "Confused with trichiasis.",

            "memory_hook":
                "DOUBLE lashes",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "What arises from meibomian glands?",

            "pattern_type":
                "RandomPattern",

            "tags": [
                "high-yield"
            ]
        }
    },

    # =================================================
    # GIANT TEXT
    # =================================================

    {
        "name": "GIANT TEXT",

        "data": {

            "title":
                "Distichiasis confusion",

            "subject":
                "Ophthalmology",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "core_concept":
                "A" * 10000,

            "why_confusing":
                "Confused with trichiasis.",

            "memory_hook":
                "DOUBLE lashes",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "What arises from meibomian glands?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [
                "high-yield"
            ]
        }
    },

    # =================================================
    # INVALID TAGS
    # =================================================

    {
        "name": "INVALID TAGS",

        "data": {

            "title":
                "Distichiasis confusion",

            "subject":
                "Ophthalmology",

            "system":
                "Eye",

            "topic":
                "Eyelid disorders",

            "error_type":
                "Image Confusion",

            "core_concept":
                "Extra row of lashes.",

            "why_confusing":
                "Confused with trichiasis.",

            "memory_hook":
                "DOUBLE lashes",

            "trap":
                "Posterior to gray line",

            "exam_pearl":
                "Meibomian glands",

            "one_liner_revision":
                "Extra row = distichiasis",

            "retest_question":
                "What arises from meibomian glands?",

            "pattern_type":
                "Clinical Spotter",

            "tags": [
                "nonsense",
                "abc",
                "high-yield"
            ]
        }
    }
]

# =====================================================
# RUN TESTS
# =====================================================

print("\n" + "=" * 60)
print("RAPID VALIDATION STRESS TEST")
print("=" * 60)

passed = 0
failed = 0

# =====================================================
# LOOP
# =====================================================

for i, test in enumerate(TEST_CASES):

    print("\n" + "-" * 60)

    print(f"TEST {i+1}: {test['name']}")

    print("-" * 60)

    report = full_validation(test["data"])

    for key, value in report.items():

        print(f"{key}: {value}")

    # ================================================
    # RESULT
    # ================================================

    if report["valid"]:

        print("\n🟢 PASSED")

        passed += 1

    else:

        print("\n🔴 REJECTED")

        failed += 1

# =====================================================
# FINAL SUMMARY
# =====================================================

print("\n" + "=" * 60)
print("FINAL TEST SUMMARY")
print("=" * 60)

print(f"\nPASSED : {passed}")
print(f"REJECTED : {failed}")

print("\nValidation stress testing complete.")