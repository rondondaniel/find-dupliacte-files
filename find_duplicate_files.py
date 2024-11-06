import os
import hashlib
import shutil
import pprint

def hash_file(path: str) -> str:
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def get_file_info(file_path: str) -> dict:
    print(f"Getting info: {file_path}")
    stat = os.stat(file_path)
    
    return {
        'size': stat.st_size,
        'mtime': stat.st_mtime,
        'hash': hash_file(file_path)
    }

def get_files(source_folder: str, dest_folder: str) -> dict[tuple[int, float, str], list[str]]:
    print(f"Source folder: {source_folder}")
    files = {}
    for root, _, filenames in os.walk(source_folder):
        for filename in filenames:
            print(f"Processing: {filename}")
            file_path = os.path.join(root, filename)
            if os.path.commonpath([file_path, dest_folder]) == dest_folder:
                continue
            try:
                info = get_file_info(file_path)
                print(f"Info: {info}")
                key = info['hash']
                if key in files:
                    files[key].append(file_path)
                else:
                    files[key] = [file_path]
            except OSError:
                continue
        
    print(f"Files found: {len(files)}")
    pprint.pprint(files)

    return files

def get_duplicates(files: list[str]) -> list[str]:
    duplicates = []
    for file_list in files.values():
        if len(file_list) > 1:
            duplicates.extend(file_list[1:])
    
    print(f"Duplicates found: {len(duplicates)}")
    
    return duplicates

def move_duplicates(duplicates: list[str], source_folder: str, dest_folder: str) -> None:
    print(f"Moving duplicates to: {dest_folder}")
    for file_path in duplicates:
        relative_path = os.path.relpath(file_path, source_folder)
        dest_path = os.path.join(dest_folder, relative_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(file_path, dest_path)
        print(f"Moved duplicate: {file_path} -> {dest_path}")

def main(source_folder: str, dest_folder: str) -> None:
    print("Getting file information...")
    files = get_files(source_folder, dest_folder)
    duplicates = get_duplicates(files)
    move_duplicates(duplicates, source_folder, dest_folder)

if __name__ == "__main__":
    print("Finding duplicate files...")
    source_folder = "/Volumes/DataHome/Anaelle/1-Photos/2012-02" #"./origin"
    dest_folder = "/Volumes/DataHome/Anaelle/0-Compress" #"./clone/"
    main(source_folder, dest_folder)