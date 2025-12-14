import google.generativeai as genai
from utils.config import GEMINI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

class GeminiClient:
    def __init__(self, model="gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt):
        return self.model.generate_content(prompt).text
