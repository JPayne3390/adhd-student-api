# 📊 File Analysis and Renaming Strategy Tool

A comprehensive Python tool designed to analyze large collections of files with inconsistent naming, detect patterns, and recommend optimal renaming strategies.

## 🎯 Purpose

This tool helps you:
- **Scan and analyze** thousands of files in your OneDrive or any directory
- **Extract patterns** like course codes (COUN5241, COUN5254), dates, and semesters
- **Categorize files** into academic, business, personal, counseling, and administrative
- **Detect naming issues** like duplicates, excessive length, inconsistent formatting
- **Generate recommendations** for optimal naming conventions
- **Create reports** for review before performing bulk renaming operations

## 🚀 Quick Start

### Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Analyze a directory (analyzes up to 200 files by default)
python file_analyzer.py /path/to/your/folder

# Analyze with custom file limit
python file_analyzer.py /path/to/your/folder --max-files 150

# Analyze only current directory (no subdirectories)
python file_analyzer.py /path/to/your/folder --no-recursive

# Save report to custom location
python file_analyzer.py /path/to/your/folder --output my_custom_report.json

# Quiet mode (only save report, don't print)
python file_analyzer.py /path/to/your/folder --quiet
```

## 📋 What It Analyzes

### 1. File Types
- Counts and categorizes all file extensions (.pdf, .docx, .txt, etc.)
- Shows distribution percentages

### 2. Content Extraction
Extracts text content from:
- **Text files**: .txt, .md, .csv, .log, .json, .xml, .html
- **PDF files**: First 3 pages (requires PyPDF2)
- **Word documents**: First 20 paragraphs (requires python-docx)

### 3. Pattern Detection
Automatically detects:
- **Course codes**: COUN5241, PSY1001, etc.
- **Dates**: Various formats (MM-DD-YYYY, YYYY-MM-DD, etc.)
- **Semesters**: Spring 2024, Fall 2025, etc.
- **Keywords**: Extracts common words from filenames

### 4. Categorization
Intelligently categorizes files as:
- **Academic**: syllabi, assignments, lectures, notes, exams
- **Business**: invoices, contracts, proposals, budgets
- **Personal**: resumes, photos, family, health documents
- **Counseling**: therapy notes, assessments, clinical materials
- **Administrative**: forms, applications, schedules
- **Uncategorized**: Files that don't match patterns

## 📊 Report Output

The tool generates two outputs:

### 1. Console Report
Beautiful formatted report showing:
- File type distribution
- Category breakdown with sample files
- Detected course codes
- Top keywords in filenames
- Naming recommendations with pros/cons
- Specific findings and suggestions

### 2. JSON Report (file_analysis_report.json)
Detailed JSON file containing:
- Complete analysis metadata
- All file details (first 50 files with full info)
- Pattern detection results
- Category assignments
- Naming recommendations
- Implementation guidance

## 💡 Naming Convention Recommendations

The tool provides 4 naming strategies:

### 🏆 Hybrid Approach (RECOMMENDED)
```
{Category}/{CourseCode_or_Project}/{YYYY-MM-DD}_{Description}.{ext}

Examples:
Academic/COUN5241/2025-03-15_Week5_Lecture_Notes.pdf
Business/ClientA/2025-02-20_Proposal_Draft.docx
Personal/Medical/2025-01-10_Insurance_Card.pdf
```

**Pros:**
- Maximum clarity and flexibility
- Easy browsing by category OR course OR date
- Scales well with large collections
- Future-proof organization

### Other Options:
1. **Course-Based Naming**: Best for academic files
2. **Category-Based Naming**: Universal approach
3. **Chronological with Category**: Date-first organization

## 🔧 Advanced Usage

### Analyzing OneDrive Folders

```bash
# Windows OneDrive path
python file_analyzer.py "C:/Users/YourName/OneDrive/Documents" --max-files 200

# Mac OneDrive path
python file_analyzer.py "/Users/YourName/OneDrive/Documents" --max-files 200

# Linux (if using OneDrive sync)
python file_analyzer.py "~/OneDrive/Documents" --max-files 200
```

### Sample Workflow

```bash
# Step 1: Analyze a small sample first (100 files)
python file_analyzer.py /path/to/folder --max-files 100

# Step 2: Review the report
cat file_analysis_report.json

