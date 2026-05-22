# =====================================================
# DUPLICATE DETECTOR
# =====================================================

from difflib import SequenceMatcher

# =====================================================
# CLEAN TITLE
# =====================================================

def clean_title(title):

    if title is None:

        return ""

    return (
        str(title)
        .strip()
        .lower()
    )

# =====================================================
# TEXT SIMILARITY
# =====================================================

def similarity(a, b):

    a = clean_title(a)

    b = clean_title(b)

    if a == "" or b == "":

        return 0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()

# =====================================================
# EXACT DUPLICATE
# =====================================================

def is_exact_duplicate(title1, title2):

    return (
        clean_title(title1)
        ==
        clean_title(title2)
    )

# =====================================================
# SIMILAR DUPLICATE
# =====================================================

def is_similar_duplicate(

    title1,
    title2,
    threshold=0.80
):

    score = similarity(
        title1,
        title2
    )

    return score >= threshold

# =====================================================
# FIND DUPLICATES
# =====================================================

def find_duplicates(

    new_title,
    existing_titles,
    threshold=0.80
):

    duplicates = []

    for old_title in existing_titles:

        # =============================================
        # EXACT DUPLICATE
        # =============================================

        if is_exact_duplicate(
            new_title,
            old_title
        ):

            duplicates.append({

                "title": old_title,

                "type": "exact",

                "similarity": 1.0
            })

            continue

        # =============================================
        # SIMILAR DUPLICATE
        # =============================================

        score = similarity(
            new_title,
            old_title
        )

        if score >= threshold:

            duplicates.append({

                "title": old_title,

                "type": "similar",

                "similarity": round(score, 2)
            })

    duplicates.sort(

        key=lambda x: x["similarity"],

        reverse=True
    )

    return duplicates

# =====================================================
# HAS DUPLICATE
# =====================================================

def has_duplicate(

    new_title,
    existing_titles,
    threshold=0.80
):

    duplicates = find_duplicates(

        new_title,
        existing_titles,
        threshold
    )

    return len(duplicates) > 0
