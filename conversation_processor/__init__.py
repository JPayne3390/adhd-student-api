"""
Conversation Processor - Batch processing system for AI conversation exports.

Transforms raw ChatGPT/Claude exports into structured, Notion-ready JSON data.
"""

from .processor import ConversationProcessor
from .schemas import Conversation, Chunk, Message

__version__ = "1.0.0"
__all__ = ["ConversationProcessor", "Conversation", "Chunk", "Message"]
