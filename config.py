from pathlib import Path

# Target Directories
SOURCE_DIR = Path("/Volumes/backtracks")
DEST_DIR = Path("/Users/thomasbalaban/Downloads/todoshorts")

# File matching pattern
FILE_PATTERN = r"^Backtrack (\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2})\.mkv$"

# The JSON file that keeps track of successfully copied files
LEDGER_FILE = DEST_DIR / "copied_inventory.json"