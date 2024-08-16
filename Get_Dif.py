import os
import difflib
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

backup_dir = '/home/tharindu2/python_test/Back_up2'
output_dir = '/home/tharindu2/python_test/Back_up_diff'

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_name = os.path.basename(event.src_path)

        # Skip Vim swap files and other unwanted files
        if file_name.endswith('.swp') or file_name.startswith('.'):
            return

        if file_name.startswith('test.txt'):
            file1, file2 = get_latest_backups(file_name)

            if file1 and file2:
                file1_path = os.path.join(backup_dir, file1)
                file2_path = os.path.join(backup_dir, file2)
                
                print('*')
                print(file1_path, file2_path)

                diff = compare_files(file1_path, file2_path)
                save_diff(file2, diff)  # Use the latest file name for the diff file
            else:
                print("Not enough backups to compare.")

def get_latest_backups(file_name):
    backups = [f for f in os.listdir(backup_dir) if f.startswith(file_name) and f != file_name]
    backups.sort()  # Sort to get the most recent ones last
    if len(backups) < 2:
        return None, None
    return backups[-2], backups[-1]

def compare_files(file1, file2):
    try:
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            f1_lines = f1.readlines()
            f2_lines = f2.readlines()
    except IOError as e:
        print(f"Error reading files: {e}")
        return []

    differ = difflib.Differ()
    diff = list(differ.compare(f1_lines, f2_lines))

    return diff

def save_diff(latest_file_name, diff):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Construct the output file name with "_diff" suffix
    output_file_name = f'{latest_file_name}_diff.txt'
    output_file_path = os.path.join(output_dir, output_file_name)

    try:
        with open(output_file_path, 'w') as f:
            for line in diff:
                f.write(line)
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=backup_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
