# =====================================================
# NOTION INGEST
# FINAL PRODUCTION VERSION
# =====================================================

print("STARTING NOTION INGESTION")

# =====================================================
# IMPORTS
# =====================================================

from notion_client import Client

from config import (

    NOTION_TOKEN,

    DATA_SOURCE_ID
)

from core.block_builder import (

    build_revision_blocks
)

print("✅ Imports successful")

# =====================================================
# NOTION CLIENT
# =====================================================

notion = Client(

    auth=NOTION_TOKEN
)

print("✅ Notion client initialized")

# =====================================================
# SAFE TEXT
# =====================================================

def safe_text(value):

    if value is None:

        return ""

    # Notion rich_text safety limit
    return str(value)[:1900]

# =====================================================
# CREATE RICH TEXT FIELD
# =====================================================

def rich_text_field(value):

    return {

        "rich_text": [

            {
                "text": {

                    "content":
                        safe_text(value)
                }
            }
        ]
    }

# =====================================================
# CREATE SELECT FIELD
# =====================================================

def select_field(value):

    return {

        "select": {

            "name":
                safe_text(value)
        }
    }

# =====================================================
# CREATE CHECKBOX FIELD
# =====================================================

def checkbox_field(value):

    return {

        "checkbox": bool(value)
    }

# =====================================================
# CREATE NUMBER FIELD
# =====================================================

def number_field(value):

    return {

        "number": value
    }

# =====================================================
# CREATE MULTI SELECT FIELD
# =====================================================

def multi_select_field(tags):

    if not isinstance(tags, list):

        tags = []

    return {

        "multi_select": [

            {
                "name": str(tag)
            }

            for tag in tags
        ]
    }

# =====================================================
# BUILD PROPERTIES
# =====================================================

def build_properties(data):

    properties = {

        # =============================================
        # TITLE
        # =============================================

        "Question / Mistake": {

            "title": [

                {
                    "text": {

                        "content":

                            safe_text(
                                data.get(
                                    "title",
                                    ""
                                )
                            )
                    }
                }
            ]
        },

        # =============================================
        # SELECTS
        # =============================================

        "Subject":

            select_field(

                data.get(
                    "subject",
                    ""
                )
            ),

        "System":

            select_field(

                data.get(
                    "system",
                    ""
                )
            ),

        "Error Type":

            select_field(

                data.get(
                    "error_type",
                    ""
                )
            ),

        "Pattern Type":

            select_field(

                data.get(
                    "pattern_type",
                    ""
                )
            ),

        # =============================================
        # TEXT FIELDS
        # =============================================

        "Topic":

            rich_text_field(

                data.get(
                    "topic",
                    ""
                )
            ),

        "Subtopic":

            rich_text_field(

                data.get(
                    "subtopic",
                    ""
                )
            ),

        "Core Concept":

            rich_text_field(

                data.get(
                    "core_concept",
                    ""
                )
            ),

        "Why Confusing":

            rich_text_field(

                data.get(
                    "why_confusing",
                    ""
                )
            ),

        "Memory Hook":

            rich_text_field(

                data.get(
                    "memory_hook",
                    ""
                )
            ),

        "Trap":

            rich_text_field(

                data.get(
                    "trap",
                    ""
                )
            ),

        "Exam Pearl":

            rich_text_field(

                data.get(
                    "exam_pearl",
                    ""
                )
            ),

        "Classic Finding":

            rich_text_field(

                data.get(
                    "classic_finding",
                    ""
                )
            ),

        "Differentials":

            rich_text_field(

                data.get(
                    "differentials",
                    ""
                )
            ),

        "One-Liner Revision":

            rich_text_field(

                data.get(
                    "one_liner_revision",
                    ""
                )
            ),

        "Retest Question":

            rich_text_field(

                data.get(
                    "retest_question",
                    ""
                )
            ),

        "Image Diagnosis":

            rich_text_field(

                data.get(
                    "image_diagnosis",
                    ""
                )
            ),

        "AI Note":

            rich_text_field(

                data.get(
                    "ai_note",
                    ""
                )
            ),

        # =============================================
        # TAGS
        # =============================================

        "Tags":

            multi_select_field(

                data.get(
                    "tags",
                    []
                )
            ),

        # =============================================
        # CHECKBOXES
        # =============================================

        "Reviewed":

            checkbox_field(False),

        "Starred":

            checkbox_field(False),

        "Volatile":

            checkbox_field(False),

        "Vector Indexed":

            checkbox_field(False),

        "High Yield":

            checkbox_field(

                "high-yield"
                in
                data.get(
                    "tags",
                    []
                )
            ),

        "Image Based":

            checkbox_field(

                "image-based"
                in
                data.get(
                    "tags",
                    []
                )
            ),

        "PYQ":

            checkbox_field(

                "pyq"
                in
                data.get(
                    "tags",
                    []
                )
            ),

        # =============================================
        # NUMBERS
        # =============================================

        "Wrong Count":

            number_field(1),

        "Revision Level":

            number_field(0)
    }

    return properties

# =====================================================
# CREATE NOTION PAGE
# =====================================================

def create_notion_page(data):

    print("\n" + "=" * 60)
    print("CREATING NOTION PAGE")
    print("=" * 60)

    # =================================================
    # BUILD PROPERTIES
    # =================================================

    properties = build_properties(
        data
    )

    # =================================================
    # BUILD BLOCKS
    # =================================================

    blocks = build_revision_blocks(
        data
    )

    # =================================================
    # CREATE PAGE
    # =================================================

    try:

        response = notion.pages.create(

            parent={

                "data_source_id":
                    DATA_SOURCE_ID
            },

            properties=properties,

            children=blocks
        )

        print("\n✅ PAGE CREATED")

        print("\nPAGE ID:")

        print(response["id"])

        print("\nPAGE URL:")

        print(response["url"])

        return response

    except Exception as e:

        print("\n🔴 NOTION INGEST FAILED")

        print(e)

        return None

# =====================================================
# TEST RUN
# =====================================================

if __name__ == "__main__":

    sample_data = {

        "title":
            "Distichiasis vs Trichiasis",

        "subject":
            "Ophthalmology",

        "system":
            "Eye",

        "topic":
            "Eyelid disorders",

        "subtopic":
            "Lash abnormalities",

        "error_type":
            "Confused similar concepts",

        "core_concept":
            "Accessory lash row vs misdirected lashes",

        "why_confusing":
            "Similar appearance of lashes",

        "memory_hook":
            "Meibomian glands",

        "trap":
            "Posterior to gray line",

        "exam_pearl":
            "Distichiasis has extra row of lashes",

        "classic_finding":
            "Accessory lashes in meibomian glands",

        "differentials":
            "Trichiasis vs distichiasis",

        "one_liner_revision":
            "Distichiasis has extra lash row, trichiasis has misdirected lashes",

        "retest_question":
            "What is the key difference between distichiasis and trichiasis?",

        "pattern_type":
            "Clinical Spotter",

        "image_diagnosis":
            "",

        "ai_note":
            "Focus on meibomian gland involvement",

        "tags": [

            "high-yield",

            "image-based",

            "confusion",

            "revision"
        ]
    }

    result = create_notion_page(
        sample_data
    )

    if result:

        print("\n✅ NOTION INGESTION COMPLETE")

    else:

        print("\n🔴 INGESTION FAILED")
