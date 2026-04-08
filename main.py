from config import SOURCE_DIR, DEST_DIR
import scanner
import file_ops

def main():
    print("Initializing Backtrack Transfer Tool...\n")
    
    # 1. Scan the source directory
    print(f"Scanning source directory: {SOURCE_DIR}")
    source_files = scanner.get_valid_files(SOURCE_DIR)
    
    if not source_files:
        print("No valid files found to process. Exiting.")
        return
        
    print(f"Found {len(source_files)} valid Backtrack files.")
    
    # 2. Execute the copy
    file_ops.copy_files(source_files, DEST_DIR)
    
    # 3. Verify the transfer
    file_ops.verify_directories(source_files, DEST_DIR)

if __name__ == "__main__":
    main()