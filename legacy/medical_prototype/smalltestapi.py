from google import genai

from config import GEMINI_API_KEY

print("STARTING MODEL LIST TEST")

# =====================================================
# CLIENT
# =====================================================

client = genai.Client(

    api_key=GEMINI_API_KEY
)

print("✅ Client initialized")

# =====================================================
# LIST MODELS
# =====================================================

print("\n" + "=" * 60)
print("AVAILABLE MODELS")
print("=" * 60)

try:

    for model in client.models.list():

        print(model.name)

except Exception as e:

    print("\n🔴 FAILED")

    print(e)

print("\nTEST COMPLETE")
