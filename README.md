# File Management Utilities

A collection of Python scripts for file management and analysis.

## Scripts

### 1. Duplicate File Finder (`find_duplicate_files.py`)
A Python script that finds and organizes duplicate files by moving them to a separate directory while preserving folder structure. Includes optional CSV tracking for complete audit trails.

### 2. File Creation Date Utility (`get_file_creation_date.py`)
A cross-platform Python script to get the creation date of files and directories recursively, handling platform-specific differences for accurate file creation time retrieval.

### 3. File Organization by Date (`organize_by_date.py`)
A utility that moves files from a source folder to destination folders organized by creation date in YYYY-MM format. Uses the creation date detection from `get_file_creation_date.py` for accurate cross-platform date handling.

## Features

- **Fast duplicate detection** using SHA-256 hash comparison
- **Preserves directory structure** when moving duplicates
- **Safe operation** - skips files already in the destination folder
- **Verbose output** - shows progress and file operations
- **CSV tracking** - optional logging of all processed and moved files
- **Cross-platform** - works on Windows, macOS, and Linux
- **Security hardened** - includes path traversal protection and input validation

## Security Features

- **Path validation** - Validates all input paths and prevents directory traversal attacks
- **Symlink protection** - Safely handles or skips symbolic links to prevent attacks
- **Permission checks** - Verifies read/write permissions before operations
- **Input sanitization** - Validates command-line arguments and file paths
- **Cryptographic security** - Uses SHA-256 instead of MD5 for file hashing
- **Information disclosure protection** - Limits sensitive information in output

## Requirements

- Python 3.8+ (uses walrus operator `:=`)
- No external dependencies (uses only standard library)

## Usage

### Basic Syntax

```bash
python find_duplicate_files.py --source-folder SOURCE_PATH --dest-folder DEST_PATH [--csv-log CSV_PATH]
```

### Arguments

- `--source-folder`: Path to the directory to search for duplicates
- `--dest-folder`: Path to the directory where duplicates will be moved
- `--csv-log` (optional): Path to CSV file for tracking all processed and moved files

### Examples

```bash
# Basic usage - Clean up Downloads folder
python find_duplicate_files.py --source-folder ~/Downloads --dest-folder ~/Downloads/duplicates

# With CSV tracking - Organize photo library
python find_duplicate_files.py --source-folder /Users/photos --dest-folder /Users/photo_duplicates --csv-log photo_audit.csv

# Clean up project files with detailed logging
python find_duplicate_files.py --source-folder ./my_project --dest-folder ./my_project/duplicates --csv-log project_cleanup.csv
```

## How It Works

1. **Validates** input paths and permissions
2. **Scans** the source directory recursively
3. **Calculates SHA-256 hash** for each file (skipping symlinks for security)
4. **Groups files** with identical hashes
5. **Keeps the first file** in each group in its original location
6. **Moves all duplicates** to the destination folder with preserved path structure
7. **Logs operations** to CSV file (if specified)

## CSV Tracking

When using the `--csv-log` option, the script creates a detailed audit trail of all operations:

### CSV Columns

- `timestamp` - When the operation occurred (ISO format)
- `operation` - Type of operation (`processed` or `moved`)
- `original_path` - Full path to the original file
- `destination_path` - Path where file was moved (empty for processed files)
- `file_hash` - SHA-256 hash of the file
- `file_size` - File size in bytes
- `modification_time` - File's last modification timestamp
- `status` - Operation result (`success` or `error`)
- `error_message` - Error details (if applicable)

### Example CSV Output

```csv
timestamp,operation,original_path,destination_path,file_hash,file_size,modification_time,status,error_message
2024-02-15T10:30:15.123456,processed,/source/image.jpg,,abc123def456...,1024768,1708012345.67,success,
2024-02-15T10:30:16.234567,moved,/source/duplicate.jpg,/dest/duplicate.jpg,abc123def456...,1024768,1708012345.67,success,
2024-02-15T10:30:17.345678,processed,/source/protected.doc,,,0,0,error,Permission denied
```

### Benefits of CSV Tracking

