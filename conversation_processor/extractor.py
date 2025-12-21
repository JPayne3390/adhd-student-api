"""
Insight and excerpt extraction for conversation chunks.

Provides:
- LLM-based insight extraction using Anthropic Claude API
- Rule-based fallback extraction
- Supporting excerpt selection
- Summary generation
"""

import json
import re
from dataclasses import dataclass
from typing import Optional

import anthropic

from .schemas import Message, SupportingExcerpt, Hub


@dataclass
class ExtractionResult:
    """Result of insight extraction."""
    chunk_title: str
    summary: str
    key_insights: list[str]
    supporting_excerpts: list[SupportingExcerpt]
    why_it_matters: str


class RuleBasedExtractor:
    """Rule-based extractor for when LLM is unavailable."""

    # Patterns that often indicate insights
    INSIGHT_PATTERNS = [
        r'i (?:realized?|learned?|discovered?|understood?|noticed?) (?:that )?(.{20,150})',
        r'(?:the )?(?:key|important|main|big) (?:thing|point|insight|takeaway) (?:is|was) (.{20,150})',
        r'what (?:works|helped|matters) (?:is|was) (.{20,150})',
        r'i need to (.{20,100})',
        r'(?:my|the) (?:goal|plan|strategy|approach) (?:is|was|should be) (.{20,150})',
    ]

    def extract(self, messages: list[Message], primary_hub: Hub) -> ExtractionResult:
        """Extract insights using pattern matching."""
        full_text = '\n'.join(msg.content for msg in messages)

        # Generate title from first user message
        first_user = next((m for m in messages if m.role == 'user'), messages[0])
        title = self._generate_title(first_user.content)

        # Generate summary
        summary = self._generate_summary(messages)

        # Extract insights
        insights = self._extract_insights(full_text)

        # Select excerpts
        excerpts = self._select_excerpts(messages)

        # Generate why it matters
        why_it_matters = self._generate_why_it_matters(primary_hub, insights)

        return ExtractionResult(
            chunk_title=title,
            summary=summary,
            key_insights=insights,
            supporting_excerpts=excerpts,
            why_it_matters=why_it_matters
        )

    def _generate_title(self, first_message: str) -> str:
        """Generate a title from the first message."""
        # Take first sentence or first 60 chars
        first_sentence = re.split(r'[.!?]', first_message)[0].strip()
        if len(first_sentence) > 60:
            # Find a good break point
            words = first_sentence[:60].split()
            first_sentence = ' '.join(words[:-1]) + '...'
        return first_sentence or "Conversation Chunk"

    def _generate_summary(self, messages: list[Message]) -> str:
        """Generate a basic summary."""
        user_messages = [m for m in messages if m.role == 'user']
        assistant_messages = [m for m in messages if m.role == 'assistant']

        # Count topics mentioned
        topics = []
        combined_text = ' '.join(m.content.lower() for m in messages)

        topic_keywords = {
            'planning': ['plan', 'schedule', 'organize'],
            'problem-solving': ['problem', 'issue', 'challenge', 'struggle'],
            'learning': ['learn', 'understand', 'figure out'],
            'emotional processing': ['feel', 'emotion', 'process'],
            'strategy discussion': ['strategy', 'approach', 'method'],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in combined_text for kw in keywords):
                topics.append(topic)

        topic_str = ', '.join(topics[:3]) if topics else 'various topics'

        return (
            f"A conversation with {len(user_messages)} user messages and "
            f"{len(assistant_messages)} assistant responses covering {topic_str}."
        )

    def _extract_insights(self, text: str) -> list[str]:
        """Extract potential insights using patterns."""
        insights = []
        text_lower = text.lower()

        for pattern in self.INSIGHT_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches[:2]:  # Limit per pattern
                cleaned = match.strip().capitalize()
                if cleaned and len(cleaned) > 20:
                    insights.append(cleaned)

        # Deduplicate and limit
        seen = set()
        unique_insights = []
        for insight in insights:
            normalized = insight.lower()[:50]
            if normalized not in seen:
                seen.add(normalized)
                unique_insights.append(insight)

        return unique_insights[:5] or ["Key discussion points require further analysis"]

    def _select_excerpts(self, messages: list[Message]) -> list[SupportingExcerpt]:
        """Select meaningful excerpts from messages."""
        excerpts = []

        # Look for messages with insight indicators
        insight_words = ['realize', 'important', 'key', 'learned', 'understand', 'insight']

        for msg in messages:
            content_lower = msg.content.lower()
            if any(word in content_lower for word in insight_words):
                # Extract a relevant portion (max 200 chars)
                excerpt_text = msg.content[:200]
                if len(msg.content) > 200:
                    # Try to end at a sentence
                    last_period = excerpt_text.rfind('.')
                    if last_period > 100:
                        excerpt_text = excerpt_text[:last_period + 1]
                    else:
                        excerpt_text += '...'

                excerpts.append(SupportingExcerpt(
                    text=excerpt_text,
                    speaker=msg.role,
                    relevance="Contains key insight or realization"
                ))

                if len(excerpts) >= 3:
                    break

        # If no insight-heavy excerpts, take first user message
        if not excerpts and messages:
            first_user = next((m for m in messages if m.role == 'user'), messages[0])
            excerpts.append(SupportingExcerpt(
                text=first_user.content[:200] + ('...' if len(first_user.content) > 200 else ''),
                speaker=first_user.role,
                relevance="Opening context for the conversation"
            ))

        return excerpts

    def _generate_why_it_matters(self, hub: Hub, insights: list[str]) -> str:
        """Generate a 'why it matters' statement."""
        hub_relevance = {
            Hub.WELLNESS: "This relates to personal wellbeing and health management",
            Hub.BUSINESS: "This has implications for business growth and professional development",
            Hub.SCHOOL: "This impacts academic performance and learning outcomes",
            Hub.PRODUCTIVITY: "This affects daily effectiveness and system optimization",
            Hub.CREATIVE: "This nurtures creative expression and artistic development",
            Hub.RELATIONSHIPS: "This influences interpersonal connections and social wellbeing",
            Hub.FINANCIAL: "This impacts financial stability and monetary decisions",
            Hub.HOME_ENVIRONMENT: "This affects living space and environmental comfort",
            Hub.IDENTITY_PERSONAL_DEVELOPMENT: "This contributes to self-understanding and personal growth",
            Hub.ENTERTAINMENT: "This supports leisure, enjoyment, and life balance",
        }

        base = hub_relevance.get(hub, "This conversation contains valuable insights")

        if insights:
            return f"{base}. Key realization: {insights[0][:100]}"
        return f"{base}."


