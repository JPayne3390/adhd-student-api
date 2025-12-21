"""
Pydantic schemas for conversation processing.

Defines the data models for messages, chunks, and conversations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Hub(str, Enum):
    """Primary hub categories for classification."""
    WELLNESS = "Wellness"
    BUSINESS = "Business"
    SCHOOL = "School"
    PRODUCTIVITY = "Productivity"
    CREATIVE = "Creative"
    RELATIONSHIPS = "Relationships"
    FINANCIAL = "Financial"
    HOME_ENVIRONMENT = "Home/Environment"
    IDENTITY_PERSONAL_DEVELOPMENT = "Identity & Personal Development"
    ENTERTAINMENT = "Entertainment"


class SourcePlatform(str, Enum):
    """Supported source platforms."""
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    OTHER = "other"


class EmotionalTone(str, Enum):
    """Emotional tones detected in conversation chunks."""
    REFLECTIVE = "reflective"
    ANXIOUS = "anxious"
    HOPEFUL = "hopeful"
    PROCESSING = "processing"
    ANALYTICAL = "analytical"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    VULNERABLE = "vulnerable"
    DETERMINED = "determined"
    OVERWHELMED = "overwhelmed"
    CURIOUS = "curious"
    NEUTRAL = "neutral"


class Intensity(str, Enum):
    """Emotional intensity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Message(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., description="Speaker role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="When the message was sent")
    message_index: int = Field(..., description="Position in conversation")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SupportingExcerpt(BaseModel):
    """A supporting excerpt from the conversation."""
    text: str = Field(..., description="Quoted text from conversation")
    speaker: str = Field(..., description="Who said this: 'user' or 'assistant'")
    relevance: str = Field(..., description="Why this excerpt matters")


class EmotionalContext(BaseModel):
    """Emotional context for a chunk."""
    tone: EmotionalTone = Field(..., description="Primary emotional tone")
    intensity: Intensity = Field(..., description="Emotional intensity level")
    themes: list[str] = Field(default_factory=list, description="Emotional themes present")


class Chunk(BaseModel):
    """A semantically coherent chunk of conversation."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique chunk identifier")
    conversation_id: str = Field(..., description="Parent conversation ID")
    source_file: str = Field(..., description="Original source filename")
    chunk_number: int = Field(..., description="Chunk position in conversation")
    chunk_title: str = Field(..., description="Descriptive title for this chunk")

    # Classification
    primary_hub: Hub = Field(..., description="Primary hub classification")
    primary_hub_confidence: float = Field(..., ge=0, le=1, description="Classification confidence")
    secondary_hubs: list[Hub] = Field(default_factory=list, description="Secondary hub classifications")
    sub_tags: list[str] = Field(default_factory=list, description="Multi-select sub-tags")

    # Content
    summary: str = Field(..., description="2-3 sentence summary")
    key_insights: list[str] = Field(default_factory=list, description="Key insights extracted")
    supporting_excerpts: list[SupportingExcerpt] = Field(default_factory=list, description="Supporting quotes")
    full_chunk_text: str = Field(..., description="Complete text of this chunk")
    why_it_matters: str = Field(..., description="Personal significance and actionability")

    # Emotional context
    emotional_context: EmotionalContext = Field(..., description="Emotional analysis")
    classification_rationale: str = Field(..., description="Why classified this way")

    # Metadata
    message_count: int = Field(..., description="Number of messages in chunk")
    word_count: int = Field(..., description="Word count of chunk")
    created_at: Optional[datetime] = Field(None, description="Original creation time")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    notion_ready: bool = Field(True, description="Ready for Notion import")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ConversationMetadata(BaseModel):
    """Metadata for a conversation."""
    word_count: int = Field(..., description="Total word count")
    participant_count: int = Field(2, description="Number of participants")
    duration_estimate: str = Field(..., description="Estimated session length")
    message_count: int = Field(..., description="Total message count")


class Conversation(BaseModel):
    """A complete processed conversation."""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID")
    source_file: str = Field(..., description="Original source filename")
    source_platform: SourcePlatform = Field(..., description="Source platform")
    title: str = Field(..., description="Inferred conversation title")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Original creation time")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")

    # Content summary
    total_chunks: int = Field(..., description="Number of chunks")
    total_messages: int = Field(..., description="Total message count")
    primary_themes: list[str] = Field(default_factory=list, description="Main themes across conversation")
    overall_summary: str = Field(..., description="High-level conversation summary")

    # Chunks
    chunks: list[Chunk] = Field(default_factory=list, description="Processed chunks")

    # Metadata
    metadata: ConversationMetadata = Field(..., description="Conversation metadata")

    # Processing info
    processing_errors: list[str] = Field(default_factory=list, description="Any errors during processing")
    notion_ready: bool = Field(True, description="Ready for Notion import")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ProcessingConfig(BaseModel):
    """Configuration for the batch processor."""
    min_chunk_messages: int = Field(15, description="Minimum messages per chunk")
    max_chunk_messages: int = Field(30, description="Maximum messages per chunk")
    use_llm_classification: bool = Field(True, description="Use LLM for classification")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    anthropic_model: str = Field("claude-sonnet-4-20250514", description="Anthropic model to use")
    fallback_to_rules: bool = Field(True, description="Fall back to rules if LLM fails")
    input_directory: str = Field("input", description="Input directory for files")
    output_directory: str = Field("processed", description="Output directory for results")
    preserve_original_timestamps: bool = Field(True, description="Keep original timestamps")


class ProcessingResult(BaseModel):
    """Result of batch processing."""
    total_files_processed: int = Field(0, description="Files successfully processed")
    total_files_failed: int = Field(0, description="Files that failed processing")
    total_chunks_created: int = Field(0, description="Total chunks created")
    conversations: list[str] = Field(default_factory=list, description="Processed conversation IDs")
    errors: list[str] = Field(default_factory=list, description="Processing errors")
    processing_time_seconds: float = Field(0, description="Total processing time")
