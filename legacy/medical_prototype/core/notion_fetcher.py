# =====================================================
# NOTION FETCHER
# FULLY IMPROVED VERSION
# =====================================================

print("STARTING NOTION FETCHER")

# =====================================================
# IMPORTS
# =====================================================

from notion_client import Client

from config import (

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
# FETCH EXISTING TITLES
# =====================================================

def fetch_existing_titles():

    print("\n" + "=" * 60)
    print("FETCHING EXISTING TITLES")
    print("=" * 60)

    titles = []

    has_more = True

    next_cursor = None

    total_pages = 0

    # =================================================
    # PAGINATION LOOP
    # =================================================

    while has_more:

        try:

            response = notion.data_sources.query(

                data_source_id=DATA_SOURCE_ID,

                start_cursor=next_cursor
            )

        except Exception as e:

            print("\n🔴 DATABASE QUERY FAILED")

            print(e)

            return []

        results = response["results"]

        total_pages += len(results)

        print(f"\n📄 Fetched {len(results)} pages")

        # =================================================
        # EXTRACT TITLES
        # =================================================

        for page in results:

            try:

                title_property = (

                    page["properties"]
                    ["Question / Mistake"]
                    ["title"]
                )

                # =========================================
                # EMPTY TITLE SAFETY
                # =========================================

                if len(title_property) == 0:

                    continue

                title = title_property[0][
                    "plain_text"
                ].strip()

                # =========================================
                # EMPTY STRING SAFETY
                # =========================================

                if title == "":

                    continue

                titles.append(title)

            except Exception as e:

                print(

                    f"⚠ Title fetch error: {e}"
                )

        # =================================================
        # PAGINATION
        # =================================================

        has_more = response["has_more"]

        next_cursor = response.get(
            "next_cursor"
        )

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    titles = list(set(titles))

    # =====================================================
    # SORT TITLES
    # =====================================================

    titles.sort()

    # =====================================================
    # FINAL REPORT
    # =====================================================

    print("\n" + "=" * 60)
    print("FETCH COMPLETE")
    print("=" * 60)

    print(f"\n✅ Total pages scanned: {total_pages}")

    print(f"✅ Unique titles loaded: {len(titles)}")

    return titles

# =====================================================
# TEST RUN
# =====================================================

if __name__ == "__main__":

    titles = fetch_existing_titles()

    print("\n" + "=" * 60)
    print("EXISTING TITLES")
    print("=" * 60)

    for title in titles:

        print("-", title)

    print("\n✅ FETCHER TEST COMPLETE")