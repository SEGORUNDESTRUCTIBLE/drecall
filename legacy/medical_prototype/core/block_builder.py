# =====================================================
# BLOCK BUILDER
# FINAL PRODUCTION VERSION
# =====================================================

# =====================================================
# CREATE RICH TEXT
# =====================================================

def rich_text(content):

    return [

        {
            "type": "text",

            "text": {

                "content": str(content)
            }
        }
    ]

# =====================================================
# CREATE PARAGRAPH
# =====================================================

def create_paragraph(text):

    return {

        "object": "block",

        "type": "paragraph",

        "paragraph": {

            "rich_text": rich_text(text)
        }
    }

# =====================================================
# CREATE HEADING
# =====================================================

def create_heading(text):

    return {

        "object": "block",

        "type": "heading_2",

        "heading_2": {

            "rich_text": rich_text(text)
        }
    }

# =====================================================
# CREATE TOGGLE
# =====================================================

def create_toggle(

    heading,
    content
):

    return {

        "object": "block",

        "type": "toggle",

        "toggle": {

            "rich_text": rich_text(heading),

            "children": [

                create_paragraph(content)
            ]
        }
    }

# =====================================================
# BUILD REVISION BLOCKS
# =====================================================

def build_revision_blocks(data):

    blocks = []

    # =================================================
    # CORE CONCEPT
    # =================================================

    blocks.append(

        create_toggle(

            "📌 CORE CONCEPT",

            data.get(
                "core_concept",
                ""
            )
        )
    )

    # =================================================
    # WHY CONFUSING
    # =================================================

    blocks.append(

        create_toggle(

            "❌ WHY CONFUSING",

            data.get(
                "why_confusing",
                ""
            )
        )
    )

    # =================================================
    # MEMORY HOOK
    # =================================================

    blocks.append(

        create_toggle(

            "🧠 MEMORY HOOK",

            data.get(
                "memory_hook",
                ""
            )
        )
    )

    # =================================================
    # TRAP
    # =================================================

    blocks.append(

        create_toggle(

            "🚨 TRAP",

            data.get(
                "trap",
                ""
            )
        )
    )

    # =================================================
    # EXAM PEARL
    # =================================================

    blocks.append(

        create_toggle(

            "⭐ EXAM PEARL",

            data.get(
                "exam_pearl",
                ""
            )
        )
    )

    # =================================================
    # CLASSIC FINDING
    # =================================================

    if data.get(
        "classic_finding",
        ""
    ) != "":

        blocks.append(

            create_toggle(

                "🖼 CLASSIC FINDING",

                data.get(
                    "classic_finding",
                    ""
                )
            )
        )

    # =================================================
    # DIFFERENTIALS
    # =================================================

    if data.get(
        "differentials",
        ""
    ) != "":

        blocks.append(

            create_toggle(

                "⚖ DIFFERENTIALS",

                data.get(
                    "differentials",
                    ""
                )
            )
        )

    # =================================================
    # IMAGE DIAGNOSIS
    # =================================================

    if data.get(
        "image_diagnosis",
        ""
    ) != "":

        blocks.append(

            create_toggle(

                "🩻 IMAGE DIAGNOSIS",

                data.get(
                    "image_diagnosis",
                    ""
                )
            )
        )

    # =================================================
    # ONE LINER
    # =================================================

    blocks.append(

        create_toggle(

            "⚡ ONE-LINER REVISION",

            data.get(
                "one_liner_revision",
                ""
            )
        )
    )

    # =================================================
    # RETEST QUESTION
    # =================================================

    blocks.append(

        create_toggle(

            "🔄 RETEST QUESTION",

            data.get(
                "retest_question",
                ""
            )
        )
    )

    # =================================================
    # AI NOTE
    # =================================================

    if data.get(
        "ai_note",
        ""
    ) != "":

        blocks.append(

            create_toggle(

                "🤖 AI NOTE",

                data.get(
                    "ai_note",
                    ""
                )
            )
        )

    return blocks