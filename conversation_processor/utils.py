"""
Utility functions for conversation processing.

Provides:
- File I/O helpers
- Text cleaning functions
- ZIP extraction
- JSON export utilities
"""

import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .schemas import Conversation, Chunk


def extract_zip(zip_path: str | Path, output_dir: str | Path) -> list[Path]:
    """
    Extract a ZIP file to the output directory.

    Args:
        zip_path: Path to the ZIP file
        output_dir: Directory to extract to

    Returns:
        List of extracted file paths
    """
    zip_path = Path(zip_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_files = []

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            # Skip directories and hidden files
            if member.endswith('/') or member.startswith('__MACOSX') or '/.' in member:
                continue

            # Skip non-conversation files
            ext = Path(member).suffix.lower()
            if ext not in ['.json', '.md', '.markdown', '.txt', '.html', '.htm']:
                continue

            # Extract file
            zf.extract(member, output_dir)
            extracted_files.append(output_dir / member)

    return extracted_files


def find_conversation_files(directory: str | Path) -> list[Path]:
    """
    Find all conversation files in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of conversation file paths
    """
    directory = Path(directory)
    extensions = ['.json', '.md', '.markdown', '.txt', '.html', '.htm']

    files = []
    for ext in extensions:
        files.extend(directory.rglob(f'*{ext}'))

    # Filter out hidden files and system files
    files = [
        f for f in files
        if not f.name.startswith('.')
        and '__MACOSX' not in str(f)
        and f.is_file()
    ]

    return sorted(files)


def clean_text(text: str) -> str:
    """
    Clean raw text from conversation exports.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove common export artifacts
    text = re.sub(r'\[Image:.*?\]', '', text)
    text = re.sub(r'\[Attachment:.*?\]', '', text)

    # Clean up markdown artifacts if they're broken
    text = re.sub(r'\*{3,}', '**', text)
    text = re.sub(r'_{3,}', '__', text)

    return text.strip()


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        name: String to sanitize
        max_length: Maximum length for the filename

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)

    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    # Truncate if needed
    if len(name) > max_length:
        name = name[:max_length].rstrip('_')

    return name or 'unnamed'


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def estimate_duration(messages: list[Any], word_count: int) -> str:
    """
    Estimate conversation duration based on content.

    Args:
        messages: List of messages
        word_count: Total word count

    Returns:
        Duration estimate string
    """
    if word_count < 500:
        return "brief exchange"
    elif word_count < 2000:
        return "short session"
    elif word_count < 5000:
        return "moderate session"
    elif word_count < 10000:
        return "extended session"
    else:
        return "lengthy deep-dive"


def save_conversation_json(
    conversation: Conversation,
    output_dir: str | Path,
    filename: str | None = None
) -> Path:
    """
    Save a conversation to JSON file.

    Args:
        conversation: Conversation object to save
        output_dir: Directory to save to
        filename: Optional filename (defaults to conversation_id)

    Returns:
        Path to saved file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"conv_{sanitize_filename(conversation.title)}_{conversation.conversation_id[:8]}.json"

    filepath = output_dir / filename

    # Convert to JSON-serializable dict
    data = conversation.model_dump(mode='json')

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return filepath


def save_chunk_json(
    chunk: Chunk,
    output_dir: str | Path,
    filename: str | None = None
) -> Path:
    """
    Save a chunk to JSON file.

    Args:
        chunk: Chunk object to save
        output_dir: Directory to save to
        filename: Optional filename

    Returns:
        Path to saved file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"chunk_{chunk.conversation_id[:8]}_{chunk.chunk_number:03d}.json"

    filepath = output_dir / filename

    # Convert to JSON-serializable dict
    data = chunk.model_dump(mode='json')

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    return filepath


def generate_processing_report(
    total_files: int,
    successful: int,
    failed: int,
    total_chunks: int,
    processing_time: float,
    errors: list[str]
) -> dict:
    """
    Generate a processing report.

    Args:
        total_files: Number of files processed
        successful: Number of successful processings
        failed: Number of failed processings
        total_chunks: Total chunks created
        processing_time: Total time in seconds
        errors: List of error messages

    Returns:
        Report dictionary
    """
    return {
        "report_generated_at": datetime.now().isoformat(),
        "summary": {
            "total_files_processed": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful / total_files * 100):.1f}%" if total_files > 0 else "N/A",
            "total_chunks_created": total_chunks,
            "processing_time_seconds": round(processing_time, 2),
            "average_time_per_file": round(processing_time / total_files, 2) if total_files > 0 else 0
        },
        "errors": errors if errors else ["No errors encountered"],
        "output_locations": {
            "conversations": "processed/conversations/",
            "chunks": "processed/chunks/"
        },
        "next_steps": [
            "Review generated JSON files in the processed directory",
            "Import conversation files to Notion 'Conversations' database",
            "Import chunk files to Notion 'Conversation Chunks' database",
            "Use Notion's CSV import or API for bulk import"
        ]
    }


def format_messages_as_text(messages: list[Any]) -> str:
    """
    Format messages as readable text.

    Args:
        messages: List of Message objects

    Returns:
        Formatted text string
    """
    lines = []
    for msg in messages:
        role = "User" if msg.role == 'user' else "Assistant"
        lines.append(f"[{role}]")
        lines.append(msg.content)
        lines.append("")  # Empty line between messages
    return '\n'.join(lines)


def load_json_file(filepath: str | Path) -> dict:
    """
    Load a JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_directory(path: str | Path) -> Path:
    """
    Ensure a directory exists.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
