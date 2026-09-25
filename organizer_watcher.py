import os
import sys
import time
import shutil
import pathlib
import argparse
from typing import Set

WATCH_DIR = r"F:\OF OUTPUT"

IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif",
    ".heic", ".heif", ".raw", ".cr2", ".nef", ".arw", ".svg"
}
VIDEO_EXTS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v",
    ".ts", ".m2ts", ".3gp", ".vob", ".mpg", ".mpeg"
}
AUDIO_EXTS = {
    ".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".opus", ".wma",
    ".alac", ".aiff"
}

IGNORE_EXTS = {
    ".part", ".crdownload", ".tmp", ".temp", ".download",
    ".db", ".db-shm", ".db-wal", ".sqlite", ".json"
}

SYSTEM_FOLDERS = {
    "$recycle.bin", "system volume information", ".data", ".git", ".config"
}

def is_file_ready(filepath: str, check_mtime: bool = True) -> bool:
    """Check if the file is completely written and not locked by another process."""
    try:
        if not os.path.exists(filepath):
            return False
        if check_mtime and (time.time() - os.path.getmtime(filepath) < 2):
            return False
        with open(filepath, "ab"):
            return True
    except (IOError, PermissionError):
        return False

def get_target_subfolder(model_dir: str, ext: str) -> str:
    """Determine destination subfolder (Images, Videos, Audios/Audio) for the file extension."""
    ext = ext.lower()
    if ext in IMAGE_EXTS:
        return os.path.join(model_dir, "Images")
    elif ext in VIDEO_EXTS:
        return os.path.join(model_dir, "Videos")
    elif ext in AUDIO_EXTS:
        # Check if user already has 'Audio' or 'Audios'
        audio_singular = os.path.join(model_dir, "Audio")
        audio_plural = os.path.join(model_dir, "Audios")
        if os.path.isdir(audio_singular):
            return audio_singular
        return audio_plural
    return ""

def get_unique_destination(dest_path: str, src_path: str) -> str:
    """If a file already exists at dest_path, check if identical or return numbered name."""
    if not os.path.exists(dest_path):
        return dest_path
    
    # Check if identical in size
    try:
        if os.path.getsize(dest_path) == os.path.getsize(src_path):
            # Same size, likely duplicate
            return dest_path
    except OSError:
        pass

    parent = os.path.dirname(dest_path)
    stem = pathlib.Path(dest_path).stem
    suffix = pathlib.Path(dest_path).suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = os.path.join(parent, new_name)
        if not os.path.exists(new_path):
            return new_path
        if os.path.getsize(new_path) == os.path.getsize(src_path):
            return new_path
        counter += 1

def clean_empty_folders(root_dir: str, protected_dirs: Set[str]):
    """Recursively remove empty directories, excluding protected ones."""
    for root, dirs, files in os.walk(root_dir, topdown=False):
        normalized_root = os.path.abspath(root).lower()
        if normalized_root in protected_dirs:
            continue
        try:
            # Check if directory is empty
            if not os.listdir(root):
                os.rmdir(root)
                print(f"[REMOVED EMPTY] {root}")
        except Exception as e:
            pass

def organize_model(model_name: str, model_path: str, check_mtime: bool = True) -> int:
    """Organize all files in a model's folder into Images, Videos, and Audios."""
    images_dir = os.path.join(model_path, "Images")
    videos_dir = os.path.join(model_path, "Videos")
    audios_dir = os.path.join(model_path, "Audios")
    audio_dir = os.path.join(model_path, "Audio")

    # Create primary folders
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    if not os.path.isdir(audio_dir):
        os.makedirs(audios_dir, exist_ok=True)

    protected_dirs = {
        os.path.abspath(model_path).lower(),
        os.path.abspath(images_dir).lower(),
        os.path.abspath(videos_dir).lower(),
        os.path.abspath(audios_dir).lower(),
        os.path.abspath(audio_dir).lower(),
    }

    moved_count = 0

    # Collect all files
    for root, dirs, files in os.walk(model_path):
        normalized_root = os.path.abspath(root).lower()
        
        # Don't recurse or move files that are already directly in the target category folders
        is_in_target = normalized_root in protected_dirs and normalized_root != os.path.abspath(model_path).lower()

        for file in files:
            file_path = os.path.join(root, file)
            ext = pathlib.Path(file).suffix.lower()

            if ext in IGNORE_EXTS or file.startswith("."):
                continue

            target_folder = get_target_subfolder(model_path, ext)
            if not target_folder:
                continue

            # If already in the target folder, nothing to do
            if is_in_target and os.path.dirname(file_path).lower() == os.path.abspath(target_folder).lower():
                continue

            if not is_file_ready(file_path, check_mtime=check_mtime):
                # Still downloading or locked, leave it for next pass
                continue

            dest_path = os.path.join(target_folder, file)
            unique_dest = get_unique_destination(dest_path, file_path)

            if os.path.abspath(unique_dest).lower() == os.path.abspath(file_path).lower():
                continue

            try:
                # If identical file exists at target, delete the extra source file
                if os.path.exists(dest_path) and os.path.getsize(dest_path) == os.path.getsize(file_path):
                    os.remove(file_path)
                    print(f"[{model_name}] Removed duplicate: {file}")
                else:
                    shutil.move(file_path, unique_dest)
                    print(f"[{model_name}] Moved -> {os.path.basename(target_folder)}: {os.path.basename(unique_dest)}")
                moved_count += 1
            except Exception as e:
                print(f"[{model_name}] Error moving {file}: {e}", file=sys.stderr)

    # Clean up empty subdirectories
    clean_empty_folders(model_path, protected_dirs)
    return moved_count

def run_organizer(root_dir: str = WATCH_DIR, check_mtime: bool = True) -> int:
    """Scan and organize all model directories in root_dir."""
    if not os.path.exists(root_dir):
        print(f"Directory {root_dir} does not exist yet.")
        return 0

    total_moved = 0
    try:
        entries = os.listdir(root_dir)
    except Exception as e:
        print(f"Error accessing {root_dir}: {e}", file=sys.stderr)
        return 0

    for entry in entries:
        if entry.lower() in SYSTEM_FOLDERS:
            continue
        full_path = os.path.join(root_dir, entry)
        if os.path.isdir(full_path):
            total_moved += organize_model(entry, full_path, check_mtime=check_mtime)

    return total_moved

def main():
    parser = argparse.ArgumentParser(description="OF-Scraper Output Watcher & Organizer")
    parser.add_argument("--dir", default=WATCH_DIR, help="Root folder to watch (default: F:\\OF OUTPUT)")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no continuous watch)")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds (default: 5)")
    args = parser.parse_args()

    print("=" * 65)
    print("      OF-Scraper Folder Organizer & Output Watcher")
    print(f"      Target: {args.dir}")
    print(f"      Structure: <Model> / Images, Videos, Audios")
    print("=" * 65)

    if args.once:
        print("\n[+] Running single-pass cleanup...")
        moved = run_organizer(args.dir, check_mtime=False)
        print(f"[+] Done! Organized {moved} file(s).\n")
        return

    print(f"\n[+] Watching '{args.dir}' every {args.interval}s...")
    print("[+] Press Ctrl+C at any time to stop.\n")

    try:
        while True:
            moved = run_organizer(args.dir)
            if moved > 0:
                print(f"[{time.strftime('%H:%M:%S')}] Organized {moved} file(s).")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[*] Watcher stopped by user.")

if __name__ == "__main__":
    main()
