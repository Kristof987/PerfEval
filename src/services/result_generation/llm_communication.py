from google import genai
from google.genai import types

class LLMCommunication:
    def __init__(self):
        self.client = genai.Client()

    def request(self, prompt: str):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0
            )
        )
        return response.text
