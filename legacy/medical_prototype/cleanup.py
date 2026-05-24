# =====================================================
# NOTION DATABASE CLEANUP SCRIPT
# DELETE REDUNDANT PROPERTIES
# =====================================================

print("STARTING DATABASE CLEANUP")

# =====================================================
# IMPORTS
# =====================================================

from notion_client import Client

from legacy_config import (

    NOTION_TOKEN,

    DATA_SOURCE_ID
)

print("✅ Imports successful")

# =====================================================
# NOTION CLIENT
# =====================================================

notion = Client(

    auth=NOTION_TOKEN
)

print("✅ Notion initialized")

# =====================================================
# DELETE / ARCHIVE PROPERTIES
# =====================================================

properties_to_remove = [

    # =============================================
    # REDUNDANT
    # =============================================

    "Last Revised",

    "Next Revision",

    # =============================================
    # OPTIONAL
    # Uncomment if desired
    # =============================================

    # "Gemini Summary",
]

# =====================================================
# GET CURRENT DATABASE
# =====================================================

print("\n" + "=" * 60)
print("FETCHING DATABASE")
print("=" * 60)

try:

    database = notion.data_sources.retrieve(

        data_source_id=DATA_SOURCE_ID
    )

    print("✅ Database fetched")

except Exception as e:

    print("\n🔴 FAILED TO FETCH DATABASE")

    print(e)

    exit()

# =====================================================
# CURRENT PROPERTIES
# =====================================================

current_properties = database["properties"]

print("\nCURRENT PROPERTIES:")

for prop in current_properties:

    print("-", prop)

# =====================================================
# BUILD UPDATE PAYLOAD
# =====================================================

update_payload = {}

for prop_name in properties_to_remove:

    if prop_name in current_properties:

        update_payload[prop_name] = None

        print(f"\n🗑 MARKED FOR REMOVAL: {prop_name}")

    else:

        print(f"\n⚠ NOT FOUND: {prop_name}")

# =====================================================
# NOTHING TO REMOVE
# =====================================================

if len(update_payload) == 0:

    print("\n⚠ NOTHING TO REMOVE")

    exit()

# =====================================================
# UPDATE DATABASE
# =====================================================

print("\n" + "=" * 60)
print("UPDATING DATABASE")
print("=" * 60)

try:

    notion.data_sources.update(

        data_source_id=DATA_SOURCE_ID,

        properties=update_payload
    )

    print("\n✅ DATABASE CLEANUP COMPLETE")

except Exception as e:

    print("\n🔴 DATABASE UPDATE FAILED")

    print(e)