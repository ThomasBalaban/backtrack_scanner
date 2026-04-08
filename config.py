from pathlib import Path

# Get the directory where config.py is located (your project root)
BASE_DIR = Path(__file__).parent

# Target Directories
SOURCE_DIR = Path("/Volumes/backtracks")
DEST_DIR = Path("/Users/thomasbalaban/Downloads/todoshorts")

# File matching pattern
FILE_PATTERN = r"^Backtrack (\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2})\.mkv$"

# The JSON file that keeps track of successfully copied files
# Now points to the project root instead of DEST_DIR
LEDGER_FILE = BASE_DIR / "copied_inventory.json"