class LLMExtractor:
    """LLM-based extractor using Anthropic Claude API."""

    EXTRACTION_PROMPT = """You are analyzing a conversation chunk to extract key insights and meaningful excerpts for a personal knowledge management system.

## Your Task
Extract insights, generate a summary, select supporting excerpts, and explain why this matters.

## Context
This conversation has been classified under the "{primary_hub}" hub.

## Conversation Chunk:
{conversation_text}

## Response Format (respond ONLY with this JSON structure):
{{
    "chunk_title": "A concise, descriptive title (5-10 words)",
    "summary": "2-3 sentence summary capturing the essence of this conversation segment",
    "key_insights": [
        "First key insight or realization (preserve nuance and emotional context)",
        "Second key insight",
        "Third key insight (if applicable)"
    ],
    "supporting_excerpts": [
        {{
            "text": "Direct quote from the conversation (max 200 chars)",
            "speaker": "user" or "assistant",
            "relevance": "Why this quote matters"
        }}
    ],
    "why_it_matters": "Personal significance and actionability - why this chunk is worth preserving and revisiting"
}}

## Guidelines:
- Preserve emotional nuance and personal significance
- Focus on insights that could inform future decisions or reflection
- Select excerpts that capture pivotal moments or realizations
- Make "why_it_matters" specific and actionable
- Keep the title clear and searchable"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def extract(self, messages: list[Message], primary_hub: Hub) -> ExtractionResult:
        """Extract insights using the Anthropic API."""
        conversation_text = self._format_conversation(messages)

        # Truncate if too long
        if len(conversation_text) > 4000:
            conversation_text = conversation_text[:4000] + "\n\n[... truncated ...]"

        prompt = self.EXTRACTION_PROMPT.format(
            primary_hub=primary_hub.value,
            conversation_text=conversation_text
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            return self._parse_response(response_text)

        except Exception as e:
            raise ExtractionError(f"LLM extraction failed: {e}")

    def _format_conversation(self, messages: list[Message]) -> str:
        """Format messages for the prompt."""
        lines = []
        for msg in messages:
            role = "User" if msg.role == 'user' else "Assistant"
            lines.append(f"**{role}:** {msg.content}")
        return "\n\n".join(lines)

    def _parse_response(self, response_text: str) -> ExtractionResult:
        """Parse the JSON response from the LLM."""
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ExtractionError("No JSON found in LLM response")

        data = json.loads(json_match.group())

        # Parse supporting excerpts
        excerpts = []
        for exc in data.get('supporting_excerpts', []):
            excerpts.append(SupportingExcerpt(
                text=exc.get('text', ''),
                speaker=exc.get('speaker', 'user'),
                relevance=exc.get('relevance', '')
            ))

        return ExtractionResult(
            chunk_title=data.get('chunk_title', 'Untitled Chunk'),
            summary=data.get('summary', ''),
            key_insights=data.get('key_insights', []),
            supporting_excerpts=excerpts,
            why_it_matters=data.get('why_it_matters', '')
        )


class ExtractionError(Exception):
    """Raised when extraction fails."""
    pass


class HybridExtractor:
    """Hybrid extractor that uses LLM with rule-based fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        use_llm: bool = True,
        fallback_to_rules: bool = True
    ):
        """
        Initialize hybrid extractor.

        Args:
            api_key: Anthropic API key
            model: Anthropic model to use
            use_llm: Whether to use LLM extraction
            fallback_to_rules: Whether to fall back to rules if LLM fails
        """
        self.use_llm = use_llm and api_key is not None
        self.fallback_to_rules = fallback_to_rules

        if self.use_llm:
            self.llm_extractor = LLMExtractor(api_key=api_key, model=model)

        self.rule_extractor = RuleBasedExtractor()

    def extract(self, messages: list[Message], primary_hub: Hub) -> ExtractionResult:
        """
        Extract insights from a chunk.

        Args:
            messages: List of messages in the chunk
            primary_hub: The primary hub classification

        Returns:
            ExtractionResult with title, summary, insights, excerpts
        """
        if self.use_llm:
            try:
                return self.llm_extractor.extract(messages, primary_hub)
            except ExtractionError:
                if self.fallback_to_rules:
                    return self.rule_extractor.extract(messages, primary_hub)
                raise

        return self.rule_extractor.extract(messages, primary_hub)


def extract_insights(
    messages: list[Message],
    primary_hub: Hub,
    api_key: Optional[str] = None,
    use_llm: bool = True
) -> ExtractionResult:
    """
    Convenience function to extract insights from a chunk.

    Args:
        messages: List of messages in the chunk
        primary_hub: The primary hub classification
        api_key: Anthropic API key
        use_llm: Whether to use LLM extraction

    Returns:
        ExtractionResult
    """
    extractor = HybridExtractor(api_key=api_key, use_llm=use_llm)
    return extractor.extract(messages, primary_hub)
