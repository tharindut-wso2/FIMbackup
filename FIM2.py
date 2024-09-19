import os
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

src_dir = '/home/TestDir/'
backup_dir = '/home/tharindu2/python_test/Back_up2'

class FileIntegrityHandler(FileSystemEventHandler):
    
    # Catch when file get modified
    def on_modified(self, event):
        if event.is_directory:
            return None

        file_path = event.src_path
        directory, file_name = os.path.split(event.src_path)
        remove_swp_files(directory)  # Remove any .swp files in the directory

        # Ignore Vim temporary file creation '4913'
        if os.path.basename(file_path) == '4913':
            return None

        # Check if the file is readable (not binary)
        if not self.is_readable_text_file(file_path):
            print(f"Skipping non-readable file: {file_path}")
            return None

        # Get the relative path with respect to the src_dir
        relative_path = os.path.relpath(file_path, src_dir)

        # Join the relative path and the back_up paths
        final_backup_file_path = os.path.join(backup_dir, relative_path)

        os.makedirs(os.path.dirname(final_backup_file_path), exist_ok=True)
        
        # Copy the modified file first
        try:
            shutil.copy2(file_path, final_backup_file_path)
        except FileNotFoundError:
            print(f"File not found: {file_path}, skipping...")
            return
        if os.path.exists(final_backup_file_path):
            unix_timestamp = time.time()  # Get time in seconds (with milliseconds)
            versioned_backup_path = f"{final_backup_file_path}_{int(unix_timestamp)}"
            shutil.move(final_backup_file_path, versioned_backup_path)
            
            # Keep only the two most recent backups
            self.cleanup_old_backups(final_backup_file_path)

    def is_readable_text_file(self, file_path):
        """Check if a file is readable as text."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file.read(1024)  # Try reading the first 1KB of the file
            return True
        except (UnicodeDecodeError, IOError):
            return False

    def cleanup_old_backups(self, backup_file_path):
        
        # Get the directory and base filename
        backup_dir = os.path.dirname(backup_file_path)
        base_filename = os.path.basename(backup_file_path)
        
        # List all files in the backup directory that match the base filename pattern
        backup_files = [
            f for f in os.listdir(backup_dir) 
            if f.startswith(base_filename) and f != base_filename
        ]
        
        # Sort backups by modification time (oldest first)
        backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))

        # Remove older backups if there are more than two
        while len(backup_files) > 2:
            old_backup = backup_files.pop(0)
            os.remove(os.path.join(backup_dir, old_backup))
            print(f"Removed old backup: {old_backup}")
def remove_swp_files(directory):
        """Remove all .swp files in the directory and its subdirectories."""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.swp') or '.swp_' in file:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        # print(f"Removed: {file_path}")
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    event_handler = FileIntegrityHandler()
    observer = Observer()
    observer.schedule(event_handler, path=src_dir, recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
