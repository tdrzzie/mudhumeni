import os
from typing import Callable, Dict, Union
from models.gemini import GeminiModel
from models.openai import OpenaiModel

class CommandHandler:

    def __init__(self):
        
        self.commands: Dict[str, Callable[[str], str]] = {
            "gemini": self.handle_gemini,
            "openai": self.handle_openai
        }
        self.models: Dict[str, Union[GeminiModel, OpenaiModel]] = {
            "gemini": GeminiModel(api_key=os.getenv('GEMINI_API_KEY')),
            "openai": OpenaiModel(api_key=os.getenv('OPENAI_API_KEY'))
        }

    def handle_command(self, command: str, message: str) -> str:
        
        handler = self.commands.get(command, self.handle_default)
        try:
            return handler(message)
        except Exception as e:
            # Log and handle any error that occurs during command handling.
            print(f"Error handling command '{command}': {e}")
            return "An error occurred while processing your command."

    def handle_gemini(self, message: str) -> str:
        
        model = self.models.get("gemini")
        if model:
            try:
                return model.generate_response(message)
            except Exception as e:
                print(f"Error generating response with Gemini model: {e}")
                return "An error occurred while generating a response."
        return "Gemini model is not available."

    def handle_openai(self, message: str) -> str:
        
        model = self.models.get("openai")
        if model:
            try:
                return model.generate_response(message)
            except Exception as e:
                print(f"Error generating response with OpenAI model: {e}")
                return "An error occurred while generating a response."
        return "OpenAI model is not available."

    def handle_default(self, message: str) -> str:
        
        return "Sorry, I didn't understand that command."
