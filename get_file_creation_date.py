#!/usr/bin/env python3
"""
File Creation Date Utility

A cross-platform Python script to get the creation date of files.
Handles platform-specific differences for file creation time retrieval.
"""

import os
import json
import platform
import argparse
import sys
import fnmatch
from datetime import datetime
from pathlib import Path


def get_creation_date(file_path: str) -> dict:
    """
    Get the creation date of a file across different platforms.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing creation date information
        
    Raises:
        OSError: If file doesn't exist or can't be accessed
        ValueError: If path is invalid
    """
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    path_obj = Path(file_path)
    
    # Check if file exists
    if not path_obj.exists():
        raise ValueError(f"File does not exist: {file_path}")
    
    # Check if it's actually a file (not a directory)
    if not path_obj.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Check read permissions
    if not os.access(path_obj, os.R_OK):
        raise PermissionError(f"No read permission for file: {file_path}")
    
    try:
        file_stat = path_obj.stat()
        system = platform.system().lower()
        
        creation_time = None
        creation_source = ""
        
        if system == "windows":
            # Windows: st_ctime is creation time
            creation_time = file_stat.st_ctime
            creation_source = "st_ctime (Windows creation time)"
            
        elif system == "darwin":  # macOS
            # macOS: Check if st_birthtime is available (creation time)
            if hasattr(file_stat, 'st_birthtime'):
                creation_time = file_stat.st_birthtime
                creation_source = "st_birthtime (macOS creation time)"
            else:
                # Fallback to ctime (metadata change time)
                creation_time = file_stat.st_ctime
                creation_source = "st_ctime (metadata change time - creation time not available)"
                
        else:  # Linux and other Unix-like systems
            # Linux: Generally no true creation time available
            # st_ctime is metadata change time, not creation time
            creation_time = file_stat.st_ctime
            creation_source = "st_ctime (metadata change time - creation time not available on this system)"
        
        # Convert to datetime object
        creation_datetime = datetime.fromtimestamp(creation_time)
        
        return {
            "file_path": str(path_obj.resolve()),
            "creation_timestamp": creation_time,
            "creation_date": creation_datetime.isoformat(),
            "creation_date_readable": creation_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "source": creation_source,
            "platform": system,
            "modification_time": file_stat.st_mtime,
            "modification_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "access_time": file_stat.st_atime,
            "access_date": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
            "file_size": file_stat.st_size
        }
        
    except OSError as e:
        raise OSError(f"Error accessing file {file_path}: {e}") from e


def format_output(file_info: dict, output_format: str = "readable") -> str:
    """
    Format the file information for output.
    
    Args:
        file_info: Dictionary containing file information
        output_format: Output format ('readable', 'json', 'csv', 'timestamp')
        
    Returns:
        Formatted string
    """
    if output_format == "json":

        return json.dumps(file_info, indent=2)
    
    elif output_format == "csv":
        return f"{file_info['file_path']},{file_info['creation_timestamp']},{file_info['creation_date']},{file_info['source']},{file_info['platform']}"
    
    elif output_format == "timestamp":
        return str(file_info['creation_timestamp'])
    
    else:  # readable format (default)
        return f"""File: {file_info['file_path']}
Creation Date: {file_info['creation_date_readable']}
Creation Date (ISO): {file_info['creation_date']}
Creation Timestamp: {file_info['creation_timestamp']}
Source: {file_info['source']}
Platform: {file_info['platform']}

Additional Information:
  Modification Date: {datetime.fromtimestamp(file_info['modification_time']).strftime('%Y-%m-%d %H:%M:%S')}
  Access Date: {datetime.fromtimestamp(file_info['access_time']).strftime('%Y-%m-%d %H:%M:%S')}
  File Size: {file_info['file_size']:,} bytes"""


def collect_files_from_paths(paths: list, recursive: bool = True, max_depth: int = None, 
                            include_patterns: list = None, exclude_patterns: list = None, quiet: bool = False) -> list:
    """
    Collect all files from the given paths, expanding directories recursively if needed.
    
    Args:
        paths: List of file or directory paths
        recursive: Whether to process directories recursively
        max_depth: Maximum recursion depth (None for unlimited)
        include_patterns: List of glob patterns to include (e.g., ['*.txt', '*.py'])
        exclude_patterns: List of glob patterns to exclude (e.g., ['*.tmp', '.*'])
        
    Returns:
        List of file paths to process
    """
    collected_files = []
    
    # Default exclude patterns to skip common unwanted files
    if exclude_patterns is None:
        exclude_patterns = ['.*', '*.tmp', '*.swp', '*.bak', '__pycache__', '.DS_Store']
    
    def should_include_file(file_path: Path) -> bool:
        """Check if file should be included based on patterns."""
        filename = file_path.name
        
        # Check exclude patterns first
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                return False
        
        # If include patterns are specified, file must match at least one
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                    return True
            return False
        
        return True
    
    def walk_directory(dir_path: Path, current_depth: int = 0) -> None:
        """Recursively walk directory and collect files."""
        if max_depth is not None and current_depth > max_depth:
            return
            
        try:
            for item in dir_path.iterdir():
                if item.is_file():
                    if should_include_file(item):
                        collected_files.append(str(item.resolve()))
                elif item.is_dir() and recursive:
                    # Skip hidden directories and common exclude patterns
                    if not any(fnmatch.fnmatch(item.name, pattern) for pattern in exclude_patterns):
                        walk_directory(item, current_depth + 1)
        except (PermissionError, OSError) as e:
            if not quiet:
                print(f"Warning: Cannot access directory {dir_path}: {e}", file=sys.stderr)
    
    for path_str in paths:
        path_obj = Path(path_str)
        
        if not path_obj.exists():
            if not quiet:
                print(f"Warning: Path does not exist: {path_str}", file=sys.stderr)
            continue
            
        if path_obj.is_file():
            if should_include_file(path_obj):
                collected_files.append(str(path_obj.resolve()))
        elif path_obj.is_dir():
            walk_directory(path_obj)
        else:
            if not quiet:
                print(f"Warning: Skipping special file: {path_str}", file=sys.stderr)
    
    return sorted(collected_files)


