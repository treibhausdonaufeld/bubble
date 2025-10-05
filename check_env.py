import os

from django.conf import settings

print(f"OPENAI_API_KEY exists: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"Settings loaded: {hasattr(settings, 'OPENAI_API_KEY')}")

if hasattr(settings, "OPENAI_API_KEY"):
    key = getattr(settings, "OPENAI_API_KEY", "")
    print(f"Settings OPENAI_API_KEY: {key[:10]}... (length: {len(key)})")
else:
    print("OPENAI_API_KEY not in Django settings")

# Try to import openai
try:
    import openai

    print("✓ OpenAI module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import openai: {e}")
