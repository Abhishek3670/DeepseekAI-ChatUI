from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ChatMessage:
    content: str
    timestamp: datetime
    is_user: bool
    attachment_path: Optional[str] = None
