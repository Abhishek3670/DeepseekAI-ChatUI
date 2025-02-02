import logging
from ollama import Client

class OllamaClient:
    def __init__(self, model_path: str):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.client = self._initialize_client()
        
    def _check_ollama_service(self):
        """Check if Ollama service is running."""
        try:
            client = Client()
            client.list()
            return True
        except Exception as e:
            self.logger.error(f"Ollama service check failed: {str(e)}")
            raise RuntimeError(
                "Ollama service is not running. Please start it using 'ollama serve' command."
            )

    def _initialize_client(self):
        """Initialize Ollama client with error handling."""
        try:
            self._check_ollama_service()
            
            client = Client()
            model_name = "deepseek-r1:7b"
            
            # Check available models
            models = client.list()
            self.logger.info(f"Available models: {models}")
            
            try:
                client.show(model_name)
                self.logger.info(f"Model {model_name} found")
            except Exception:
                self.logger.info(f"Loading model from path: {self.model_path}")
                client.create(model_name, path=self.model_path)
                self.logger.info(f"Model {model_name} loaded successfully")
                
            return client
                
        except ImportError:
            self.logger.error("Ollama client not installed")
            raise RuntimeError("Please install ollama client: pip install ollama")
        except Exception as e:
            self.logger.error(f"Client initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to initialize client: {str(e)}")

    def generate_response(self, message: str) -> str:
        """Generate response using the model."""
        try:
            response = self.client.chat(
                model='deepseek-r1:7b',
                messages=[{'role': 'user', 'content': message}]
            )
            return response['message']['content']
        except Exception as e:
            self.logger.error(f"Response generation failed: {str(e)}")
            raise
