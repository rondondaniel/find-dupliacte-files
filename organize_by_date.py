#!/usr/bin/env python3
"""
Organize Files by Date

A script that moves files from a source folder to destination folders
organized by creation date in YYYY-MM format. Uses functions from
get_file_creation_date.py for cross-platform date detection.
"""

import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Import functions from our existing utility
from get_file_creation_date import (
    get_creation_date,
    collect_files_from_paths
)


def show_progress(current: int, total: int) -> None:
    """Show progress indicator for file processing."""
    progress_pct = (current / total) * 100
    print(f"Progress: {current}/{total} ({progress_pct:.1f}%)", file=sys.stderr)


def create_date_folder(dest_path: Path, file_date: datetime) -> Path:
    """
    Create YYYY-MM folder structure and return the path.
    
    Args:
        dest_path: Base destination path
        file_date: File date (modification date for better photo accuracy)
        
    Returns:
        Path to the YYYY-MM folder
    """
    year_month = file_date.strftime("%Y-%m")
    date_folder = dest_path / year_month
    date_folder.mkdir(parents=True, exist_ok=True)
    return date_folder


def move_file_to_date_folder(file_path: str, dest_base: Path, dry_run: bool = False) -> dict:
    """
    Move a file to appropriate date folder based on its modification date (better for photos).
    
    Args:
        file_path: Source file path
        dest_base: Base destination directory
        dry_run: If True, don't actually move files
        
    Returns:
        Dictionary with operation result
    """
    try:
        # Get file creation date info (but we'll use modification date for better photo accuracy)
        file_info = get_creation_date(file_path)
        # Use modification date instead of creation date for better photo date accuracy
        creation_date = datetime.fromtimestamp(file_info['modification_time'])
        
        # Create destination folder
        date_folder = create_date_folder(dest_base, creation_date)
        
        # Determine destination file path
        source_path = Path(file_path)
        dest_file_path = date_folder / source_path.name
        
        # Handle filename conflicts
        counter = 1
        while dest_file_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            dest_file_path = date_folder / f"{stem}_{counter}{suffix}"
            counter += 1
        
        if not dry_run:
            # Move the file
            shutil.move(str(source_path), str(dest_file_path))
        
        return {
            "status": "success",
            "source": str(source_path),
            "destination": str(dest_file_path),
            "date_folder": creation_date.strftime("%Y-%m"),
            "modification_date": datetime.fromtimestamp(file_info['modification_time']).strftime("%Y-%m-%d %H:%M:%S"),
            "size": file_info['file_size']
        }
        
    except (OSError, PermissionError, ValueError) as e:
        return {
            "status": "error",
            "source": file_path,
            "error": str(e)
        }


def organize_files(source_folder: str, dest_folder: str, dry_run: bool = False,
                  include_patterns: list = None, exclude_patterns: list = None,
                  quiet: bool = False) -> dict:
    """
    Organize files from source folder into date-based folders.
    
    Args:
        source_folder: Source directory path
        dest_folder: Destination directory path
        dry_run: If True, simulate without actually moving files
        include_patterns: File patterns to include
        exclude_patterns: File patterns to exclude
        quiet: Suppress progress output
        
    Returns:
        Dictionary with operation statistics
    """
    source_path = Path(source_folder).resolve()
    dest_path = Path(dest_folder).resolve()
    
    # Validate paths
    if not source_path.exists():
        raise ValueError(f"Source folder does not exist: {source_folder}")
    
    if not source_path.is_dir():
        raise ValueError(f"Source path is not a directory: {source_folder}")
    
    # Create destination directory if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Collect all files
    all_files = collect_files_from_paths(
        [str(source_path)],
        recursive=True,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        quiet=quiet
    )
    
    if not all_files:
        return {"total": 0, "moved": 0, "errors": 0, "folders_created": set()}
    
    total_files = len(all_files)
    moved_count = 0
    error_count = 0
    folders_created = set()
    
    if not quiet:
        action = "Would move" if dry_run else "Moving"
        print(f"{action} {total_files} files from {source_path} to {dest_path}")
        if dry_run:
            print("DRY RUN - No files will actually be moved")
    
    # Process each file
    for i, file_path in enumerate(all_files):
        if not quiet and total_files > 10 and i > 0 and i % 50 == 0:
            show_progress(i, total_files)
        
        result = move_file_to_date_folder(file_path, dest_path, dry_run)
        
        if result["status"] == "success":
            moved_count += 1
            folders_created.add(result["date_folder"])
            
            if not quiet:
                action = "Would move" if dry_run else "Moved"
                print(f"{action}: {Path(result['source']).name} -> {result['date_folder']}/")
                
        else:
            error_count += 1
            if not quiet:
                print(f"Error: {result['source']} - {result['error']}", file=sys.stderr)
    
    return {
        "total": total_files,
        "moved": moved_count,
        "errors": error_count,
        "folders_created": folders_created
    }


def main():
    """Main entry point for the file organization utility."""
    parser = argparse.ArgumentParser(
        description="Organize files into folders by creation date (YYYY-MM format)",
        epilog="""
Examples:
  %(prog)s data moved
  %(prog)s /source/path /dest/path --dry-run
  %(prog)s data moved --include "*.jpg" "*.png"
  %(prog)s data moved --exclude "*.tmp" "Thumbs.db"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'source_folder',
        help='Source folder containing files to organize'
    )
    
    parser.add_argument(
        'dest_folder', 
        help='Destination folder where organized files will be moved'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually moving files'
    )
    
    parser.add_argument(
        '--include',
        nargs='*',
        metavar='PATTERN',
        help='Include only files matching these glob patterns (e.g., "*.jpg" "*.png")'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='*',
        metavar='PATTERN',
        help='Exclude files matching these glob patterns (e.g., "*.tmp" "Thumbs.db")'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='File Organization Utility 1.0'
    )
    
    args = parser.parse_args()
    
    try:
        stats = organize_files(
            args.source_folder,
            args.dest_folder,
            dry_run=args.dry_run,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            quiet=args.quiet
        )
        
        if not args.quiet:
            action = "Would be moved" if args.dry_run else "moved"
            print("\nSummary:")
            print(f"  Files processed: {stats['total']}")
            print(f"  Files {action}: {stats['moved']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Date folders created: {len(stats['folders_created'])}")
            
            if stats['folders_created']:
                print(f"  Folders: {', '.join(sorted(stats['folders_created']))}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except (OSError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
