from google import genai

class LLMCommunication:
    def __init__(self):
        self.client = genai.Client()

    def request(self, prompt: str):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