# Step 3: Once satisfied, analyze more files
python file_analyzer.py /path/to/folder --max-files 500

# Step 4: Review recommendations and choose naming convention

# Step 5: Implement renaming (see next steps)
```

## 📈 Understanding the Output

### File Type Distribution
Shows what types of files you have:
```
.pdf         450 files (45.0%)
.docx        300 files (30.0%)
.txt         150 files (15.0%)
```

### Category Detection
Groups files by detected category:
```
ACADEMIC - 600 files (60%)
  Sample files:
    • COUN5241_Assignment1.pdf
    • Lecture_Notes_Week3.docx
    • Exam_Study_Guide.pdf
```

### Course Codes
Lists all detected course codes:
```
COUN5241   - 45 files
COUN5254   - 38 files
PSY2001    - 22 files
```

### Top Keywords
Most common words in filenames:
```
assignment    (45)    lecture      (38)
notes         (67)    syllabus     (12)
exam          (23)    chapter      (31)
```

## 🎯 Next Steps After Analysis

1. **Review the report** - Look at categories, patterns, and recommendations
2. **Choose a naming convention** - Select the one that fits your needs
3. **Test on a small subset** - Manually rename 10-20 files using your chosen convention
4. **Validate the approach** - Make sure it works for your workflow
5. **Prepare for bulk renaming** - Create a renaming script or use the recommended structure
6. **Always backup first** - Copy files before any bulk operations!

## ⚠️ Important Notes

- The tool is **read-only** - it analyzes but doesn't rename files
- Always **backup your files** before any bulk operations
- Start with a **small sample** (100-200 files) to validate patterns
- Review the JSON report for complete details
- Course code detection works for standard formats (e.g., ABC1234, ABCD1234)

## 🔍 Troubleshooting

### "No files found"
- Check that the directory path is correct
- Ensure you have read permissions
- Try without `--no-recursive` flag

### "Could not extract content from PDF/DOCX"
- Install dependencies: `pip install PyPDF2 python-docx`
- Some files may be corrupted or password-protected
- The tool will skip problematic files and continue

### "Analysis taking too long"
- Reduce `--max-files` to a smaller number
- Use `--no-recursive` to skip subdirectories
- Content extraction from PDFs can be slow for large files

## 📝 Example Output

```
================================================================================
📊 FILE ANALYSIS REPORT
================================================================================

📅 Analysis Date: 2025-11-09 14:30:00
📁 Total Files Analyzed: 200

================================================================================
📋 FILE TYPES DISTRIBUTION
================================================================================
  .pdf                   120 files ( 60.0%)
  .docx                   50 files ( 25.0%)
  .txt                    20 files ( 10.0%)
  .xlsx                   10 files (  5.0%)

================================================================================
🗂️  CATEGORIES DETECTED
================================================================================

  📌 ACADEMIC - 150 files (75.0%)
     Sample files:
       • COUN5241_Assignment_1_Draft.pdf
       • Lecture_Notes_Week_5.docx
       • Final_Exam_Study_Guide.pdf

  📌 PERSONAL - 30 files (15.0%)
     Sample files:
       • Resume_Updated_2025.docx
       • Cover_Letter_Template.docx

================================================================================
🎓 COURSE CODES DETECTED
================================================================================
  COUN5241   -  45 files
             Sample: COUN5241_Assignment_1_Draft.pdf
  COUN5254   -  38 files
             Sample: COUN5254_Week3_Reading.pdf

================================================================================
💡 RENAMING RECOMMENDATIONS
================================================================================

────────────────────────────────────────────────────────────────────────────────
  🏆 HYBRID APPROACH (RECOMMENDED)
────────────────────────────────────────────────────────────────────────────────
  Pattern: {Category}/{CourseCode_or_Project}/{YYYY-MM-DD}_{Description}.{ext}
  Example: Academic/COUN5241/2025-03-15_Week5_Lecture_Notes.pdf
  ...
```

## 🤝 Support

For issues or questions:
1. Check this README first
2. Review the generated JSON report for details
3. Test with a small sample directory first
4. Ensure all dependencies are installed

## 📜 License

This tool is part of the ADHD Student API project.

---

**Remember:** This tool only analyzes and recommends. Always review recommendations and test on a small sample before any bulk renaming operations!
