"""
Parsers for different AI conversation export formats.

Supports:
- ChatGPT JSON exports
- Claude JSON exports
- Claude Markdown exports
- Plain text files
- HTML files
"""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

from .schemas import Message, SourcePlatform


class BaseParser(ABC):
    """Abstract base class for conversation parsers."""

    @abstractmethod
    def can_parse(self, content: str, filename: str) -> bool:
        """Check if this parser can handle the given content."""
        pass

    @abstractmethod
    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse content into a list of messages."""
        pass


class ChatGPTParser(BaseParser):
    """Parser for ChatGPT JSON exports."""

    def can_parse(self, content: str, filename: str) -> bool:
        """Check if content is ChatGPT export format."""
        if not filename.endswith('.json'):
            return False
        try:
            data = json.loads(content)
            # ChatGPT exports have 'mapping' key with nested structure
            if isinstance(data, dict) and 'mapping' in data:
                return True
            # ChatGPT exports can also be a list of conversations
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict) and 'mapping' in data[0]:
                    return True
            return False
        except json.JSONDecodeError:
            return False

    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse ChatGPT JSON export."""
        data = json.loads(content)

        # Handle list of conversations (take first one)
        if isinstance(data, list):
            data = data[0]

        messages = []
        created_at = None

        # Extract creation time
        if 'create_time' in data:
            try:
                created_at = datetime.fromtimestamp(data['create_time'])
            except (ValueError, TypeError):
                pass

        # Parse mapping structure
        mapping = data.get('mapping', {})

        # Build message chain by following parent references
        message_nodes = []
        for node_id, node in mapping.items():
            message = node.get('message')
            if message and message.get('content', {}).get('parts'):
                content_parts = message['content']['parts']
                text_content = ' '.join(str(p) for p in content_parts if isinstance(p, str))

                if text_content.strip():
                    author_role = message.get('author', {}).get('role', 'unknown')
                    role = 'user' if author_role == 'user' else 'assistant'

                    timestamp = None
                    if message.get('create_time'):
                        try:
                            timestamp = datetime.fromtimestamp(message['create_time'])
                        except (ValueError, TypeError):
                            pass

                    message_nodes.append({
                        'id': node_id,
                        'parent': node.get('parent'),
                        'role': role,
                        'content': text_content.strip(),
                        'timestamp': timestamp,
                        'create_time': message.get('create_time', 0)
                    })

        # Sort by creation time
        message_nodes.sort(key=lambda x: x['create_time'])

        # Convert to Message objects
        for idx, node in enumerate(message_nodes):
            messages.append(Message(
                role=node['role'],
                content=node['content'],
                timestamp=node['timestamp'],
                message_index=idx
            ))

        return messages, SourcePlatform.CHATGPT, created_at


class ClaudeJSONParser(BaseParser):
    """Parser for Claude JSON exports."""

    def can_parse(self, content: str, filename: str) -> bool:
        """Check if content is Claude JSON export format."""
        if not filename.endswith('.json'):
            return False
        try:
            data = json.loads(content)
            # Claude exports have 'chat_messages' or 'messages' key
            if isinstance(data, dict):
                if 'chat_messages' in data or 'messages' in data:
                    return True
                # Also check for uuid and name (Claude conversation format)
                if 'uuid' in data and 'name' in data:
                    return True
            return False
        except json.JSONDecodeError:
            return False

    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse Claude JSON export."""
        data = json.loads(content)
        messages = []
        created_at = None

        # Extract creation time
        if 'created_at' in data:
            try:
                created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass

        # Get messages list
        message_list = data.get('chat_messages') or data.get('messages', [])

        for idx, msg in enumerate(message_list):
            role = msg.get('sender', msg.get('role', 'unknown'))
            role = 'user' if role in ('human', 'user') else 'assistant'

            content_text = msg.get('text', msg.get('content', ''))

            # Handle content that might be a list
            if isinstance(content_text, list):
                content_text = ' '.join(
                    item.get('text', str(item)) if isinstance(item, dict) else str(item)
                    for item in content_text
                )

            if content_text.strip():
                timestamp = None
                if msg.get('created_at'):
                    try:
                        timestamp = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        pass

                messages.append(Message(
                    role=role,
                    content=content_text.strip(),
                    timestamp=timestamp,
                    message_index=idx
                ))

        return messages, SourcePlatform.CLAUDE, created_at


class ClaudeMarkdownParser(BaseParser):
    """Parser for Claude Markdown exports."""

    # Patterns for different Claude markdown export formats
    PATTERNS = [
        # Format: ## Human: / ## Assistant:
        (r'^##\s*(Human|Assistant):\s*$', lambda m: 'user' if m.group(1) == 'Human' else 'assistant'),
        # Format: **Human:** / **Assistant:**
        (r'^\*\*(Human|Assistant)\*\*:', lambda m: 'user' if m.group(1) == 'Human' else 'assistant'),
        # Format: [Human] / [Assistant]
        (r'^\[(Human|Assistant)\]', lambda m: 'user' if m.group(1) == 'Human' else 'assistant'),
        # Format: Human: / Assistant: (at line start)
        (r'^(Human|Assistant):\s*', lambda m: 'user' if m.group(1) == 'Human' else 'assistant'),
        # Format: User: / Claude:
        (r'^(User|Claude):\s*', lambda m: 'user' if m.group(1) == 'User' else 'assistant'),
    ]

    def can_parse(self, content: str, filename: str) -> bool:
        """Check if content is Claude Markdown export format."""
        if not filename.endswith(('.md', '.markdown')):
            return False

        # Check for common Claude markdown patterns
        for pattern, _ in self.PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                return True

        return False

    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse Claude Markdown export."""
        messages = []

        # Detect which pattern is used
        active_pattern = None
        role_extractor = None

        for pattern, extractor in self.PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                active_pattern = pattern
                role_extractor = extractor
                break

        if not active_pattern:
            # Fall back to treating entire content as a single message
            messages.append(Message(
                role='user',
                content=content.strip(),
                timestamp=None,
                message_index=0
            ))
            return messages, SourcePlatform.CLAUDE, None

        # Split content by the pattern
        parts = re.split(f'({active_pattern})', content, flags=re.MULTILINE)

        current_role = None
        current_content = []
        idx = 0

        for part in parts:
            match = re.match(active_pattern, part)
            if match:
                # Save previous message
                if current_role and current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        messages.append(Message(
                            role=current_role,
                            content=content_text,
                            timestamp=None,
                            message_index=idx
                        ))
                        idx += 1

                # Start new message
                current_role = role_extractor(match)
                current_content = []
            else:
                if current_role:
                    current_content.append(part)

        # Don't forget the last message
        if current_role and current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                messages.append(Message(
                    role=current_role,
                    content=content_text,
                    timestamp=None,
                    message_index=idx
                ))

        return messages, SourcePlatform.CLAUDE, None


