"""
Classification module for conversation chunks.

Provides:
- LLM-based classification using Anthropic Claude API
- Rule-based fallback classification
- Hub and sub-tag assignment with confidence scores
"""

import json
import re
from typing import Optional

import anthropic

from .schemas import Hub, EmotionalTone, Intensity, Message


# Keyword mappings for rule-based classification
HUB_KEYWORDS: dict[Hub, list[str]] = {
    Hub.WELLNESS: [
        'health', 'sleep', 'exercise', 'therapy', 'therapist', 'mental health', 'anxiety',
        'depression', 'self-care', 'medication', 'doctor', 'stress', 'burnout', 'wellness',
        'meditation', 'mindfulness', 'panic', 'wellbeing', 'healing', 'recovery', 'symptom',
        'diagnosis', 'treatment', 'psychiatrist', 'counselor', 'coping'
    ],
    Hub.BUSINESS: [
        'revenue', 'client', 'startup', 'marketing', 'sales', 'business model', 'entrepreneur',
        'income stream', 'customers', 'product launch', 'pitch', 'investor', 'company',
        'business', 'profit', 'strategy', 'market', 'branding', 'monetize', 'scale',
        'b2b', 'b2c', 'saas', 'pricing', 'competitors'
    ],
    Hub.SCHOOL: [
        'class', 'professor', 'assignment', 'exam', 'grade', 'homework', 'university',
        'college', 'course', 'study', 'academic', 'semester', 'lecture', 'student',
        'degree', 'thesis', 'dissertation', 'gpa', 'tutor', 'school', 'campus',
        'syllabus', 'midterm', 'final', 'research paper'
    ],
    Hub.PRODUCTIVITY: [
        'workflow', 'task', 'system', 'organize', 'schedule', 'habit', 'time management',
        'efficiency', 'automation', 'tools', 'notion', 'productivity', 'calendar',
        'todo', 'to-do', 'planning', 'routine', 'process', 'optimize', 'streamline',
        'pomodoro', 'time block', 'prioritize', 'gtd', 'second brain'
    ],
    Hub.CREATIVE: [
        'writing', 'art', 'music', 'design', 'create', 'creative project', 'idea',
        'inspiration', 'story', 'creative', 'content', 'novel', 'poem', 'paint',
        'draw', 'compose', 'artistic', 'craft', 'portfolio', 'creative writing',
        'fiction', 'screenplay', 'illustration', 'photography'
    ],
    Hub.RELATIONSHIPS: [
        'partner', 'friend', 'family', 'communication', 'boundary', 'boundaries',
        'conflict', 'support', 'connection', 'dating', 'relationship', 'marriage',
        'spouse', 'parent', 'sibling', 'romantic', 'friendship', 'social',
        'attachment', 'trust', 'intimacy', 'breakup', 'divorce'
    ],
    Hub.FINANCIAL: [
        'money', 'budget', 'invest', 'debt', 'savings', 'income', 'expense',
        'financial', 'bank', 'credit', 'payment', 'loan', 'mortgage', 'retirement',
        'stocks', 'crypto', 'tax', 'salary', 'net worth', 'emergency fund',
        'compound interest', 'portfolio', 'dividends'
    ],
    Hub.HOME_ENVIRONMENT: [
        'apartment', 'house', 'clean', 'organize', 'move', 'space', 'furniture',
        'room', 'living', 'environment', 'home', 'decor', 'declutter', 'minimalism',
        'roommate', 'lease', 'rent', 'renovation', 'moving', 'neighborhood',
        'kitchen', 'bedroom', 'office space'
    ],
    Hub.IDENTITY_PERSONAL_DEVELOPMENT: [
        'identity', 'growth', 'self', 'values', 'purpose', 'meaning', 'who am i',
        'trauma', 'healing', 'personal development', 'journey', 'self-discovery',
        'authentic', 'beliefs', 'worldview', 'life philosophy', 'spirituality',
        'self-improvement', 'mindset', 'inner work', 'shadow work', 'ego'
    ],
    Hub.ENTERTAINMENT: [
        'movie', 'show', 'game', 'fun', 'hobby', 'leisure', 'watch', 'play',
        'enjoy', 'entertainment', 'relax', 'netflix', 'youtube', 'podcast',
        'book', 'reading for fun', 'video game', 'board game', 'streaming',
        'tv series', 'anime', 'manga', 'concert', 'festival'
    ],
}

