"""
Main conversation processor orchestrator.

Coordinates all processing steps:
1. File discovery and parsing
2. Semantic chunking
3. Classification
4. Insight extraction
5. JSON output generation
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .chunker import SemanticChunker
from .classifier import HybridClassifier
from .extractor import HybridExtractor
from .parsers import parse_file
from .schemas import (
    Chunk,
    Conversation,
    ConversationMetadata,
    EmotionalContext,
    Message,
    ProcessingConfig,
    ProcessingResult,
)
from .utils import (
    count_words,
    ensure_directory,
    estimate_duration,
    extract_zip,
    find_conversation_files,
    format_messages_as_text,
    generate_processing_report,
    sanitize_filename,
    save_chunk_json,
    save_conversation_json,
)


class ConversationProcessor:
    """
    Main processor for batch conversion of AI conversation exports.

    Transforms raw ChatGPT/Claude exports into structured, Notion-ready JSON.
    """

    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize the processor.

        Args:
            config: Processing configuration. If None, uses defaults.
        """
        self.config = config or ProcessingConfig()

        # Initialize sub-components
        self.chunker = SemanticChunker(
            min_messages=self.config.min_chunk_messages,
            max_messages=self.config.max_chunk_messages
        )

        self.classifier = HybridClassifier(
            api_key=self.config.anthropic_api_key,
            model=self.config.anthropic_model,
            use_llm=self.config.use_llm_classification,
            fallback_to_rules=self.config.fallback_to_rules
        )

        self.extractor = HybridExtractor(
            api_key=self.config.anthropic_api_key,
            model=self.config.anthropic_model,
            use_llm=self.config.use_llm_classification,
            fallback_to_rules=self.config.fallback_to_rules
        )

        # Ensure output directories exist
        self.conversations_dir = ensure_directory(
            Path(self.config.output_directory) / "conversations"
        )
        self.chunks_dir = ensure_directory(
            Path(self.config.output_directory) / "chunks"
        )

    def process_directory(self, input_dir: str | Path) -> ProcessingResult:
        """
        Process all conversation files in a directory.

        Args:
            input_dir: Directory containing conversation files

        Returns:
            ProcessingResult with statistics and any errors
        """
        start_time = time.time()
        result = ProcessingResult()

        # Find all conversation files
        files = find_conversation_files(input_dir)
        print(f"Found {len(files)} conversation files to process")

        for filepath in files:
            try:
                print(f"\nProcessing: {filepath.name}")
                conversation = self.process_file(filepath)
                result.conversations.append(conversation.conversation_id)
                result.total_chunks_created += len(conversation.chunks)
                result.total_files_processed += 1
                print(f"  -> Created {len(conversation.chunks)} chunks")
            except Exception as e:
                error_msg = f"Failed to process {filepath.name}: {str(e)}"
                print(f"  -> ERROR: {error_msg}")
                result.errors.append(error_msg)
                result.total_files_failed += 1

        result.processing_time_seconds = time.time() - start_time

        # Generate and save report
        report = generate_processing_report(
            total_files=result.total_files_processed + result.total_files_failed,
            successful=result.total_files_processed,
            failed=result.total_files_failed,
            total_chunks=result.total_chunks_created,
            processing_time=result.processing_time_seconds,
            errors=result.errors
        )

        report_path = Path(self.config.output_directory) / "processing_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{'='*50}")
        print("PROCESSING COMPLETE")
        print(f"{'='*50}")
        print(f"Files processed: {result.total_files_processed}")
        print(f"Files failed: {result.total_files_failed}")
        print(f"Chunks created: {result.total_chunks_created}")
        print(f"Time elapsed: {result.processing_time_seconds:.2f}s")
        print(f"Report saved to: {report_path}")

        return result

    def process_zip(self, zip_path: str | Path) -> ProcessingResult:
        """
        Process a ZIP file containing conversation exports.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            ProcessingResult
        """
        # Extract ZIP to input directory
        extract_dir = Path(self.config.input_directory) / "extracted"
        print(f"Extracting ZIP to: {extract_dir}")

        extracted_files = extract_zip(zip_path, extract_dir)
        print(f"Extracted {len(extracted_files)} files")

        # Process the extracted directory
        return self.process_directory(extract_dir)

    def process_file(self, filepath: str | Path) -> Conversation:
        """
        Process a single conversation file.

        Args:
            filepath: Path to the conversation file

        Returns:
            Processed Conversation object
        """
        filepath = Path(filepath)

        # Parse the file
        messages, platform, created_at = parse_file(filepath)

        if not messages:
            raise ValueError(f"No messages found in {filepath.name}")

        # Create conversation ID
        conversation_id = str(uuid.uuid4())

        # Chunk the conversation
        message_chunks = self.chunker.chunk(messages)

        # Process each chunk
        processed_chunks = []
        all_themes = set()

        for chunk_num, chunk_messages in enumerate(message_chunks, 1):
            chunk = self._process_chunk(
                messages=chunk_messages,
                chunk_number=chunk_num,
                conversation_id=conversation_id,
                source_file=filepath.name,
                created_at=created_at
            )
            processed_chunks.append(chunk)

            # Collect themes
            all_themes.add(chunk.primary_hub.value)
            all_themes.update(chunk.sub_tags[:3])

            # Save individual chunk file
            save_chunk_json(chunk, self.chunks_dir)

        # Calculate metadata
        total_text = format_messages_as_text(messages)
        word_count = count_words(total_text)

        # Generate title from first chunk or first message
        title = processed_chunks[0].chunk_title if processed_chunks else "Untitled Conversation"

        # Generate overall summary
        overall_summary = self._generate_conversation_summary(processed_chunks)

        # Create conversation object
        conversation = Conversation(
            conversation_id=conversation_id,
            source_file=filepath.name,
            source_platform=platform,
            title=title,
            created_at=created_at,
            processed_at=datetime.now(),
            total_chunks=len(processed_chunks),
            total_messages=len(messages),
            primary_themes=list(all_themes)[:10],
            overall_summary=overall_summary,
            chunks=processed_chunks,
            metadata=ConversationMetadata(
                word_count=word_count,
                participant_count=2,
                duration_estimate=estimate_duration(messages, word_count),
                message_count=len(messages)
            )
        )

        # Save conversation file
        save_conversation_json(conversation, self.conversations_dir)

        return conversation

    def _process_chunk(
        self,
        messages: list[Message],
        chunk_number: int,
        conversation_id: str,
        source_file: str,
        created_at: Optional[datetime]
    ) -> Chunk:
        """
        Process a single chunk of messages.

        Args:
            messages: Messages in this chunk
            chunk_number: Position in conversation
            conversation_id: Parent conversation ID
            source_file: Original filename
            created_at: Original creation time

        Returns:
            Processed Chunk object
        """
        # Classify the chunk
        classification = self.classifier.classify(messages)

        # Extract insights
        extraction = self.extractor.extract(messages, classification.primary_hub)

        # Format full chunk text
        full_text = format_messages_as_text(messages)

        # Create chunk object
        chunk = Chunk(
            conversation_id=conversation_id,
            source_file=source_file,
            chunk_number=chunk_number,
            chunk_title=extraction.chunk_title,
            primary_hub=classification.primary_hub,
            primary_hub_confidence=classification.primary_confidence,
            secondary_hubs=classification.secondary_hubs,
            sub_tags=classification.sub_tags,
            summary=extraction.summary,
            key_insights=extraction.key_insights,
            supporting_excerpts=extraction.supporting_excerpts,
            full_chunk_text=full_text,
            why_it_matters=extraction.why_it_matters,
            emotional_context=EmotionalContext(
                tone=classification.emotional_tone,
                intensity=classification.emotional_intensity,
                themes=classification.emotional_themes
            ),
            classification_rationale=classification.rationale,
            message_count=len(messages),
            word_count=count_words(full_text),
            created_at=created_at,
            processed_at=datetime.now()
        )

        return chunk

    def _generate_conversation_summary(self, chunks: list[Chunk]) -> str:
        """
        Generate an overall summary from processed chunks.

        Args:
            chunks: List of processed chunks

        Returns:
            Overall summary string
        """
        if not chunks:
            return "Empty conversation"

        # Collect unique hubs
        hubs = set(chunk.primary_hub.value for chunk in chunks)

        # Collect key insights (first from each chunk)
        key_points = [
            chunk.key_insights[0]
            for chunk in chunks
            if chunk.key_insights
        ][:5]

        hub_list = ', '.join(sorted(hubs))
        summary = f"A {len(chunks)}-part conversation spanning {hub_list}."

        if key_points:
            summary += f" Key themes include: {'; '.join(key_points[:3])}"

        return summary


def create_processor(
    anthropic_api_key: Optional[str] = None,
    use_llm: bool = True,
    min_chunk_size: int = 15,
    max_chunk_size: int = 30,
    input_dir: str = "input",
    output_dir: str = "processed"
) -> ConversationProcessor:
    """
    Factory function to create a configured processor.

    Args:
        anthropic_api_key: API key for Anthropic (for LLM classification)
        use_llm: Whether to use LLM-based classification
        min_chunk_size: Minimum messages per chunk
        max_chunk_size: Maximum messages per chunk
        input_dir: Input directory
        output_dir: Output directory

    Returns:
        Configured ConversationProcessor
    """
    config = ProcessingConfig(
        anthropic_api_key=anthropic_api_key,
        use_llm_classification=use_llm and anthropic_api_key is not None,
        min_chunk_messages=min_chunk_size,
        max_chunk_messages=max_chunk_size,
        input_directory=input_dir,
        output_directory=output_dir
    )

    return ConversationProcessor(config)
