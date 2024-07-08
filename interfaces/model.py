class ModelInterface:

    def generate_response(self, question: str) -> str:
        
        raise NotImplementedError("Subclasses must implement this method.")
