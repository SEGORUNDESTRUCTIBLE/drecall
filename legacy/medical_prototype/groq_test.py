# =====================================================
# GROQ TEST
# =====================================================

print("STARTING GROQ TEST")

# =====================================================
# IMPORTS
# =====================================================

from groq import Groq

from config import GROQ_API_KEY

print("✅ Imports successful")

# =====================================================
# CLIENT
# =====================================================

client = Groq(

    api_key=GROQ_API_KEY
)

print("✅ Groq client initialized")

# =====================================================
# PROMPT
# =====================================================

PROMPT = """

Convert this medical mistake into a short JSON.

Mistake:
Distichiasis vs trichiasis confusion.

"""

# =====================================================
# RUN MODEL
# =====================================================

print("\nRUNNING MODEL...\n")

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

    print("✅ RESPONSE RECEIVED\n")

    print(raw_text)

except Exception as e:

    print("\n🔴 GROQ FAILED")

    print(e)

print("\nTEST COMPLETE")