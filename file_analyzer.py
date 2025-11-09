#!/usr/bin/env python3
"""
File Analysis and Renaming Strategy Tool
Analyzes files in a directory to detect patterns, categories, and propose renaming conventions.
"""

import os
import re
import json
import mimetypes
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import hashlib

try:
    # For PDF processing
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    # For DOCX processing
    from docx import Document
except ImportError:
    Document = None


class FileAnalyzer:
    """Analyzes files to extract metadata, content, and detect patterns"""

    def __init__(self, max_files=200, max_content_length=1000):
        self.max_files = max_files
        self.max_content_length = max_content_length
        self.files_analyzed = []
        self.patterns = defaultdict(list)
        self.categories = defaultdict(list)
        self.course_codes = defaultdict(list)
        self.file_types = Counter()
        self.keywords = Counter()

        # Pattern definitions
        self.course_code_pattern = re.compile(r'\b([A-Z]{3,4}\s?\d{4})\b')
        self.date_pattern = re.compile(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b')
        self.semester_pattern = re.compile(r'\b(Spring|Summer|Fall|Winter)\s?(\d{4})\b', re.IGNORECASE)

        # Category keywords
        self.category_keywords = {
            'academic': ['syllabus', 'assignment', 'homework', 'lecture', 'notes', 'exam',
                        'quiz', 'study', 'course', 'textbook', 'reading', 'paper', 'essay',
                        'research', 'thesis', 'dissertation', 'grade', 'student'],
            'business': ['invoice', 'receipt', 'contract', 'agreement', 'proposal', 'budget',
                        'financial', 'revenue', 'expense', 'tax', 'payroll', 'client', 'meeting'],
            'personal': ['resume', 'cv', 'cover letter', 'personal', 'family', 'photo', 'image',
                        'vacation', 'travel', 'recipe', 'health', 'medical', 'insurance'],
            'counseling': ['therapy', 'counseling', 'psychology', 'mental health', 'assessment',
                          'client notes', 'supervision', 'practicum', 'internship', 'clinical'],
            'administrative': ['form', 'application', 'registration', 'enrollment', 'transcript',
                             'schedule', 'calendar', 'agenda', 'minutes', 'memo']
        }

    def analyze_directory(self, directory_path, recursive=True):
        """Analyze all files in the specified directory"""
        print(f"\n{'='*80}")
        print(f"ANALYZING DIRECTORY: {directory_path}")
        print(f"{'='*80}\n")

        path = Path(directory_path)
        if not path.exists():
            print(f"❌ Error: Directory '{directory_path}' does not exist!")
            return None

        # Get all files
        if recursive:
            files = list(path.rglob('*'))
        else:
            files = list(path.glob('*'))

        # Filter out directories
        files = [f for f in files if f.is_file()]

        print(f"📁 Found {len(files)} total files")
        print(f"📊 Analyzing up to {self.max_files} files...\n")

        # Limit number of files
        files_to_analyze = files[:self.max_files]

        # Analyze each file
        for idx, file_path in enumerate(files_to_analyze, 1):
            if idx % 10 == 0:
                print(f"   Progress: {idx}/{len(files_to_analyze)} files analyzed...")

            file_info = self._analyze_file(file_path)
            if file_info:
                self.files_analyzed.append(file_info)

        print(f"\n✅ Analysis complete! Processed {len(self.files_analyzed)} files\n")

        # Generate summary
        return self._generate_summary()

    def _analyze_file(self, file_path):
        """Analyze a single file and extract information"""
        try:
            file_info = {
                'path': str(file_path),
                'name': file_path.name,
                'stem': file_path.stem,
                'extension': file_path.suffix.lower(),
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'content_snippet': '',
                'detected_patterns': {},
                'suggested_category': None
            }

            # Track file type
            self.file_types[file_info['extension']] += 1

            # Extract content based on file type
            content = self._extract_content(file_path)
            file_info['content_snippet'] = content[:self.max_content_length] if content else ''

            # Analyze filename
            filename_lower = file_path.name.lower()

            # Detect course codes in filename and content
            course_codes_found = self.course_code_pattern.findall(file_path.name)
            if content:
                course_codes_found.extend(self.course_code_pattern.findall(content[:500]))

            if course_codes_found:
                # Normalize course codes (remove spaces)
                normalized_codes = [code.replace(' ', '') for code in course_codes_found]
                file_info['detected_patterns']['course_codes'] = list(set(normalized_codes))
                for code in normalized_codes:
                    self.course_codes[code].append(file_path.name)

            # Detect dates
            dates_found = self.date_pattern.findall(file_path.name)
            if dates_found:
                file_info['detected_patterns']['dates'] = dates_found

            # Detect semesters
            semesters_found = self.semester_pattern.findall(file_path.name)
            if semesters_found:
                file_info['detected_patterns']['semesters'] = [f"{s[0]} {s[1]}" for s in semesters_found]

            # Categorize file
            category = self._categorize_file(filename_lower, content)
            file_info['suggested_category'] = category
            if category:
                self.categories[category].append(file_path.name)

            # Extract keywords from filename
            # Remove extension and split by common separators
            words = re.split(r'[-_\s.]+', file_path.stem.lower())
            for word in words:
                if len(word) > 3 and not word.isdigit():  # Filter short words and numbers
                    self.keywords[word] += 1

            return file_info

        except Exception as e:
            print(f"⚠️  Warning: Could not analyze {file_path.name}: {e}")
            return None

    def _extract_content(self, file_path):
        """Extract text content from various file types"""
        extension = file_path.suffix.lower()

        try:
            # Text files
            if extension in ['.txt', '.md', '.csv', '.log', '.json', '.xml', '.html']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(5000)  # Read first 5000 chars

            # PDF files
            elif extension == '.pdf' and PyPDF2:
                return self._extract_pdf_content(file_path)

            # Word documents
            elif extension in ['.docx'] and Document:
                return self._extract_docx_content(file_path)

            # For other files, just return empty string
            else:
                return ''

        except Exception as e:
            return ''

    def _extract_pdf_content(self, file_path):
        """Extract text from PDF files"""
        if not PyPDF2:
            return ''

        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ''
                # Read first 3 pages max
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                return text[:5000]
        except:
            return ''

    def _extract_docx_content(self, file_path):
        """Extract text from Word documents"""
        if not Document:
            return ''

        try:
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs[:20]])  # First 20 paragraphs
            return text[:5000]
        except:
            return ''

    def _categorize_file(self, filename, content):
        """Categorize file based on filename and content"""
        combined_text = f"{filename} {content[:500] if content else ''}".lower()

        # Score each category
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in combined_text)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        return 'uncategorized'

    def _generate_summary(self):
        """Generate comprehensive summary report"""
        summary = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_files_analyzed': len(self.files_analyzed),
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'file_types': dict(self.file_types.most_common()),
            'categories': {
                category: {
                    'count': len(files),
                    'percentage': round(len(files) / len(self.files_analyzed) * 100, 1),
                    'sample_files': files[:5]
                }
                for category, files in self.categories.items()
            },
            'course_codes': {
                code: {
                    'count': len(files),
                    'sample_files': files[:5]
                }
                for code, files in sorted(self.course_codes.items(),
                                         key=lambda x: len(x[1]), reverse=True)
            },
            'top_keywords': dict(self.keywords.most_common(30)),
            'files_details': self.files_analyzed[:50]  # Include details for first 50 files
        }

        return summary

    def generate_naming_recommendations(self, summary):
        """Generate naming convention recommendations based on analysis"""
        recommendations = {
            'analysis_summary': {
                'total_files': summary['analysis_metadata']['total_files_analyzed'],
                'categories_found': len(summary['categories']),
                'course_codes_found': len(summary['course_codes']),
                'file_types': len(summary['file_types'])
            },
            'recommended_conventions': []
        }

        # Recommendation 1: Course-based naming (if course codes detected)
        if summary['course_codes']:
            recommendations['recommended_conventions'].append({
                'priority': 1,
                'name': 'Course-Based Naming',
                'pattern': '{CourseCode}_{Category}_{Description}_{Date}.{ext}',
                'example': 'COUN5241_Assignment_Research_Paper_2025-03-15.docx',
                'use_case': 'Academic files with course codes',
                'applicable_files': sum(len(files) for files in self.course_codes.values()),
                'pros': [
                    'Easy to find files by course',
                    'Clear academic organization',
                    'Supports semester-based filing'
                ],
                'cons': [
                    'Requires course code detection',
                    'Not suitable for non-academic files'
                ]
            })

        # Recommendation 2: Category-based naming
        recommendations['recommended_conventions'].append({
            'priority': 2,
            'name': 'Category-Based Naming',
            'pattern': '{Category}/{Subcategory}_{Description}_{Date}.{ext}',
            'example': 'Academic/Counseling_Therapy_Notes_Week5_2025-03-15.pdf',
            'use_case': 'All file types organized by category',
            'applicable_files': len(self.files_analyzed),
            'pros': [
                'Universal - works for all file types',
                'Clear organizational structure',
                'Easy to browse by category'
            ],
            'cons': [
                'May require manual category verification',
                'Longer file paths'
            ]
        })

        # Recommendation 3: Date-based with category
        recommendations['recommended_conventions'].append({
            'priority': 3,
            'name': 'Chronological with Category Prefix',
            'pattern': '{YYYY-MM-DD}_{Category}_{Description}.{ext}',
            'example': '2025-03-15_Academic_COUN5241_Lecture_Notes.pdf',
            'use_case': 'Files where date is important',
            'applicable_files': len(self.files_analyzed),
            'pros': [
                'Automatic chronological sorting',
                'Easy to find recent files',
                'Good for ongoing projects'
            ],
            'cons': [
                'Date must be known/detected',
                'Less intuitive for topic-based searches'
            ]
        })

        # Recommendation 4: Hybrid approach (RECOMMENDED)
        recommendations['recommended_conventions'].append({
            'priority': 0,  # Highest priority
            'name': '🏆 HYBRID APPROACH (RECOMMENDED)',
            'pattern': '{Category}/{CourseCode_or_Project}/{YYYY-MM-DD}_{Description}.{ext}',
            'example': 'Academic/COUN5241/2025-03-15_Week5_Lecture_Notes.pdf',
            'use_case': 'Best of all worlds - category, course/project, date, description',
            'applicable_files': len(self.files_analyzed),
            'pros': [
                'Maximum flexibility and clarity',
                'Easy browsing by category OR course OR date',
                'Scales well with large file collections',
                'Future-proof organization'
            ],
            'cons': [
                'Requires more initial setup',
                'Longer file paths'
            ],
            'implementation_steps': [
                '1. Create main category folders (Academic, Business, Personal, etc.)',
                '2. Within each category, create subfolders by course code or project name',
                '3. Rename files with date prefix and descriptive name',
                '4. Maintain consistent date format (YYYY-MM-DD for sorting)',
                '5. Keep descriptions concise but meaningful (3-5 words)'
            ]
        })

        # Add specific recommendations based on what was found
        recommendations['specific_findings'] = {}

        if summary['course_codes']:
            recommendations['specific_findings']['courses'] = {
                'message': f"Found {len(summary['course_codes'])} unique course codes",
                'top_courses': list(summary['course_codes'].keys())[:10],
                'suggestion': 'Create a folder structure: Academic/[CourseCode]/...'
            }

        if summary['categories']:
            top_category = max(summary['categories'].items(),
                             key=lambda x: x[1]['count'])
            recommendations['specific_findings']['primary_category'] = {
                'name': top_category[0],
                'percentage': top_category[1]['percentage'],
                'message': f"'{top_category[0]}' is your primary category ({top_category[1]['percentage']}% of files)",
                'suggestion': f'Consider creating main folder for {top_category[0]} materials'
            }

        # Identify problematic file names
        problematic_patterns = []
        for file_info in self.files_analyzed[:50]:
            name = file_info['name']
            if len(name) > 100:
                problematic_patterns.append('Very long filenames detected')
            if re.search(r'\(\d+\)', name):
                problematic_patterns.append('Duplicate markers found (e.g., "file (1).pdf")')
            if re.search(r'[A-Z]{10,}', name):
                problematic_patterns.append('All-caps sections in filenames')
            if name.count('_') > 5 or name.count('-') > 5:
                problematic_patterns.append('Excessive separators in filenames')

        if problematic_patterns:
            recommendations['specific_findings']['issues'] = {
                'problems_detected': list(set(problematic_patterns)),
                'suggestion': 'Renaming will fix these inconsistencies'
            }

        return recommendations

    def save_report(self, summary, recommendations, output_file='file_analysis_report.json'):
        """Save analysis report to JSON file"""
        report = {
            'summary': summary,
            'recommendations': recommendations
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Full report saved to: {output_file}")
        return output_file

    def print_report(self, summary, recommendations):
        """Print formatted report to console"""
        print("\n" + "="*80)
        print("📊 FILE ANALYSIS REPORT")
        print("="*80)

        # Metadata
        meta = summary['analysis_metadata']
        print(f"\n📅 Analysis Date: {meta['analysis_date']}")
        print(f"📁 Total Files Analyzed: {meta['total_files_analyzed']}")

        # File Types
        print(f"\n{'='*80}")
        print("📋 FILE TYPES DISTRIBUTION")
        print(f"{'='*80}")
        for ext, count in sorted(summary['file_types'].items(),
                                 key=lambda x: x[1], reverse=True):
            percentage = (count / meta['total_files_analyzed']) * 100
            ext_display = ext if ext else '(no extension)'
            print(f"  {ext_display:20} {count:5} files ({percentage:5.1f}%)")

        # Categories
        print(f"\n{'='*80}")
        print("🗂️  CATEGORIES DETECTED")
        print(f"{'='*80}")
        for category, data in sorted(summary['categories'].items(),
                                    key=lambda x: x[1]['count'], reverse=True):
            print(f"\n  📌 {category.upper()} - {data['count']} files ({data['percentage']}%)")
            print(f"     Sample files:")
            for filename in data['sample_files'][:3]:
                print(f"       • {filename}")

        # Course Codes
        if summary['course_codes']:
            print(f"\n{'='*80}")
            print("🎓 COURSE CODES DETECTED")
            print(f"{'='*80}")
            for code, data in list(summary['course_codes'].items())[:15]:
                print(f"  {code:10} - {data['count']:3} files")
                if data['sample_files']:
                    print(f"             Sample: {data['sample_files'][0]}")

        # Top Keywords
        print(f"\n{'='*80}")
        print("🔑 TOP KEYWORDS IN FILENAMES")
        print(f"{'='*80}")
        top_20_keywords = list(summary['top_keywords'].items())[:20]
        for i in range(0, len(top_20_keywords), 2):
            kw1, count1 = top_20_keywords[i]
            if i + 1 < len(top_20_keywords):
                kw2, count2 = top_20_keywords[i + 1]
                print(f"  {kw1:20} ({count1:3})    {kw2:20} ({count2:3})")
            else:
                print(f"  {kw1:20} ({count1:3})")

        # Recommendations
        print(f"\n{'='*80}")
        print("💡 RENAMING RECOMMENDATIONS")
        print(f"{'='*80}")

        for rec in sorted(recommendations['recommended_conventions'],
                         key=lambda x: x['priority']):
            print(f"\n{'─'*80}")
            print(f"  {rec['name']}")
            print(f"{'─'*80}")
            print(f"  Pattern: {rec['pattern']}")
            print(f"  Example: {rec['example']}")
            print(f"  Use Case: {rec['use_case']}")
            print(f"  Applicable to: {rec['applicable_files']} files")

            print(f"\n  ✅ Pros:")
            for pro in rec['pros']:
                print(f"     • {pro}")

            print(f"\n  ⚠️  Cons:")
            for con in rec['cons']:
                print(f"     • {con}")

            if 'implementation_steps' in rec:
                print(f"\n  📝 Implementation Steps:")
                for step in rec['implementation_steps']:
                    print(f"     {step}")

        # Specific Findings
        if recommendations['specific_findings']:
            print(f"\n{'='*80}")
            print("🔍 SPECIFIC FINDINGS & SUGGESTIONS")
            print(f"{'='*80}")

            for finding_type, finding_data in recommendations['specific_findings'].items():
                print(f"\n  📍 {finding_type.upper().replace('_', ' ')}")
                if 'message' in finding_data:
                    print(f"     {finding_data['message']}")
                if 'suggestion' in finding_data:
                    print(f"     💡 {finding_data['suggestion']}")
                if 'top_courses' in finding_data:
                    print(f"     Top courses: {', '.join(finding_data['top_courses'][:5])}")
                if 'problems_detected' in finding_data:
                    print(f"     Issues found:")
                    for problem in finding_data['problems_detected']:
                        print(f"       • {problem}")

        print(f"\n{'='*80}")
        print("✨ NEXT STEPS")
        print(f"{'='*80}")
        print("  1. Review the recommendations above")
        print("  2. Choose your preferred naming convention")
        print("  3. Test the renaming on a small subset (10-20 files)")
        print("  4. Once satisfied, proceed with batch renaming")
        print("  5. Always keep backups before bulk operations!")
        print(f"{'='*80}\n")


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze files and propose renaming strategies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  python file_analyzer.py .

  # Analyze specific folder with limit
  python file_analyzer.py /path/to/folder --max-files 150

  # Analyze without recursion
  python file_analyzer.py /path/to/folder --no-recursive

  # Save report to custom location
  python file_analyzer.py /path/to/folder --output my_report.json
        """
    )

    parser.add_argument('directory', help='Directory to analyze')
    parser.add_argument('--max-files', type=int, default=200,
                       help='Maximum number of files to analyze (default: 200)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not analyze subdirectories')
    parser.add_argument('--output', default='file_analysis_report.json',
                       help='Output file for JSON report (default: file_analysis_report.json)')
    parser.add_argument('--quiet', action='store_true',
                       help='Only save report, do not print to console')

    args = parser.parse_args()

    # Create analyzer
    analyzer = FileAnalyzer(max_files=args.max_files)

    # Run analysis
    summary = analyzer.analyze_directory(
        args.directory,
        recursive=not args.no_recursive
    )

    if not summary:
        return 1

    # Generate recommendations
    recommendations = analyzer.generate_naming_recommendations(summary)

    # Print report
    if not args.quiet:
        analyzer.print_report(summary, recommendations)

    # Save report
    analyzer.save_report(summary, recommendations, args.output)

    return 0


if __name__ == '__main__':
    exit(main())
