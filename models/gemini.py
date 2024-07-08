import google.generativeai as genai
from interfaces.model import ModelInterface
import os

class GeminiModel(ModelInterface):

    def __init__(self, api_key: str):
        
        self.api_key = api_key
        self.model = os.getenv('GEMINI_MODEL')
        self.word_limit = 100
        
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            
            # Handle exceptions related to API configuration errors.
            print(f"Failed to configure Gemini API with provided API key: {e}")
            
            # Optionally, re-raise the exception if the application cannot recover.
            raise

    def generate_response(self, question: str) -> str:

        try:
            # Prepare the model instance.
            model = genai.GenerativeModel(self.model)

            # Get the content and return it.
            response = model.generate_content(f'Answer this question in {self.word_limit} words: ' + question)
            return response.text

        except Exception as e:
            
            # Handle exceptions related to the model generation process.
            print(f"Error generating response from Gemini model: {e}")
            
            # Optionally, re-raise the exception if the application cannot recover.
            raise
