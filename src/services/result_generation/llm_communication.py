import os

from google import genai
from google.genai import types


class LLMCommunication:
    def __init__(self):
        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GENAI_API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "Missing Gemini API key. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in the app environment."
            )

        self.client = genai.Client(api_key=api_key)

    def request(self, prompt: str):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0
            )
        )
        return response.text