SUB_TAGS_KEYWORDS: dict[str, list[str]] = {
    'ADHD': [
        'adhd', 'attention', 'focus', 'hyperfocus', 'executive function',
        'dopamine', 'stimulant', 'distraction', 'impulsivity', 'hyperactivity',
        'neurodivergent', 'adderall', 'vyvanse', 'ritalin', 'working memory'
    ],
    'trauma processing': [
        'trauma', 'ptsd', 'trigger', 'processing', 'childhood', 'abuse',
        'neglect', 'flashback', 'dissociation', 'hypervigilance', 'cptsd',
        'traumatic', 'survivor'
    ],
    'workflow design': [
        'workflow', 'system design', 'automate', 'process', 'pipeline',
        'integration', 'setup', 'architecture', 'flow', 'systematic'
    ],
    'therapy themes': [
        'therapy', 'therapist', 'session', 'therapeutic', 'counseling',
        'psychotherapy', 'cbt', 'dbt', 'emdr', 'inner child'
    ],
    'executive function': [
        'executive function', 'planning', 'prioritizing', 'task initiation',
        'working memory', 'cognitive flexibility', 'self-monitoring',
        'impulse control', 'organization'
    ],
    'business strategy': [
        'strategy', 'business plan', 'market analysis', 'competitive',
        'positioning', 'growth strategy', 'scaling', 'pivot', 'roadmap'
    ],
    'academic planning': [
        'academic', 'semester plan', 'study schedule', 'course selection',
        'degree planning', 'research plan', 'academic goals'
    ],
    'emotional regulation': [
        'emotional regulation', 'emotions', 'regulate', 'overwhelm',
        'mood', 'feelings', 'self-soothe', 'grounding', 'coping mechanism'
    ],
    'identity work': [
        'identity', 'self-concept', 'who am i', 'authentic self',
        'values clarification', 'life purpose', 'self-understanding'
    ],
    'systems architecture': [
        'architecture', 'system design', 'infrastructure', 'framework',
        'integration', 'api', 'database', 'backend', 'frontend'
    ],
    'habit building': [
        'habit', 'routine', 'consistency', 'streak', 'habit stack',
        'cue', 'reward', 'behavior change', 'atomic habits'
    ],
    'goal setting': [
        'goal', 'objective', 'target', 'milestone', 'okr', 'smart goals',
        'vision', 'aspiration', 'achievement'
    ],
    'self-reflection': [
        'reflect', 'introspection', 'journal', 'self-awareness',
        'insight', 'realization', 'understanding myself'
    ],
    'anxiety management': [
        'anxiety', 'anxious', 'worry', 'panic', 'nervous', 'stress management',
        'calm', 'relaxation', 'breathing exercises'
    ],
    'career development': [
        'career', 'job search', 'interview', 'resume', 'networking',
        'promotion', 'career path', 'professional development'
    ],
}

EMOTIONAL_KEYWORDS: dict[EmotionalTone, list[str]] = {
    EmotionalTone.REFLECTIVE: ['thinking about', 'reflecting', 'looking back', 'realize', 'understand now'],
    EmotionalTone.ANXIOUS: ['worried', 'anxious', 'nervous', 'scared', 'fear', 'panic', 'stress'],
    EmotionalTone.HOPEFUL: ['hope', 'optimistic', 'looking forward', 'excited about', 'possibility'],
    EmotionalTone.PROCESSING: ['processing', 'working through', 'figuring out', 'trying to understand'],
    EmotionalTone.ANALYTICAL: ['analyze', 'logic', 'systematic', 'breakdown', 'understand how'],
    EmotionalTone.FRUSTRATED: ['frustrated', 'annoyed', 'stuck', 'difficult', 'struggling'],
    EmotionalTone.EXCITED: ['excited', 'can\'t wait', 'amazing', 'thrilled', 'energized'],
    EmotionalTone.VULNERABLE: ['vulnerable', 'open up', 'honest', 'admit', 'hard to say'],
    EmotionalTone.DETERMINED: ['determined', 'committed', 'going to', 'will do', 'must'],
    EmotionalTone.OVERWHELMED: ['overwhelmed', 'too much', 'can\'t handle', 'drowning', 'exhausted'],
    EmotionalTone.CURIOUS: ['curious', 'wonder', 'what if', 'interested', 'want to know'],
    EmotionalTone.NEUTRAL: [],
}


class ClassificationResult:
    """Result of chunk classification."""

    def __init__(
        self,
        primary_hub: Hub,
        primary_confidence: float,
        secondary_hubs: list[Hub],
        sub_tags: list[str],
        emotional_tone: EmotionalTone,
        emotional_intensity: Intensity,
        emotional_themes: list[str],
        rationale: str
    ):
        self.primary_hub = primary_hub
        self.primary_confidence = primary_confidence
        self.secondary_hubs = secondary_hubs
        self.sub_tags = sub_tags
        self.emotional_tone = emotional_tone
        self.emotional_intensity = emotional_intensity
        self.emotional_themes = emotional_themes
        self.rationale = rationale


