import requests
from interfaces.model import ModelInterface
import os

class OpenaiModel(ModelInterface):

    def __init__(self, api_key: str):
        
        self.api_key = api_key

        # Get the model, else use default - gpt-3.5-turbo-instruct.
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo-instruct')

        # Max tokens that OpenAI should use.
        self.word_limit = 100

    def generate_response(self, question: str) -> str:
        
        try:
            response = requests.post(
                f'https://api.openai.com/v1/engines/{self.model}/completions',
                json={
                    'prompt': question,
                    'max_tokens': self.word_limit * 5
                },
                headers={
                    'Authorization': f'Bearer {self.api_key}'
                }
            )

            # Raises an HTTPError for bad responses.
            response.raise_for_status()

            return response.json()['choices'][0]['text'].strip()

        except requests.exceptions.HTTPError as http_err:
            
            # Handle HTTP errors separately from other exceptions
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            
            # Handle other errors like connection problems, request timeouts, etc.
            print(f"An error occurred: {err}")
        return None
