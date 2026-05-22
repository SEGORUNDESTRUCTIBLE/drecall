# =====================================================
# NORMALIZER TEST
# =====================================================

from normalizers import *

# =====================================================
# TEST CASES
# =====================================================

TEST_CASES = [

    {
        "name": "SUBJECT NORMALIZATION",

        "input": "ophthal",

        "function": normalize_subject
    },

    {
        "name": "SYSTEM NORMALIZATION",

        "input": "cardio",

        "function": normalize_system
    },

    {
        "name": "ERROR TYPE NORMALIZATION",

        "input": "guess",

        "function": normalize_error_type
    },

    {
        "name": "TAG CLEANING",

        "input": [

            "high-yield",
            "abc",
            "revision",
            "revision",
            "random",
            "spotter"
        ],

        "function": normalize_tags
    }
]

# =====================================================
# RUN SIMPLE TESTS
# =====================================================

print("\n" + "=" * 60)
print("RUNNING NORMALIZER TESTS")
print("=" * 60)

for i, test in enumerate(TEST_CASES):

    print("\n" + "-" * 60)

    print(f"TEST {i+1}: {test['name']}")

    print("-" * 60)

    print(f"\nINPUT:\n{test['input']}")

    result = test["function"](test["input"])

    print(f"\nOUTPUT:\n{result}")

# =====================================================
# FULL DATA NORMALIZATION TEST
# =====================================================

print("\n" + "=" * 60)
print("FULL DATA NORMALIZATION TEST")
print("=" * 60)

RAW_AI_DATA = {

    "title":
        "Distichiasis confusion",

    "subject":
        "ophthal",

    "system":
        "cardio",

    "error_type":
        "guess",

    "tags": [

        "high-yield",
        "revision",
        "abc",
        "spotter",
        "spotter"
    ]
}

print("\nRAW DATA:\n")

print(RAW_AI_DATA)

# =====================================================
# NORMALIZE
# =====================================================

CLEANED = normalize_data(RAW_AI_DATA)

print("\nCLEANED DATA:\n")

print(CLEANED)

# =====================================================
# DONE
# =====================================================

print("\n" + "=" * 60)
print("NORMALIZATION TEST COMPLETE")
print("=" * 60)