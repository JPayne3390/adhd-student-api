#!/usr/bin/env python3
"""
CLI entry point for the conversation batch processor.

Usage:
    # Process a directory of conversation files
    python run_processor.py --input ./my_conversations

    # Process a ZIP file
    python run_processor.py --zip ./exports.zip

    # Process with LLM classification (requires ANTHROPIC_API_KEY)
    python run_processor.py --input ./conversations --use-llm

    # Custom chunk sizes
    python run_processor.py --input ./conversations --min-chunk 10 --max-chunk 25

Environment Variables:
    ANTHROPIC_API_KEY: Your Anthropic API key for LLM-based classification
"""

import argparse
import os
import sys
from pathlib import Path

from conversation_processor import ConversationProcessor
from conversation_processor.schemas import ProcessingConfig


def main():
    parser = argparse.ArgumentParser(
        description="Batch process AI conversation exports into Notion-ready JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input", "-i",
        type=str,
        help="Directory containing conversation files to process"
    )
    input_group.add_argument(
        "--zip", "-z",
        type=str,
        help="ZIP file containing conversation exports"
    )
    input_group.add_argument(
        "--file", "-f",
        type=str,
        help="Single conversation file to process"
    )

    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="processed",
        help="Output directory for processed files (default: processed)"
    )

    # Processing options
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM-based classification (requires ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Anthropic model to use (default: claude-sonnet-4-20250514)"
    )

    # Chunk size options
    parser.add_argument(
        "--min-chunk",
        type=int,
        default=15,
        help="Minimum messages per chunk (default: 15)"
    )
    parser.add_argument(
        "--max-chunk",
        type=int,
        default=30,
        help="Maximum messages per chunk (default: 30)"
    )

    # Flags
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Don't fall back to rule-based classification if LLM fails"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Validate LLM usage
    if args.use_llm and not args.api_key:
        print("ERROR: --use-llm requires ANTHROPIC_API_KEY environment variable or --api-key")
        print("       Set it with: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Create configuration
    config = ProcessingConfig(
        anthropic_api_key=args.api_key if args.use_llm else None,
        anthropic_model=args.model,
        use_llm_classification=args.use_llm,
        fallback_to_rules=not args.no_fallback,
        min_chunk_messages=args.min_chunk,
        max_chunk_messages=args.max_chunk,
        input_directory="input",
        output_directory=args.output
    )

    # Create processor
    processor = ConversationProcessor(config)

    print("=" * 60)
    print("CONVERSATION BATCH PROCESSOR")
    print("=" * 60)
    print(f"Output directory: {args.output}")
    print(f"Chunk size: {args.min_chunk}-{args.max_chunk} messages")
    print(f"LLM classification: {'Enabled' if args.use_llm else 'Disabled (rule-based)'}")
    if args.use_llm:
        print(f"Model: {args.model}")
    print("=" * 60)

    try:
        if args.zip:
            zip_path = Path(args.zip)
            if not zip_path.exists():
                print(f"ERROR: ZIP file not found: {args.zip}")
                sys.exit(1)
            print(f"\nProcessing ZIP file: {zip_path}")
            result = processor.process_zip(zip_path)

        elif args.input:
            input_dir = Path(args.input)
            if not input_dir.exists():
                print(f"ERROR: Directory not found: {args.input}")
                sys.exit(1)
            print(f"\nProcessing directory: {input_dir}")
            result = processor.process_directory(input_dir)

        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"ERROR: File not found: {args.file}")
                sys.exit(1)
            print(f"\nProcessing single file: {file_path}")
            conversation = processor.process_file(file_path)
            print(f"\nProcessed: {conversation.title}")
            print(f"Chunks created: {len(conversation.chunks)}")
            print(f"Output saved to: {args.output}/")
            return

        # Print summary for batch processing
        print("\n" + "=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        print(f"Successfully processed: {result.total_files_processed} files")
        print(f"Failed: {result.total_files_failed} files")
        print(f"Total chunks created: {result.total_chunks_created}")
        print(f"Processing time: {result.processing_time_seconds:.2f} seconds")

        if result.errors:
            print("\nErrors encountered:")
            for error in result.errors[:5]:
                print(f"  - {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more")

        print("\nOutput files:")
        print(f"  Conversations: {args.output}/conversations/")
        print(f"  Chunks: {args.output}/chunks/")
        print(f"  Report: {args.output}/processing_report.json")

    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
