import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["GOOGLE_API_KEY"]

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=gemini-3.5-flash-lite"