def process_multiple_files(file_paths: list, output_format: str = "readable", show_progress: bool = True) -> None:
    """
    Process multiple files and output their creation dates.
    
    Args:
        file_paths: List of file paths to process
        output_format: Output format for results
        show_progress: Whether to show progress for large numbers of files
    """
    total_files = len(file_paths)
    
    # Show progress for large numbers of files (except for CSV/JSON which might be piped)
    show_progress_indicator = (
        show_progress and 
        total_files > 10 and 
        output_format in ["readable", "timestamp"]
    )
    
    if output_format == "csv":
        print("file_path,creation_timestamp,creation_date,source,platform")
    
    if show_progress_indicator:
        print(f"Processing {total_files} files...", file=sys.stderr)
    
    processed_count = 0
    error_count = 0
    
    for i, file_path in enumerate(file_paths):
        try:
            # Show progress every 50 files for large batches
            if show_progress_indicator and i > 0 and i % 50 == 0:
                progress_pct = (i / total_files) * 100
                print(f"Progress: {i}/{total_files} ({progress_pct:.1f}%)", file=sys.stderr)
            
            file_info = get_creation_date(file_path)
            output = format_output(file_info, output_format)
            
            if output_format == "readable":
                if total_files > 1:
                    if i > 0:
                        print("\n" + "="*60 + "\n")
                    # For many files, show a more compact header
                    if total_files > 5:
                        print(f"[{i+1}/{total_files}] {file_info['file_path']}")
                        print("-" * 40)
                print(output)
            else:
                print(output)
            
            processed_count += 1
                
        except (ValueError, OSError, PermissionError) as e:
            error_count += 1
            if output_format == "csv":
                print(f"\"{file_path}\",ERROR,ERROR,\"{e}\",ERROR")
            else:
                print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    # Summary for large batches
    if show_progress_indicator:
        print(f"\nCompleted: {processed_count} files processed successfully, {error_count} errors.", file=sys.stderr)


def main():
    """Main entry point for the file creation date utility."""
    parser = argparse.ArgumentParser(
        description="Get the creation date of files and directories",
        epilog="""
Examples:
  %(prog)s file.txt
  %(prog)s file1.txt file2.txt --format json
  %(prog)s /path/to/directory --recursive
  %(prog)s *.py --format csv
  %(prog)s document.pdf --format timestamp
  %(prog)s /home/user --recursive --include '*.txt' '*.py'
  %(prog)s /project --recursive --exclude '*.log' --max-depth 3
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'paths',
        nargs='+',
        help='Path(s) to file(s) or directory(ies) to check'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['readable', 'json', 'csv', 'timestamp'],
        default='readable',
        help='Output format (default: readable)'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Process directories recursively (default for directories)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not process directories recursively'
    )
    
    parser.add_argument(
        '--max-depth',
        type=int,
        metavar='N',
        help='Maximum recursion depth (unlimited by default)'
    )
    
    parser.add_argument(
        '--include',
        nargs='*',
        metavar='PATTERN',
        help='Include only files matching these glob patterns (e.g., "*.txt" "*.py")'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='*',
        metavar='PATTERN',
        help='Exclude files matching these glob patterns (e.g., "*.log" "*.tmp")'
    )
    
    parser.add_argument(
        '--count',
        action='store_true',
        help='Show only the count of files that would be processed'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress indicators and warnings'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='File Creation Date Utility 2.0'
    )
    
    args = parser.parse_args()
    
    # Determine if we should process recursively
    recursive = True
    if args.no_recursive:
        recursive = False
    elif not args.recursive:
        # Default behavior: recursive for directories, non-recursive for explicit files
        recursive = any(Path(p).is_dir() for p in args.paths if Path(p).exists())
    
    try:
        # Collect all files from the given paths
        all_files = collect_files_from_paths(
            args.paths, 
            recursive=recursive,
            max_depth=args.max_depth,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            quiet=args.quiet
        )
        
        if not all_files:
            print("No files found to process.", file=sys.stderr)
            sys.exit(1)
        
        if args.count:
            print(f"Found {len(all_files)} files to process.")
            return
        
        # Process all collected files
        process_multiple_files(all_files, args.format, show_progress=not args.quiet)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, PermissionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
