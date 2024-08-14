# import os
# import shutil
# from datetime import datetime
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# src_dir = '/home/TestDir'
# backup_dir = '/home/tharindu2/python_test/Back_up2'

# class FileIntegrityHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         if event.is_directory:
#             return None

#         file_path = event.src_path
#         relative_path = os.path.relpath(file_path, src_dir)

#         # Combine the relative path and backup dir path
#         final_backup_file_path = os.path.join(backup_dir, relative_path)

#         # Ensure the final backup directory exists
#         os.makedirs(os.path.dirname(final_backup_file_path), exist_ok=True)

#         # If a backup already exists, find existing versions
#         base_name = os.path.basename(final_backup_file_path)
#         dir_name = os.path.dirname(final_backup_file_path)

#         # Find all existing backup files for this file
#         backups = sorted(
#             [f for f in os.listdir(dir_name) if f.startswith(base_name) and f != base_name],
#             key=lambda x: os.path.getmtime(os.path.join(dir_name, x))
#         )

#         # If there are already two backups, remove the oldest one
#         if len(backups) >= 2:
#             os.remove(os.path.join(dir_name, backups[0]))

#         # Create the new backup with a timestamp
#         timestamp = datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
#         versioned_backup_path = f"{final_backup_file_path}_{timestamp}"
        
#         shutil.copy2(file_path, versioned_backup_path)

# if __name__ == "__main__":
#     event_handler = FileIntegrityHandler()
#     observer = Observer()
#     observer.schedule(event_handler, path=src_dir, recursive=True)
#     observer.start()

#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()



##############################################################


# import os
# import shutil
# from datetime import datetime
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# src_dir = '/home/TestDir'
# backup_dir = '/home/tharindu2/python_test/Back_up2'

# class FileIntegrityHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         if event.is_directory:
#             return None

#         file_path = event.src_path

#         if os.path.basename(file_path) == '4913':
#             return None

#         relative_path = os.path.relpath(file_path, src_dir)

#         #Combine the relative path and backup dir path
#         final_backup_file_path = os.path.join(backup_dir, relative_path)

#         # Ensure the final backup directory exists
#         os.makedirs(os.path.dirname(final_backup_file_path), exist_ok=True)

#         # If a backup already exists, rename it with a timestamp
#         if os.path.exists(final_backup_file_path):
#             timestamp = datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
#             versioned_backup_path = f"{final_backup_file_path}_{timestamp}"
#             shutil.move(final_backup_file_path, versioned_backup_path)

#         # Copy the current file to the final backup location
#         shutil.copy2(file_path, final_backup_file_path)

# if __name__ == "__main__":
#     event_handler = FileIntegrityHandler()
#     observer = Observer()
#     observer.schedule(event_handler, path=src_dir, recursive=True)
#     observer.start()

#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()


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
        
        if os.path.exists(final_backup_file_path):
            timestamp = datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
            versioned_backup_path = f"{final_backup_file_path}_{timestamp}"
            shutil.move(final_backup_file_path, versioned_backup_path)
            
            # Keep only the two most recent backups
            self.cleanup_old_backups(final_backup_file_path)

        try:
            shutil.copy2(file_path, final_backup_file_path)
        except FileNotFoundError:
            print(f"File not found: {file_path}, skipping...")

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