class PlainTextParser(BaseParser):
    """Parser for plain text conversation exports."""

    # Common patterns for speaker turns in text files
    PATTERNS = [
        # Format: "You:" / "AI:" or "Me:" / "Assistant:"
        r'^(You|Me|User|Human):\s*',
        r'^(AI|Assistant|Claude|ChatGPT|GPT):\s*',
    ]

    def can_parse(self, content: str, filename: str) -> bool:
        """Check if content is a plain text file we can try to parse."""
        return filename.endswith('.txt')

    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse plain text conversation."""
        messages = []

        # Try to detect alternating speaker pattern
        user_pattern = re.compile(r'^(You|Me|User|Human):\s*', re.MULTILINE | re.IGNORECASE)
        assistant_pattern = re.compile(r'^(AI|Assistant|Claude|ChatGPT|GPT):\s*', re.MULTILINE | re.IGNORECASE)

        # Check if we have speaker markers
        has_user_markers = bool(user_pattern.search(content))
        has_assistant_markers = bool(assistant_pattern.search(content))

        if has_user_markers or has_assistant_markers:
            # Split by any speaker marker
            combined_pattern = re.compile(
                r'^(You|Me|User|Human|AI|Assistant|Claude|ChatGPT|GPT):\s*',
                re.MULTILINE | re.IGNORECASE
            )

            parts = combined_pattern.split(content)
            idx = 0

            # Parts will alternate: [pre-text, speaker1, content1, speaker2, content2, ...]
            i = 1  # Skip any text before first speaker
            while i < len(parts) - 1:
                speaker = parts[i].lower()
                content_text = parts[i + 1].strip() if i + 1 < len(parts) else ''

                role = 'user' if speaker in ('you', 'me', 'user', 'human') else 'assistant'

                if content_text:
                    messages.append(Message(
                        role=role,
                        content=content_text,
                        timestamp=None,
                        message_index=idx
                    ))
                    idx += 1

                i += 2
        else:
            # No speaker markers - treat paragraphs as alternating turns
            paragraphs = re.split(r'\n\n+', content.strip())
            for idx, para in enumerate(paragraphs):
                if para.strip():
                    role = 'user' if idx % 2 == 0 else 'assistant'
                    messages.append(Message(
                        role=role,
                        content=para.strip(),
                        timestamp=None,
                        message_index=idx
                    ))

        return messages, SourcePlatform.OTHER, None


class HTMLParser(BaseParser):
    """Parser for HTML conversation exports."""

    def can_parse(self, content: str, filename: str) -> bool:
        """Check if content is an HTML file."""
        if not filename.endswith(('.html', '.htm')):
            return False
        return '<html' in content.lower() or '<!doctype' in content.lower()

    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse HTML conversation export."""
        soup = BeautifulSoup(content, 'html.parser')
        messages = []

        # Try to find message containers (common patterns)
        message_containers = (
            soup.find_all(class_=re.compile(r'message|chat|conversation', re.I)) or
            soup.find_all(['div', 'p', 'article'])
        )

        # Extract text content
        text_content = soup.get_text(separator='\n\n')

        # Use plain text parser logic on extracted text
        plain_parser = PlainTextParser()
        return plain_parser.parse(text_content, filename.replace('.html', '.txt').replace('.htm', '.txt'))


class ConversationParserFactory:
    """Factory for creating appropriate parsers."""

    def __init__(self):
        self.parsers = [
            ChatGPTParser(),
            ClaudeJSONParser(),
            ClaudeMarkdownParser(),
            HTMLParser(),
            PlainTextParser(),  # Fallback
        ]

    def detect_format(self, content: str, filename: str) -> Optional[BaseParser]:
        """Detect the format and return appropriate parser."""
        for parser in self.parsers:
            if parser.can_parse(content, filename):
                return parser
        return None

    def parse(self, content: str, filename: str) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
        """Parse content using the appropriate parser."""
        parser = self.detect_format(content, filename)

        if parser is None:
            # Last resort: treat as plain text
            parser = PlainTextParser()

        return parser.parse(content, filename)


def parse_file(file_path: str | Path) -> tuple[list[Message], SourcePlatform, Optional[datetime]]:
    """
    Parse a conversation file and return messages.

    Args:
        file_path: Path to the conversation file

    Returns:
        Tuple of (messages, platform, created_at)
    """
    file_path = Path(file_path)

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    factory = ConversationParserFactory()
    return factory.parse(content, file_path.name)
