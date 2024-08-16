import os
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

src_dir = '/home/TestDir'
backup_dir = '/home/tharindu2/python_test/Back_up2'

class FileIntegrityHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return None

        file_path = event.src_path

        # Ignore Vim temporary file creation '4913'
        if os.path.basename(file_path) == '4913':
            return None

        relative_path = os.path.relpath(file_path, src_dir)

        final_backup_file_path = os.path.join(backup_dir, relative_path)

        os.makedirs(os.path.dirname(final_backup_file_path), exist_ok=True)
        
        # Copy the modified file first
        try:
            shutil.copy2(file_path, final_backup_file_path)
        except FileNotFoundError:
            print(f"File not found: {file_path}, skipping...")
            return

        # If there is an existing backup file, rename it with a timestamp
        if os.path.exists(final_backup_file_path):
            timestamp = datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
            versioned_backup_path = f"{final_backup_file_path}_{timestamp}"
            shutil.move(final_backup_file_path, versioned_backup_path)
            
            # Keep only the two most recent backups
            self.cleanup_old_backups(final_backup_file_path)

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
        while len(backup_files) > 3:
            old_backup = backup_files.pop(0)
            os.remove(os.path.join(backup_dir, old_backup))
            print(f"Removed old backup: {old_backup}")

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
