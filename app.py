from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

# Data structure for chat messages
@dataclass
class ChatMessage:
    content: str
    timestamp: datetime
    is_user: bool
    attachment_path: Optional[str] = None

class ChatApp:
    def __init__(self, model_path: str, upload_folder: str):
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = upload_folder
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        self.app.secret_key = os.urandom(24)  # For session management
        
        # Configure logging
        logging.basicConfig(
            filename='chat_app.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize model
        try:
            self.model = self._initialize_model(model_path)
        except Exception as e:
            self.logger.error(f"Failed to initialize model: {str(e)}")
            raise
        
        # Store chat histories in memory (consider using a database for production)
        self.chat_histories: Dict[str, List[ChatMessage]] = {}
        
        # Register routes
        self._register_routes()
        
        # Create upload folder if it doesn't exist
        Path(upload_folder).mkdir(parents=True, exist_ok=True)

    def _initialize_model(self, model_path: str):
        """Initialize the Deepseek-R1 model with error handling."""
        try:
            return load_model(model_path)
        except Exception as e:
            self.logger.error(f"Model initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def _register_routes(self):
        # Main routes
        self.app.route('/')(self.index)
        self.app.route('/chat/<chat_id>')(self.chat)
        self.app.route('/send_message', methods=['POST'])(self.send_message)
        self.app.route('/upload_attachment', methods=['POST'])(self.upload_attachment)
        
        # Error handlers
        self.app.errorhandler(404)(self.page_not_found)
        self.app.errorhandler(500)(self.internal_server_error)

    def index(self):
        """Home page route."""
        return render_template('index.html')

    def chat(self, chat_id: str):
        """Individual chat page route."""
        if chat_id not in self.chat_histories:
            self.chat_histories[chat_id] = []
        return render_template(
            'chat.html',
            chat_id=chat_id,
            chat_history=self.chat_histories[chat_id]
        )

    def send_message(self):
        """Handle sending messages and getting model responses."""
        try:
            chat_id = request.form['chat_id']
            message = request.form['message']
            
            if not message.strip():
                return jsonify({
                    'status': 'error',
                    'message': 'Empty message'
                }), 400

            # Create user message
            user_message = ChatMessage(
                content=message,
                timestamp=datetime.now(),
                is_user=True
            )
            
            # Generate model response
            try:
                response = self.model.generate_response(message)
                model_message = ChatMessage(
                    content=response,
                    timestamp=datetime.now(),
                    is_user=False
                )
            except Exception as e:
                self.logger.error(f"Model response generation failed: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to generate response'
                }), 500

            # Store messages in chat history
            if chat_id not in self.chat_histories:
                self.chat_histories[chat_id] = []
            self.chat_histories[chat_id].extend([user_message, model_message])

            return jsonify({
                'status': 'success',
                'response': response,
                'timestamp': model_message.timestamp.isoformat()
            })

        except Exception as e:
            self.logger.error(f"Message handling failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500

    def upload_attachment(self):
        """Handle file uploads with security checks."""
        try:
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file part'
                }), 400

            file = request.files['file']
            if not file.filename:
                return jsonify({
                    'status': 'error',
                    'message': 'No selected file'
                }), 400

            # Validate file type (add more as needed)
            allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
            if not self._allowed_file(file.filename, allowed_extensions):
                return jsonify({
                    'status': 'error',
                    'message': 'File type not allowed'
                }), 400

            filename = secure_filename(file.filename)
            file_path = Path(self.app.config['UPLOAD_FOLDER']) / filename
            
            # Save file with error handling
            try:
                file.save(file_path)
            except Exception as e:
                self.logger.error(f"File save failed: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save file'
                }), 500

            return jsonify({
                'status': 'success',
                'filename': filename,
                'path': str(file_path)
            })

        except Exception as e:
            self.logger.error(f"File upload failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500

    @staticmethod
    def _allowed_file(filename: str, allowed_extensions: set) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def page_not_found(self, e):
        """404 error handler."""
        return render_template('404.html'), 404

    def internal_server_error(self, e):
        """500 error handler."""
        return render_template('500.html'), 500

    def run(self, **kwargs):
        """Run the Flask application."""
        self.app.run(**kwargs)

if __name__ == '__main__':
    # Configuration
    MODEL_PATH = r"C:\Users\%USERNAME%\.ollama\models\manifests\registry.ollama.ai\library\deepseek-r1\7b"
    UPLOAD_FOLDER = Path('uploads')
    
    # Initialize and run application
    try:
        chat_app = ChatApp(MODEL_PATH, str(UPLOAD_FOLDER))
        chat_app.run(debug=True)
    except Exception as e:
        print(f"Failed to start application: {str(e)}")