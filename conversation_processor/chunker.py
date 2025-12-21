"""
Semantic chunking for conversations.

Splits conversations into coherent chunks based on:
- Topic shifts
- Message count boundaries (15-30 messages)
- Natural conversation breaks
- Preserving question-answer pairs
"""

import re
from dataclasses import dataclass

from .schemas import Message


@dataclass
class ChunkBoundary:
    """Represents a potential chunk boundary."""
    position: int  # Message index
    score: float   # How strong this boundary is (0-1)
    reason: str    # Why this is a boundary


class SemanticChunker:
    """
    Chunks conversations semantically while respecting size limits.

    Strategy:
    1. Identify potential topic shifts using keyword changes
    2. Score each message boundary
    3. Select boundaries that create chunks within size limits
    4. Ensure Q&A pairs stay together
    """

    # Topic shift indicators
    TOPIC_SHIFT_PHRASES = [
        r'\b(anyway|moving on|next topic|different question|another thing|by the way)\b',
        r'\b(let\'s talk about|can we discuss|i want to ask about|switching gears)\b',
        r'\b(on a different note|separately|unrelated but|also wanted to)\b',
        r'^(ok|okay|alright|so)[,.]?\s*(now|next|let\'s)',
    ]

    # Strong topic keywords by category
    TOPIC_KEYWORDS = {
        'health': ['health', 'doctor', 'medication', 'therapy', 'sleep', 'exercise', 'anxiety', 'depression'],
        'work': ['work', 'job', 'career', 'boss', 'colleague', 'project', 'deadline', 'meeting'],
        'school': ['class', 'professor', 'assignment', 'exam', 'grade', 'study', 'course', 'homework'],
        'relationships': ['friend', 'family', 'partner', 'relationship', 'dating', 'conversation', 'conflict'],
        'productivity': ['task', 'system', 'workflow', 'organize', 'schedule', 'habit', 'productivity'],
        'finance': ['money', 'budget', 'savings', 'debt', 'income', 'expense', 'invest', 'financial'],
        'creative': ['write', 'create', 'design', 'art', 'music', 'project', 'idea', 'story'],
        'personal': ['feel', 'think', 'believe', 'identity', 'growth', 'self', 'meaning', 'purpose'],
    }

    def __init__(self, min_messages: int = 15, max_messages: int = 30):
        """
        Initialize chunker with size constraints.

        Args:
            min_messages: Minimum messages per chunk
            max_messages: Maximum messages per chunk
        """
        self.min_messages = min_messages
        self.max_messages = max_messages

    def chunk(self, messages: list[Message]) -> list[list[Message]]:
        """
        Split messages into semantic chunks.

        Args:
            messages: List of conversation messages

        Returns:
            List of message groups (chunks)
        """
        if len(messages) <= self.max_messages:
            return [messages]

        # Find all potential boundaries
        boundaries = self._find_boundaries(messages)

        # Select optimal boundaries
        selected = self._select_boundaries(boundaries, len(messages))

        # Split messages at selected boundaries
        return self._split_at_boundaries(messages, selected)

    def _find_boundaries(self, messages: list[Message]) -> list[ChunkBoundary]:
        """Find all potential chunk boundaries."""
        boundaries = []

        for i in range(1, len(messages)):
            score, reason = self._score_boundary(messages, i)
            if score > 0.1:  # Only consider non-trivial boundaries
                boundaries.append(ChunkBoundary(position=i, score=score, reason=reason))

        return boundaries

    def _score_boundary(self, messages: list[Message], position: int) -> tuple[float, str]:
        """
        Score a potential boundary between messages[position-1] and messages[position].

        Returns (score, reason) tuple.
        """
        if position <= 0 or position >= len(messages):
            return 0.0, ""

        prev_msg = messages[position - 1]
        curr_msg = messages[position]
        score = 0.0
        reasons = []

        # 1. User message after assistant response is natural break (0.3)
        if prev_msg.role == 'assistant' and curr_msg.role == 'user':
            score += 0.3
            reasons.append("user turn after assistant")

        # 2. Explicit topic shift phrases (0.5)
        for pattern in self.TOPIC_SHIFT_PHRASES:
            if re.search(pattern, curr_msg.content, re.IGNORECASE):
                score += 0.5
                reasons.append("explicit topic shift")
                break

        # 3. Topic keyword change detection (0.4)
        prev_topics = self._detect_topics(prev_msg.content)
        curr_topics = self._detect_topics(curr_msg.content)

        if prev_topics and curr_topics:
            # If topics changed significantly
            overlap = len(prev_topics & curr_topics)
            if overlap == 0 and len(curr_topics) > 0:
                score += 0.4
                reasons.append(f"topic shift: {prev_topics} -> {curr_topics}")

        # 4. Long silence indicator (if timestamps available) (0.3)
        if prev_msg.timestamp and curr_msg.timestamp:
            time_diff = (curr_msg.timestamp - prev_msg.timestamp).total_seconds()
            if time_diff > 3600:  # More than 1 hour gap
                score += 0.3
                reasons.append("time gap > 1 hour")

        # 5. Question mark at end of current message suggests continuing (reduce score)
        if curr_msg.role == 'user' and curr_msg.content.strip().endswith('?'):
            # This is a question - next message will answer it, weak boundary
            pass  # Don't reduce, but don't add either

        # 6. Length-based hints (very long messages often signal topic completion)
        if len(prev_msg.content) > 1500 and prev_msg.role == 'assistant':
            score += 0.2
            reasons.append("long assistant response completed")

        return min(score, 1.0), "; ".join(reasons) if reasons else "weak signals"

    def _detect_topics(self, text: str) -> set[str]:
        """Detect topic categories present in text."""
        text_lower = text.lower()
        detected = set()

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.add(topic)
                    break

        return detected

    def _select_boundaries(self, boundaries: list[ChunkBoundary], total_messages: int) -> list[int]:
        """
        Select optimal boundaries that respect chunk size constraints.

        Uses a greedy approach:
        1. Start from beginning
        2. Find best boundary within [min, max] range
        3. Repeat until end
        """
        if not boundaries:
            # No good boundaries found, split evenly
            return self._create_even_splits(total_messages)

        selected = []
        current_start = 0

        while current_start < total_messages:
            remaining = total_messages - current_start

            if remaining <= self.max_messages:
                # Last chunk
                break

            # Find boundaries in acceptable range
            min_pos = current_start + self.min_messages
            max_pos = min(current_start + self.max_messages, total_messages)

            candidates = [
                b for b in boundaries
                if min_pos <= b.position <= max_pos
            ]

            if candidates:
                # Select highest scoring boundary
                best = max(candidates, key=lambda b: b.score)
                selected.append(best.position)
                current_start = best.position
            else:
                # No good boundary in range, force split at max
                selected.append(max_pos)
                current_start = max_pos

        return selected

    def _create_even_splits(self, total_messages: int) -> list[int]:
        """Create evenly distributed splits when no good boundaries exist."""
        if total_messages <= self.max_messages:
            return []

        chunk_count = (total_messages + self.max_messages - 1) // self.max_messages
        chunk_size = total_messages // chunk_count

        return [chunk_size * i for i in range(1, chunk_count)]

    def _split_at_boundaries(self, messages: list[Message], boundaries: list[int]) -> list[list[Message]]:
        """Split messages at the given boundary positions."""
        chunks = []
        start = 0

        for boundary in sorted(boundaries):
            if boundary > start:
                chunks.append(messages[start:boundary])
                start = boundary

        # Don't forget the last chunk
        if start < len(messages):
            chunks.append(messages[start:])

        return chunks


def chunk_conversation(
    messages: list[Message],
    min_messages: int = 15,
    max_messages: int = 30
) -> list[list[Message]]:
    """
    Convenience function to chunk a conversation.

    Args:
        messages: List of conversation messages
        min_messages: Minimum messages per chunk
        max_messages: Maximum messages per chunk

    Returns:
        List of message groups (chunks)
    """
    chunker = SemanticChunker(min_messages=min_messages, max_messages=max_messages)
    return chunker.chunk(messages)
