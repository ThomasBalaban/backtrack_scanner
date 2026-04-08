import shutil
import os
import json
from config import LEDGER_FILE

def load_ledger():
    """Loads the JSON ledger of previously copied files into a Python Set for fast lookups."""
    if LEDGER_FILE.exists():
        try:
            with open(LEDGER_FILE, 'r') as f:
                # Convert the JSON list into a Set
                return set(json.load(f))
        except json.JSONDecodeError:
            print("Warning: JSON inventory file corrupted. Building a new one.")
            return set()
    return set()

def save_ledger(ledger_data):
    """Saves the Set of copied files back to a formatted JSON file."""
    with open(LEDGER_FILE, 'w') as f:
        # Convert the Set back to a sorted list so the JSON file is highly readable
        json.dump(sorted(list(ledger_data)), f, indent=4)

def copy_files(source_files, dest_dir):
    """Copies a list of file paths and updates the JSON inventory."""
    if not dest_dir.exists():
        print(f"Creating destination directory: {dest_dir}")
        dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n--- Loading Inventory ---")
    ledger = load_ledger()
    initial_ledger_size = len(ledger)
    print(f"Found {initial_ledger_size} previously copied files in JSON ledger.")

    print(f"\n--- Copying Files ---")
    copied_count = 0
    skipped_count = 0
    
    for source_path, _ in source_files:
        filename = source_path.name
        dest_path = dest_dir / filename
        
        # Fast Check: Is it in the JSON ledger? 
        # Fallback Check: Does it actually exist on the disk anyway?
        if filename in ledger or dest_path.exists():
            skipped_count += 1
            # If it was on the disk but missing from the JSON, add it to our ledger memory
            ledger.add(filename) 
            continue
            
        print(f"Copying: {filename}...")
        try:
            shutil.copy2(source_path, dest_path)
            # Only add to the ledger if the copy succeeds without throwing an error
            ledger.add(filename) 
            copied_count += 1
        except Exception as e:
            print(f"Failed to copy {filename}. Error: {e}")
            
    # Save the updated ledger only if we actually added new files to it
    if len(ledger) > initial_ledger_size:
        print("\nSaving updated JSON inventory file...")
        save_ledger(ledger)
            
    print(f"Completed! Copied {copied_count} new files. Skipped {skipped_count} existing files.")


def verify_directories(source_files, dest_dir):
    """Compares the source file list against the destination to check for missing/corrupted files."""
    print("\n--- Verifying Destination ---")
    
    missing_files = []
    incomplete_files = []
    
    if not dest_dir.exists():
        print("Error: Destination directory does not exist!")
        return False

    for source_path, _ in source_files:
        dest_path = dest_dir / source_path.name
        
        if not dest_path.exists():
            missing_files.append(source_path.name)
        elif source_path.stat().st_size != dest_path.stat().st_size:
            incomplete_files.append(source_path.name)

    if not missing_files and not incomplete_files:
        print("Success: All source files are present in the destination and sizes match perfectly.")
        return True
    else:
        if missing_files:
            print(f"\nWarning: {len(missing_files)} files are completely missing:")
            for f in missing_files:
                print(f"  - {f}")
                
        if incomplete_files:
            print(f"\nWarning: {len(incomplete_files)} files have mismatched sizes (likely an interrupted copy):")
            for f in incomplete_files:
                print(f"  - {f}")
        return False