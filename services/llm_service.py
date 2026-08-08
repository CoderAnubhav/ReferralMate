from google import genai

from config import GEMINI_API_KEY


class LLMService:

    def __init__(self):

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

    def generate(self, prompt):

        response = self.client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt

        )

        return response.text.strip()