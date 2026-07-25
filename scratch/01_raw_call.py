import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["GOOGLE_API_KEY"]

from google import genai

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input="Explain how AI works in a few words"
)
print(interaction.output_text)
