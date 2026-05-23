"""Quick check that the Gemini API key works.

Run:  python test_api.py
Expect: one short sentence printed back.
"""
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one short sentence.",
)

print(response.text)
