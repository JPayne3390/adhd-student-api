#!/usr/bin/env python3
"""
Create sample test files for the file analyzer
Generates a realistic set of files with various naming issues
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import random

def create_test_directory(base_path='./test_files', num_files=50):
    """Create a test directory with sample files"""

    base = Path(base_path)
    base.mkdir(exist_ok=True)

    print(f"Creating test directory: {base_path}")
    print(f"Generating {num_files} sample files...\n")

    # Sample file names representing common issues
    file_templates = [
        # Academic files with course codes
        "COUN5241_Assignment_{n}_Draft.txt",
        "COUN5254_Week{n}_Reading_Notes.txt",
        "PSY2001_Lecture_{n}_Slides.txt",
        "COUN5241 - Final Paper - Draft {n}.txt",
        "coun5254_homework_{n}.txt",

        # Files with dates in various formats
        "Therapy_Notes_03-15-2025_{n}.txt",
        "2025-02-20_Client_Assessment_{n}.txt",
        "Meeting_Notes_2_20_25_{n}.txt",

        # Semester-based files
        "Spring_2025_Syllabus_COUN5241_{n}.txt",
        "Fall_2024_Grade_Report_{n}.txt",

        # Files with duplicate markers (common OneDrive issue)
        "Assignment_Draft_{n} (1).txt",
        "Paper_Final_{n} (2).txt",
        "Notes_{n} - Copy.txt",

        # Overly long filenames
        "COUN5241_Group_Project_Team_Meeting_Notes_Week_{n}_Discussion_Points_Action_Items.txt",

        # Files with inconsistent casing
        "THERAPY_SESSION_NOTES_{n}.txt",
        "therapy_session_notes_{n}.txt",
        "Therapy_Session_Notes_{n}.txt",

        # Personal files
        "Resume_Updated_{n}.txt",
        "Cover_Letter_Draft_{n}.txt",
        "Medical_Insurance_Card_{n}.txt",

        # Business files
        "Invoice_{n}_ClientA.txt",
        "Contract_Draft_{n}.txt",
        "Budget_Proposal_{n}.txt",

        # Files with special characters
        "Assignment #_{n} - Final Version!.txt",
        "Notes & Ideas_{n}.txt",

        # Vague/unclear names
        "Document_{n}.txt",
        "File_{n}.txt",
        "New Document ({n}).txt",
        "Untitled_{n}.txt",

        # Administrative
        "Registration_Form_{n}.txt",
        "Application_Graduate_School_{n}.txt",
    ]

    created_files = []

    for i in range(num_files):
        # Select random template
        template = random.choice(file_templates)
        filename = template.format(n=i+1)

        filepath = base / filename

        # Create file with sample content
        content = generate_sample_content(filename, i)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        created_files.append(filename)

    print(f"✅ Created {len(created_files)} test files in '{base_path}'\n")
    print("Sample files created:")
    for filename in created_files[:10]:
        print(f"  • {filename}")

    if len(created_files) > 10:
        print(f"  ... and {len(created_files) - 10} more\n")

    print("\nYou can now analyze these files with:")
    print(f"  python file_analyzer.py {base_path}\n")

    return str(base)

def generate_sample_content(filename, index):
    """Generate realistic sample content based on filename"""

    base_content = f"""Sample Document - {filename}
Created for testing the file analyzer

"""

    # Add content based on file type
    if 'COUN' in filename.upper() or 'PSY' in filename.upper():
        base_content += """Course: Counseling Psychology
Semester: Spring 2025

This is a sample academic document for COUN5241 or COUN5254.
Topics covered include therapy techniques, assessment methods,
and clinical supervision.

Key concepts:
- Cognitive Behavioral Therapy
- Client-centered approaches
- Ethical considerations in counseling
- Assessment and diagnosis

Assignment requirements:
1. Research current literature
2. Develop case study analysis
3. Present findings in class

"""

    elif 'therapy' in filename.lower() or 'session' in filename.lower():
        base_content += """Clinical Session Notes

Client ID: [Confidential]
Session Date: 2025-03-15
Duration: 50 minutes

Progress notes:
- Client reported improved mood
- Discussed coping strategies
- Homework assigned for next session

Next appointment scheduled.

"""

    elif 'assignment' in filename.lower():
        base_content += """Assignment Submission

Student Name: [Sample]
Course: COUN5241
Due Date: 2025-04-01

This assignment explores the intersection of counseling theory
and practical application in clinical settings.

Introduction:
The field of counseling psychology requires both theoretical
knowledge and practical skills...

"""

    elif 'resume' in filename.lower() or 'cover letter' in filename.lower():
        base_content += """Professional Document

[Your Name]
[Contact Information]

Objective:
Seeking position in counseling psychology field...

Education:
- Master's in Counseling Psychology
- Graduate coursework in clinical practice

Experience:
- Practicum at community mental health center
- Internship in university counseling center

"""

    elif 'invoice' in filename.lower() or 'contract' in filename.lower():
        base_content += """Business Document

Date: 2025-03-15
Invoice #: INV-001

Services rendered:
- Consulting services
- Project management
- Client meetings

Total amount due: $XXX.XX

Payment terms: Net 30 days

"""

    else:
        base_content += """General Document

This is a sample file created for testing purposes.
It contains generic content to simulate real documents.

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Document ID: {index}
Date: 2025-03-15

"""

    # Add some random variation
    if index % 3 == 0:
        base_content += "\nAdditional notes: This document needs revision.\n"
    elif index % 3 == 1:
        base_content += "\nStatus: Final version\n"
    else:
        base_content += "\nStatus: Draft\n"

    return base_content.format(index=index)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Create test files for analyzer')
    parser.add_argument('--path', default='./test_files',
                       help='Directory to create test files in (default: ./test_files)')
    parser.add_argument('--count', type=int, default=50,
                       help='Number of test files to create (default: 50)')

    args = parser.parse_args()

    create_test_directory(args.path, args.count)

if __name__ == '__main__':
    main()
