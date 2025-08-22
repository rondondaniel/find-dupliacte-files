import os
import hashlib
import shutil
import argparse
import sys
import csv
from datetime import datetime
from pathlib import Path

def hash_file(path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()

def get_file_info(file_path: str) -> dict:
    """Get file size, modification time, and hash."""
    print(f"Processing file: {os.path.basename(file_path)}")

    # Check if file is a symbolic link (security risk)
    if os.path.islink(file_path):
        raise OSError(f"Skipping symbolic link: {file_path}")

    stat = os.stat(file_path)

    return {
        'size': stat.st_size,
        'mtime': stat.st_mtime,
        'hash': hash_file(file_path)
    }

def validate_path(path: str, path_type: str) -> Path:
    """Validate and resolve a path safely."""
    if not path:
        raise ValueError(f"{path_type} path cannot be empty")

    try:
        # Convert to Path object and resolve to absolute path
        path_obj = Path(path).resolve()

        # Check if path exists
        if not path_obj.exists():
            raise ValueError(f"{path_type} path does not exist: {path}")

        # Check if it's a directory
        if not path_obj.is_dir():
            raise ValueError(f"{path_type} path is not a directory: {path}")

        # Check read permissions
        if not os.access(path_obj, os.R_OK):
            raise ValueError(f"No read permission for {path_type} path: {path}")

        return path_obj

    except OSError as e:
        raise ValueError(f"Invalid {path_type} path: {e}") from e

def is_safe_path(file_path: Path, base_path: Path) -> bool:
    """Check if file_path is safely within base_path (prevent directory traversal)."""
    try:
        file_path.resolve().relative_to(base_path.resolve())
        return True
    except ValueError:
        return False

def initialize_csv_log(csv_path: str) -> None:
    """Initialize CSV file with headers for tracking file operations."""
    headers = [
        'timestamp',
        'operation',
        'original_path',
        'destination_path',
        'file_hash',
        'file_size',
        'modification_time',
        'status',
        'error_message'
    ]

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
        print(f"Initialized CSV log: {csv_path}")
    except OSError as e:
        print(f"Warning: Could not initialize CSV log {csv_path}: {e}")

def log_to_csv(csv_path: str, operation: str, original_path: str,
               destination_path: str = "", file_hash: str = "",
               file_size: int = 0, modification_time: float = 0,
               status: str = "success", error_message: str = "") -> None:
    """Log file operation to CSV file."""
    timestamp = datetime.now().isoformat()

    row = [
        timestamp,
        operation,
        original_path,
        destination_path,
        file_hash,
        file_size,
        modification_time,
        status,
        error_message
    ]

    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row)
    except OSError as e:
        print(f"Warning: Could not write to CSV log: {e}")

def get_files(source_folder: str, dest_folder: str,
              csv_log_path: str = None) -> dict[str, list[str]]:
    """Walk through source folder and group files by hash."""
    # Validate paths
    source_path = validate_path(source_folder, "Source")
    dest_path = validate_path(dest_folder, "Destination")

    print(f"Scanning: {source_path}")
    files = {}
    for root, _, filenames in os.walk(source_path):
        for filename in filenames:
            file_path = Path(root) / filename

            # Security check: ensure file is within source directory
            if not is_safe_path(file_path, source_path):
                print(f"Warning: Skipping file outside source directory: {filename}")
                continue

            # Skip files that are already in destination folder
            if is_safe_path(file_path, dest_path):
                continue

            try:
                info = get_file_info(str(file_path))
                key = info['hash']
                if key in files:
                    files[key].append(str(file_path))
                else:
                    files[key] = [str(file_path)]

                # Log processed file to CSV
                if csv_log_path:
                    log_to_csv(
                        csv_log_path,
                        "processed",
                        str(file_path),
                        "",
                        info['hash'],
                        info['size'],
                        info['mtime'],
                        "success"
                    )
            except OSError as e:
                print(f"Warning: Could not process {filename}: {e}")
                # Log failed processing to CSV
                if csv_log_path:
                    log_to_csv(
                        csv_log_path,
                        "processed",
                        str(file_path),
                        "",
                        "",
                        0,
                        0,
                        "error",
                        str(e)
                    )
                continue

    print(f"Unique files found: {len(files)}")
    # Don't print full file paths for security (information disclosure)

    return files

def get_duplicates(files: dict[str, list[str]]) -> list[str]:
    """Extract duplicate files from grouped files."""
    duplicates = []
    for file_list in files.values():
        if len(file_list) > 1:
            duplicates.extend(file_list[1:])

    print(f"Duplicates found: {len(duplicates)}")

    return duplicates

def move_duplicates(duplicates: list[str], source_folder: str, dest_folder: str,
                    csv_log_path: str = None) -> None:
    """Move duplicate files to destination folder."""
    source_path = Path(source_folder).resolve()
    dest_path = Path(dest_folder).resolve()

    # Check write permissions for destination
    if not os.access(dest_path, os.W_OK):
        raise PermissionError(f"No write permission for destination: {dest_path}")

    print(f"Moving {len(duplicates)} duplicates to: {dest_path}")

    for file_path_str in duplicates:
        file_path = Path(file_path_str).resolve()

        # Security check: ensure file is within source directory
        if not is_safe_path(file_path, source_path):
            print(f"Warning: Skipping file outside source directory: {file_path}")
            continue

        try:
            relative_path = file_path.relative_to(source_path)
            final_dest_path = dest_path / relative_path

            # Security check: ensure destination is within dest directory
            if not is_safe_path(final_dest_path, dest_path):
                print(f"Warning: Skipping unsafe destination path: {relative_path}")
                continue

            # Create directory structure
            final_dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Get file info before moving for CSV logging
            file_stat = file_path.stat()
            file_hash = ""
            try:
                file_hash = hash_file(str(file_path))
            except OSError:
                pass  # Hash calculation failed, continue without it

            # Move file
            shutil.move(str(file_path), str(final_dest_path))
            print(f"Moved: {file_path.name} -> {relative_path}")

            # Log successful move to CSV
            if csv_log_path:
                log_to_csv(
                    csv_log_path,
                    "moved",
                    str(file_path),
                    str(final_dest_path),
                    file_hash,
                    file_stat.st_size,
                    file_stat.st_mtime,
                    "success"
                )

        except (OSError, PermissionError, ValueError) as e:
            print(f"Error moving {file_path.name}: {e}")
            # Log failed move to CSV
            if csv_log_path:
                log_to_csv(
                    csv_log_path,
                    "moved",
                    str(file_path),
                    str(final_dest_path) if 'final_dest_path' in locals() else "",
                    "",
                    0,
                    0,
                    "error",
                    str(e)
                )
            continue

def main():
    """Main entry point for the duplicate file finder."""
    parser = argparse.ArgumentParser(description="Find and move duplicate files")
    parser.add_argument('--source-folder', required=True, help='Path to the source folder')
    parser.add_argument('--dest-folder', required=True, help='Path to the destination folder')
    parser.add_argument('--csv-log', help='Path to CSV file for tracking processed and moved files')
    args = parser.parse_args()

    try:
        # Initialize CSV log if specified
        if args.csv_log:
            initialize_csv_log(args.csv_log)

        print("Finding duplicate files...")
        files = get_files(args.source_folder, args.dest_folder, args.csv_log)
        duplicates = get_duplicates(files)

        if not duplicates:
            print("No duplicates found.")
            return

        move_duplicates(duplicates, args.source_folder, args.dest_folder, args.csv_log)

    except (ValueError, PermissionError, OSError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
    print("Done")