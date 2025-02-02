import os
from pathlib import Path

class Config:
    MODEL_PATH = r"C:\Users\Abhishek\.ollama\models\manifests\registry.ollama.ai\library\deepseek-r1\7b"
    UPLOAD_FOLDER = str(Path('uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    SECRET_KEY = os.urandom(24)