- **Audit trail** - Complete record of what was processed and moved
- **Error tracking** - Identify files that couldn't be processed
- **Data analysis** - Import into spreadsheets for further analysis
- **Rollback assistance** - Detailed information for undoing operations
- **Compliance** - Meet audit requirements for file operations

## Safety Features

- Files already in the destination folder are automatically skipped
- Directory structure is preserved in the destination
- Only moves files (doesn't delete anything permanently)
- Handles file access errors gracefully

## Important Notes

⚠️ **This script moves files, not copies them.** Duplicates will be removed from their original locations.

🔒 **Safety Tip:** Always test on a small sample or create backups before running on important data.

📁 **Directory Structure:** The relative path structure is maintained in the destination folder.

## Example Output

### Basic Usage
```
Finding duplicate files...
Scanning: /Users/daniel/Downloads
Processing file: image1.jpg
Processing file: image1_copy.jpg
Unique files found: 1
Duplicates found: 1
Moving 1 duplicates to: /Users/daniel/Downloads/duplicates
Moved: image1_copy.jpg -> image1_copy.jpg
Done
```

### With CSV Tracking
```
Initialized CSV log: tracking.csv
Finding duplicate files...
Scanning: /Users/daniel/Downloads
Processing file: image1.jpg
Processing file: image1_copy.jpg
Unique files found: 1
Duplicates found: 1
Moving 1 duplicates to: /Users/daniel/Downloads/duplicates
Moved: image1_copy.jpg -> image1_copy.jpg
Done
```

---

## File Creation Date Utility

### Features

- **Cross-platform compatibility** - Works on Windows, macOS, and Linux
- **Accurate creation dates** - Uses platform-specific methods for true creation time
- **Recursive directory processing** - Process entire directory trees with filtering options
- **Multiple output formats** - readable, JSON, CSV, and timestamp formats
- **Advanced filtering** - Include/exclude patterns, max depth control, file type filtering
- **Batch processing** - Handle thousands of files efficiently with progress indicators
- **Safe operation** - Comprehensive error handling and input validation
- **Performance optimized** - Progress indicators for large batches, quiet mode for automation

### Platform Differences

- **Windows**: Uses `st_ctime` for true file creation time
- **macOS**: Uses `st_birthtime` for true file creation time (when available)
- **Linux**: Uses `st_ctime` (metadata change time) as creation time is not typically available

### Usage

```bash
# Single file
python get_file_creation_date.py file.txt

# Multiple files with JSON output
python get_file_creation_date.py file1.txt file2.txt --format json

# Process entire directory recursively
python get_file_creation_date.py /path/to/directory

# Directory with specific file types only
python get_file_creation_date.py /project --include "*.py" "*.js" "*.txt"

# Directory excluding certain files
python get_file_creation_date.py /logs --exclude "*.tmp" "*.log"

# Limit recursion depth
python get_file_creation_date.py /deep/directory --max-depth 3

# CSV format for spreadsheet analysis
python get_file_creation_date.py /data --format csv --include "*.csv"

# Count files without processing
python get_file_creation_date.py /large/directory --count

# Quiet mode for automation (no progress indicators)
python get_file_creation_date.py /project --quiet --format json

# Raw timestamp for scripting
python get_file_creation_date.py document.pdf --format timestamp
```

### Advanced Usage Examples

```bash
# Process only Python and JavaScript files in a project
python get_file_creation_date.py ./my_project --include "*.py" "*.js" --exclude "test_*"

# Generate CSV report of all images in a directory tree
python get_file_creation_date.py ~/Pictures --include "*.jpg" "*.png" "*.gif" --format csv > image_report.csv

# Quick file count for different file types
python get_file_creation_date.py /var/log --include "*.log" --count
python get_file_creation_date.py /var/log --include "*.err" --count

# Process large directory with progress indicators
python get_file_creation_date.py /massive/dataset --format json > creation_dates.json

# Non-recursive processing (current directory only)
python get_file_creation_date.py /some/dir --no-recursive
```

### Command Line Options

- `--recursive`, `-r`: Force recursive processing of directories (default for directories)
- `--no-recursive`: Disable recursive processing (process only files in specified directories)
- `--max-depth N`: Limit recursion depth to N levels
- `--include PATTERN [PATTERN ...]`: Include only files matching these glob patterns
- `--exclude PATTERN [PATTERN ...]`: Exclude files matching these glob patterns
- `--format`, `-f`: Output format (readable, json, csv, timestamp)
- `--count`: Show only the number of files that would be processed
- `--quiet`, `-q`: Suppress progress indicators and warnings (useful for automation)

### Filtering

The utility supports powerful filtering options:

- **Include patterns**: Only process files matching specified glob patterns
- **Exclude patterns**: Skip files matching specified patterns (applied after include)
- **Default exclusions**: Automatically skips hidden files (.*), temporary files (*.tmp, *.swp, *.bak), and system files (__pycache__, .DS_Store)
- **Depth control**: Limit how deep to recurse into directory structures

### Output Formats

#### Readable (default)
```
File: /path/to/file.txt
Creation Date: 2024-02-15 10:30:15
Creation Date (ISO): 2024-02-15T10:30:15.123456
Creation Timestamp: 1708012215.123456
Source: st_birthtime (macOS creation time)
Platform: darwin

Additional Information:
  Modification Date: 2024-02-15 10:35:20
  Access Date: 2024-02-15 10:40:25
  File Size: 1,024 bytes
```

#### JSON
```json
{
  "file_path": "/path/to/file.txt",
  "creation_timestamp": 1708012215.123456,
  "creation_date": "2024-02-15T10:30:15.123456",
  "creation_date_readable": "2024-02-15 10:30:15",
  "source": "st_birthtime (macOS creation time)",
  "platform": "darwin",
  "modification_time": 1708012520.789012,
  "modification_date": "2024-02-15T10:35:20.789012",
  "access_time": 1708012825.345678,
  "access_date": "2024-02-15T10:40:25.345678",
  "file_size": 1024
}
```

#### CSV
```csv
file_path,creation_timestamp,creation_date,source,platform
/path/to/file.txt,1708012215.123456,2024-02-15T10:30:15.123456,st_birthtime (macOS creation time),darwin
```

#### Timestamp
```
1708012215.123456
```

---

## File Organization by Date

### Features

- **Date-based organization** - Automatically creates YYYY-MM folder structure
- **Cross-platform date detection** - Uses functions from `get_file_creation_date.py`
- **Safe operation** - Handles filename conflicts by appending numbers
- **Dry run mode** - Preview changes before actually moving files
- **Advanced filtering** - Include/exclude patterns for selective processing
- **Progress indicators** - Shows progress for large file batches
- **Recursive processing** - Processes entire directory trees

### Usage

```bash
# Basic usage - organize all files by date
python organize_by_date.py source_folder dest_folder

# Dry run to preview what would be done
python organize_by_date.py data moved --dry-run

# Process only specific file types
python organize_by_date.py data moved --include "*.jpg" "*.png" "*.gif"

# Exclude unwanted files
python organize_by_date.py data moved --exclude "*.tmp" "Thumbs.db" "*.DS_Store"

# Quiet mode for automation
python organize_by_date.py data moved --quiet
```

### How It Works

1. **Scans source folder** recursively for files
2. **Gets creation date** using cross-platform detection
3. **Creates YYYY-MM folders** in destination directory
4. **Moves files** to appropriate date folder
5. **Handles conflicts** by appending numbers to duplicate filenames
6. **Shows progress** and provides detailed summary

### Example Output

```
Moving 176 files from /source to /destination

Moved: IMG_3156.JPG -> 2025-08/
Moved: IMG_3157.JPG -> 2025-08/
Moved: vacation_photo.jpg -> 2024-07/
Progress: 50/176 (28.4%)
...

Summary:
  Files processed: 176
  Files moved: 176
  Errors: 0
  Date folders created: 3
  Folders: 2024-07, 2024-12, 2025-08
```

### Command Line Options

- `--dry-run`: Preview changes without actually moving files
- `--include PATTERN [PATTERN ...]`: Include only files matching these patterns
- `--exclude PATTERN [PATTERN ...]`: Exclude files matching these patterns  
- `--quiet`, `-q`: Suppress progress output (useful for automation)

---

## License

This project is open source and available under the MIT License.
