import os
import time
import shutil
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileIntegrityHandler(FileSystemEventHandler):
    def __init__(self, watch_directory, backup_directory, log_file):
        self.watch_directory = watch_directory
        self.backup_directory = backup_directory
        self.log_file = log_file
        if not os.path.exists(backup_directory):
            os.makedirs(backup_directory)
        if not os.path.exists(log_file):
            df = pd.DataFrame(columns=['File', 'Backup Path', 'Timestamp'])
            df.to_excel(log_file, index=False)
        
        self.initial_backup()

    def initial_backup(self):
        for root, dirs, files in os.walk(self.watch_directory):
            for file in files:
                file_path = os.path.join(root, file)
                self.backup_file(file_path)

    def on_modified(self, event):
        if event.is_directory:
            return None
        else:
            self.backup_file(event.src_path)

    def backup_file(self, file_path):
        relative_path = os.path.relpath(file_path, self.watch_directory)
        backup_path = os.path.join(self.backup_directory, relative_path)
        backup_dir = os.path.dirname(backup_path)
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        shutil.copy2(file_path, backup_path)
        
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.update_log(file_path, backup_path, timestamp)

    def update_log(self, file_path, backup_path, timestamp):
        df = pd.read_excel(self.log_file)
        new_entry = pd.DataFrame([[file_path, backup_path, timestamp]], columns=['File', 'Backup Path', 'Timestamp'])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(self.log_file, index=False)
        print(f"Logged: {new_entry}")

if __name__ == "__main__":
    watch_directory = "/home/TestDir"
    backup_directory = "/home/tharindu2/python_test/Back_up"
    log_file = "/home/tharindu2/python_test/log_file.xlsx"

    event_handler = FileIntegrityHandler(watch_directory, backup_directory, log_file)
    observer = Observer()
    observer.schedule(event_handler, path=watch_directory, recursive=True)

    print(f"Starting monitoring on {watch_directory}")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("Monitoring stopped.")
