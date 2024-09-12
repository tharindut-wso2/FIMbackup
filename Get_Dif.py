import os
import time
import difflib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Directories to monitor and save diffs
backup_dir = "/home/tharindu2/python_test/Back_up2"
diff_dir = "/home/tharindu2/python_test/Backup_diff"

if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

def compare_files(file1, file2):
    """Compare two text files and return the differences."""
    try:
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            diff = difflib.unified_diff(
                f1.readlines(), f2.readlines(),
                fromfile=os.path.basename(file1),
                tofile=os.path.basename(file2)
            )
            return ''.join(diff)
    except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
        return "Skipping binary or non-readable files."

def get_latest_files(directory):
    """Get the two latest files in the directory with the same base name."""
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    
    # Group files by base name (excluding timestamp)
    base_name_dict = {}
    for f in files:
        base_name = '_'.join(f.split('_')[:-1])
        if base_name not in base_name_dict:
            base_name_dict[base_name] = []
        base_name_dict[base_name].append(f)
    
    latest_files = []
    for base_name, file_list in base_name_dict.items():
        if len(file_list) >= 2:
            latest_files.append(file_list[-2:])
    
    return latest_files

def process_file(directory, base_name):
    """Process files with the same base name in the given directory and save the differences."""
    latest_files = get_latest_files(directory)
    if latest_files:
        
        for file_pair in latest_files:

            file1, file2 = [os.path.join(directory, f) for f in file_pair]

            diff = compare_files(file1, file2)

            # Create diff file name and directory structure
            relative_dir = os.path.relpath(directory, backup_dir)
            diff_file_name = f'{file_pair[1]}_diff.txt'
            output_dir = os.path.join(diff_dir, relative_dir)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, diff_file_name)
            save_diff(diff, output_path)

def save_diff(diff, output_path):

    """Save the diff to a file."""
    with open(output_path, 'w') as f:
        f.write(diff)

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

class Watcher:
    def __init__(self, directory):
        self.observer = Observer()
        self.directory = directory

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    
    def on_created(self, event):
        """Handle file creation event."""
        if not event.is_directory and not event.src_path.endswith('.swp'):
            directory, file_name = os.path.split(event.src_path)
            remove_swp_files(directory)  # Remove any .swp files in the directory
            base_name = '_'.join(file_name.split('_')[:-1])

            #add small time to create the file
            time.sleep(0.1)
            process_file(directory, base_name)

if __name__ == "__main__":
    w = Watcher(backup_dir)
    w.run()
