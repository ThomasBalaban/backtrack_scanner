import shutil
import os
import json
from config import LEDGER_FILE

def load_ledger():
    if LEDGER_FILE.exists():
        try:
            with open(LEDGER_FILE, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            print("Warning: JSON inventory file corrupted. Building a new one.")
            return set()
    return set()

def save_ledger(ledger_data):
    with open(LEDGER_FILE, 'w') as f:
        json.dump(sorted(list(ledger_data)), f, indent=4)

def copy_files(source_files, dest_dir):
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
        
        # We append a temporary extension for the transfer process
        temp_dest_path = dest_path.with_suffix('.mkv.part')
        
        # Fast Check & Fallback Check
        if filename in ledger or dest_path.exists():
            skipped_count += 1
            ledger.add(filename) 
            continue
            
        print(f"Copying: {filename}...")
        try:
            # 1. Copy to the temporary .part file
            shutil.copy2(source_path, temp_dest_path)
            
            # 2. If we reach this line, the copy was 100% successful. Rename to .mkv
            temp_dest_path.rename(dest_path)
            
            # 3. Log the success
            ledger.add(filename) 
            copied_count += 1
            
        except OSError as e:
            # OSError catches network drops, missing drives, and I/O interruptions
            print(f"\n[!] NETWORK ERROR: Interrupted while copying {filename}.")
            print(f"Error Details: {e}")
            
            # Auto-Cleanup: Delete the incomplete partial file
            if temp_dest_path.exists():
                print(f"Cleaning up incomplete file: {temp_dest_path.name}")
                temp_dest_path.unlink()
                
            print("\nAborting the rest of the queue to prevent errors. Please reconnect and run again.")
            break # Breaks out of the loop completely
            
        except Exception as e:
            print(f"\n[!] UNEXPECTED ERROR: {e}")
            if temp_dest_path.exists():
                temp_dest_path.unlink()
            break
            
    # Save the updated ledger only if we actually added new files
    if len(ledger) > initial_ledger_size:
        print("\nSaving updated JSON inventory file...")
        save_ledger(ledger)
            
    print(f"Completed! Copied {copied_count} new files. Skipped {skipped_count} existing files.")


def verify_directories(source_files, dest_dir):
    print("\n--- Verifying Destination ---")
    
    # Quick check to make sure the network drive didn't drop before verification
    if not source_files or not source_files.parent.exists():
        print("Warning: Cannot verify because the source drive is no longer accessible.")
        return False

    missing_files = []
    incomplete_files = []
    
    if not dest_dir.exists():
        print("Error: Destination directory does not exist!")
        return False

    for source_path, _ in source_files:
        dest_path = dest_dir / source_path.name
        
        if not dest_path.exists():
            missing_files.append(source_path.name)
        else:
            try:
                # Wrap stat checks in try/except in case the network drops during verification
                if source_path.stat().st_size != dest_path.stat().st_size:
                    incomplete_files.append(source_path.name)
            except OSError:
                print(f"Warning: Lost connection while verifying {source_path.name}")
                return False

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