class RuleBasedClassifier:
    """Rule-based classifier using keyword matching."""

    def classify(self, messages: list[Message]) -> ClassificationResult:
        """Classify a chunk using keyword matching."""
        # Combine all message content
        full_text = ' '.join(msg.content for msg in messages).lower()

        # Score each hub
        hub_scores: dict[Hub, float] = {}
        for hub, keywords in HUB_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in full_text)
            if score > 0:
                hub_scores[hub] = score

        # Determine primary hub
        if hub_scores:
            sorted_hubs = sorted(hub_scores.items(), key=lambda x: x[1], reverse=True)
            primary_hub = sorted_hubs[0][0]
            primary_confidence = min(sorted_hubs[0][1] / 10, 0.9)  # Cap at 0.9 for rule-based

            # Secondary hubs (if score > 2)
            secondary_hubs = [h for h, s in sorted_hubs[1:4] if s >= 2]
        else:
            primary_hub = Hub.PRODUCTIVITY  # Default
            primary_confidence = 0.3
            secondary_hubs = []

        # Detect sub-tags
        sub_tags = []
        for tag, keywords in SUB_TAGS_KEYWORDS.items():
            if any(kw.lower() in full_text for kw in keywords):
                sub_tags.append(tag)

        # Detect emotional tone
        emotional_tone = EmotionalTone.NEUTRAL
        max_emotion_score = 0
        for tone, keywords in EMOTIONAL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in full_text)
            if score > max_emotion_score:
                max_emotion_score = score
                emotional_tone = tone

        # Estimate intensity based on punctuation and caps
        exclamation_count = full_text.count('!')
        caps_ratio = sum(1 for c in full_text if c.isupper()) / max(len(full_text), 1)

        if exclamation_count > 5 or caps_ratio > 0.1:
            intensity = Intensity.HIGH
        elif exclamation_count > 2 or caps_ratio > 0.05:
            intensity = Intensity.MEDIUM
        else:
            intensity = Intensity.LOW

        # Extract emotional themes from sub-tags
        emotional_themes = [t for t in sub_tags if t in [
            'trauma processing', 'emotional regulation', 'anxiety management',
            'self-reflection', 'identity work'
        ]]

        rationale = f"Rule-based classification. Primary hub '{primary_hub.value}' based on keyword matches."

        return ClassificationResult(
            primary_hub=primary_hub,
            primary_confidence=primary_confidence,
            secondary_hubs=secondary_hubs,
            sub_tags=sub_tags[:10],  # Limit to 10 tags
            emotional_tone=emotional_tone,
            emotional_intensity=intensity,
            emotional_themes=emotional_themes,
            rationale=rationale
        )


