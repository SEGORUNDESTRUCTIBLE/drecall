from notion_client import Client

from config import (

    NOTION_TOKEN,

    DATA_SOURCE_ID
)

# =====================================================
# NOTION CLIENT
# =====================================================

notion = Client(

    auth=NOTION_TOKEN
)

# =====================================================
# RETRIEVE DATA SOURCE
# =====================================================

db = notion.data_sources.retrieve(

    DATA_SOURCE_ID
)

# =====================================================
# PRINT PROPERTIES
# =====================================================

print("\n" + "=" * 60)
print("DATA SOURCE PROPERTIES")
print("=" * 60)

for name, info in db["properties"].items():

    print(f"\n{name}")

    print(
        f"TYPE: {info['type']}"
    )