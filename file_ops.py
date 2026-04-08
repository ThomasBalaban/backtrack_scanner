import shutil
import os
import json
from config import LEDGER_FILE
from datetime import datetime
from pathlib import Path
from send2trash import send2trash

CLUSTER_WINDOW_SECONDS = 120
DELETED_LEDGER_FILE = Path("deleted_ledger.json")


def load_ledger():
    if LEDGER_FILE.exists():
        try:
            with open(LEDGER_FILE, 'r') as f:
                data = json.load(f)

                if isinstance(data, list):
                    print("Migrating old ledger format to new dictionary format...")
                    new_ledger = {}
                    for filename in data:
                        ts_str = filename.replace("Backtrack ", "").replace(".mkv", "")
                        new_ledger[filename] = ts_str

                    save_ledger(new_ledger)
                    return new_ledger

                return data
        except json.JSONDecodeError:
            print("Warning: JSON inventory file corrupted. Building a new one.")
            return {}
    return {}


def save_ledger(ledger_data):
    with open(LEDGER_FILE, 'w') as f:
        sorted_ledger = dict(sorted(ledger_data.items()))
        json.dump(sorted_ledger, f, indent=4)


def load_deleted_ledger():
    if DELETED_LEDGER_FILE.exists():
        with open(DELETED_LEDGER_FILE, "r") as f:
            return json.load(f)
    return {}


def save_deleted_ledger(data):
    with open(DELETED_LEDGER_FILE, "w") as f:
        json.dump(data, f, indent=4)


def copy_files(source_files, dest_dir):
    deleted_ledger = load_deleted_ledger()

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

    for source_path, timestamp in source_files:
        filename = source_path.name
        dest_path = dest_dir / filename
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ledger[filename] = timestamp_str
        temp_dest_path = dest_path.with_suffix('.mkv.part')

        if filename in ledger or filename in deleted_ledger or dest_path.exists():
            skipped_count += 1
            ledger[filename] = timestamp_str
            continue

        print(f"Copying: {filename}...")
        try:
            shutil.copy2(source_path, temp_dest_path)
            temp_dest_path.rename(dest_path)

            ledger[filename] = timestamp_str
            copied_count += 1

        except OSError as e:
            print(f"\n[!] NETWORK ERROR: Interrupted while copying {filename}.")
            print(f"Error Details: {e}")

            if temp_dest_path.exists():
                temp_dest_path.unlink()

            print("\nAborting to prevent corruption.")
            break

        except Exception as e:
            print(f"\n[!] UNEXPECTED ERROR: {e}")
            if temp_dest_path.exists():
                temp_dest_path.unlink()
            break

    if len(ledger) > initial_ledger_size:
        print("\nSaving updated JSON inventory file...")
        save_ledger(ledger)

    print(f"Completed! Copied {copied_count} new files. Skipped {skipped_count} existing files.")


def cluster_files(ledger):
    if not ledger:
        return []

    parsed = []
    for filename, ts in ledger.items():
        # Split into date and time to safely target only the time portion
        date_part, time_part = ts.split(" ")
        
        # Replace dashes with colons only in the time part
        time_part = time_part.replace("-", ":")
        
        # Recombine into the correct format
        ts_fixed = f"{date_part} {time_part}"
        
        dt = datetime.strptime(ts_fixed, "%Y-%m-%d %H:%M:%S")
        parsed.append((filename, dt))

    # Sort strictly by the datetime object
    parsed.sort(key=lambda x: x)

    clusters = []
    current_cluster = [parsed]

    for i in range(1, len(parsed)):
        # Explicitly unpack the tuple into filename and time
        prev_filename, prev_time = parsed[i - 1]
        curr_filename, curr_time = parsed[i]

        # Now we know for sure prev_time and curr_time are just datetime objects
        if (curr_time - prev_time).total_seconds() <= CLUSTER_WINDOW_SECONDS:
            current_cluster.append(parsed[i])
        else:
            clusters.append(current_cluster)
            current_cluster = [parsed[i]]

    clusters.append(current_cluster)
    return clusters


def select_files_to_delete(clusters, deleted_ledger):
    to_delete = []

    for cluster in clusters:
        if len(cluster) <= 1:
            continue

        # Safely finds the max using the datetime object (x)
        newest = max(cluster, key=lambda x: x)

        print("\nCluster detected:")
        for f, t in cluster:
            print(f"  {f} -> {t}")
        print(f"Keeping: {newest}")

        for file in cluster:
            filename = file
            if file != newest and filename not in deleted_ledger:
                to_delete.append(filename)

    return to_delete


def delete_files(to_delete, dest_dir, deleted_log):
    deleted = {}

    for filename in to_delete:
        file_path = dest_dir / filename

        if not file_path.exists():
            continue

        print(f"Trashing: {filename}")
        send2trash(str(file_path))

        deleted[filename] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    deleted_log.update(deleted)
    return deleted_log


def cleanup_clusters(dest_dir):
    ledger = load_ledger()
    deleted_ledger = load_deleted_ledger()

    clusters = cluster_files(ledger)
    to_delete = select_files_to_delete(clusters, deleted_ledger)

    if not to_delete:
        print("No clustered duplicates found.")
        return

    print(f"\nFound {len(to_delete)} files to remove from clusters.")

    deleted_ledger = delete_files(to_delete, dest_dir, deleted_ledger)
    save_deleted_ledger(deleted_ledger)


def verify_directories(source_files, dest_dir):
    print("\n--- Verifying Destination ---")

    if not source_files:
        return False

    first_file_path = source_files[0][0]

    if not first_file_path.parent.exists():
        print("Warning: Source drive not accessible.")
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
                if source_path.stat().st_size != dest_path.stat().st_size:
                    incomplete_files.append(source_path.name)
            except OSError:
                print(f"Warning: Lost connection while verifying {source_path.name}")
                return False

    if not missing_files and not incomplete_files:
        print("Success: All files verified.")
        return True
    else:
        if missing_files:
            print(f"\nMissing files ({len(missing_files)}):")
            for f in missing_files:
                print(f"  - {f}")

        if incomplete_files:
            print(f"\nIncomplete files ({len(incomplete_files)}):")
            for f in incomplete_files:
                print(f"  - {f}")

        return False