class LLMClassifier:
    """LLM-based classifier using Anthropic Claude API."""

    CLASSIFICATION_PROMPT = """You are analyzing a conversation chunk for classification into a personal knowledge management system.

## Your Task
Analyze the following conversation excerpt and provide a structured classification.

## Available Hubs (choose ONE primary, up to 3 secondary):
- Wellness: Health, mental health, therapy, self-care, medical, sleep, exercise
- Business: Entrepreneurship, clients, revenue, marketing, business strategy
- School: Academic work, courses, professors, assignments, studying
- Productivity: Systems, workflows, task management, tools, habits, time management
- Creative: Writing, art, music, design, creative projects
- Relationships: Family, friends, partners, social dynamics, communication
- Financial: Money, budgets, investments, debt, financial planning
- Home/Environment: Living space, organization, moving, home improvement
- Identity & Personal Development: Self-discovery, values, purpose, personal growth, trauma healing
- Entertainment: Movies, games, hobbies, leisure activities

## Available Sub-Tags (select all that apply):
ADHD, trauma processing, workflow design, therapy themes, executive function, business strategy,
academic planning, emotional regulation, identity work, systems architecture, habit building,
goal setting, self-reflection, anxiety management, career development

## Emotional Tones:
reflective, anxious, hopeful, processing, analytical, frustrated, excited, vulnerable,
determined, overwhelmed, curious, neutral

## Conversation Chunk to Analyze:
{conversation_text}

## Response Format (respond ONLY with this JSON structure):
{{
    "primary_hub": "Hub name exactly as listed above",
    "primary_confidence": 0.0 to 1.0,
    "secondary_hubs": ["Hub1", "Hub2"],
    "sub_tags": ["tag1", "tag2", "tag3"],
    "emotional_tone": "tone from list above",
    "emotional_intensity": "low" | "medium" | "high",
    "emotional_themes": ["theme1", "theme2"],
    "rationale": "Brief explanation of why this classification was chosen"
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def classify(self, messages: list[Message]) -> ClassificationResult:
        """Classify a chunk using the Anthropic API."""
        # Format conversation for the prompt
        conversation_text = self._format_conversation(messages)

        # Truncate if too long (keep under ~3000 chars for efficiency)
        if len(conversation_text) > 3000:
            conversation_text = conversation_text[:3000] + "\n\n[... truncated for classification ...]"

        prompt = self.CLASSIFICATION_PROMPT.format(conversation_text=conversation_text)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON from response
            response_text = response.content[0].text
            result = self._parse_response(response_text)
            return result

        except Exception as e:
            # Return a default result on error
            raise ClassificationError(f"LLM classification failed: {e}")

    def _format_conversation(self, messages: list[Message]) -> str:
        """Format messages for the prompt."""
        lines = []
        for msg in messages:
            role = "User" if msg.role == 'user' else "Assistant"
            # Truncate very long messages
            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            lines.append(f"**{role}:** {content}")
        return "\n\n".join(lines)

    def _parse_response(self, response_text: str) -> ClassificationResult:
        """Parse the JSON response from the LLM."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ClassificationError("No JSON found in LLM response")

        data = json.loads(json_match.group())

        # Map string to Hub enum
        hub_map = {h.value: h for h in Hub}
        primary_hub = hub_map.get(data.get('primary_hub', ''), Hub.PRODUCTIVITY)

        secondary_hubs = [
            hub_map[h] for h in data.get('secondary_hubs', [])
            if h in hub_map
        ]

        # Map emotional tone
        tone_map = {t.value: t for t in EmotionalTone}
        emotional_tone = tone_map.get(data.get('emotional_tone', ''), EmotionalTone.NEUTRAL)

        # Map intensity
        intensity_map = {'low': Intensity.LOW, 'medium': Intensity.MEDIUM, 'high': Intensity.HIGH}
        intensity = intensity_map.get(data.get('emotional_intensity', '').lower(), Intensity.MEDIUM)

        return ClassificationResult(
            primary_hub=primary_hub,
            primary_confidence=float(data.get('primary_confidence', 0.8)),
            secondary_hubs=secondary_hubs,
            sub_tags=data.get('sub_tags', []),
            emotional_tone=emotional_tone,
            emotional_intensity=intensity,
            emotional_themes=data.get('emotional_themes', []),
            rationale=data.get('rationale', 'LLM classification')
        )


class ClassificationError(Exception):
    """Raised when classification fails."""
    pass


class HybridClassifier:
    """
    Hybrid classifier that uses LLM with rule-based fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        use_llm: bool = True,
        fallback_to_rules: bool = True
    ):
        """
        Initialize hybrid classifier.

        Args:
            api_key: Anthropic API key (required if use_llm=True)
            model: Anthropic model to use
            use_llm: Whether to use LLM classification
            fallback_to_rules: Whether to fall back to rules if LLM fails
        """
        self.use_llm = use_llm and api_key is not None
        self.fallback_to_rules = fallback_to_rules

        if self.use_llm:
            self.llm_classifier = LLMClassifier(api_key=api_key, model=model)

        self.rule_classifier = RuleBasedClassifier()

    def classify(self, messages: list[Message]) -> ClassificationResult:
        """
        Classify a chunk using LLM with optional fallback.

        Args:
            messages: List of messages in the chunk

        Returns:
            ClassificationResult with hub assignments and metadata
        """
        if self.use_llm:
            try:
                return self.llm_classifier.classify(messages)
            except ClassificationError as e:
                if self.fallback_to_rules:
                    result = self.rule_classifier.classify(messages)
                    result.rationale = f"Fallback to rules after LLM error: {e}. {result.rationale}"
                    return result
                raise

        return self.rule_classifier.classify(messages)


def classify_chunk(
    messages: list[Message],
    api_key: Optional[str] = None,
    use_llm: bool = True
) -> ClassificationResult:
    """
    Convenience function to classify a conversation chunk.

    Args:
        messages: List of messages in the chunk
        api_key: Anthropic API key
        use_llm: Whether to use LLM classification

    Returns:
        ClassificationResult
    """
    classifier = HybridClassifier(api_key=api_key, use_llm=use_llm)
    return classifier.classify(messages)
