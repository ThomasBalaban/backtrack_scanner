import re
from datetime import datetime
from config import FILE_PATTERN

def get_valid_files(directory_path):
    """Scans the directory and returns a sorted list of valid (Path, datetime) tuples."""
    pattern = re.compile(FILE_PATTERN)
    valid_files = []
    
    if not directory_path.exists():
        print(f"Error: Could not find the directory at '{directory_path}'")
        print("Please ensure the SMB drive is currently connected and mounted via Finder.")
        return valid_files

    for file_path in directory_path.iterdir():
        if file_path.is_file():
            match = pattern.match(file_path.name)
            if match:
                timestamp_str = match.group(1)
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H-%M-%S")
                    valid_files.append((file_path, timestamp))
                except ValueError:
                    continue
                    
    # Sort chronologically by the timestamp
    valid_files.sort(key=lambda x: x)
    return valid_files