import os
import time
import difflib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re
from datetime import datetime

# Directories to monitor and save diffs
backup_dir = "/home/tharindu2/python_test/Back_up2"
diff_dir = "/home/tharindu2/python_test/Backup_diff"
input_file = '/var/log/audit/audit.log'

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

def process_log_line(line, syscall_info, capture, buffer, timestamp_backup, output_path):
    if re.search(r' UID="mysql"', line):  # Skip lines where UID is "mysql"
        return syscall_info, capture, buffer  # Skip this line and move to the next one

    if (re.search(r'syscall=56', line)) and (re.search(timestamp_backup, line)):
        global openat
        openat = False
        capture = True
        buffer.append(line)

        timestamp = re.search(r'audit\((\d+\.\d+)', line).group(1)
        auid = re.search(r' AUID="([^"]+)"', line).group(1)
        uid = re.search(r' UID="([^"]+)"', line).group(1)
                
        syscall_info['cmd'] = 'Write the file'
        syscall_info['Syscall'] = 'Openat'
        openat = 1

        syscall_info.update({
            'timestamp': timestamp,
            'auid': auid,
            'uid': uid
        })

        if re.search(r'comm="cp"', line):
            syscall_info['cmd'] = 'Copied file'
                            
    elif capture and re.match(r'^type=PATH', line):
        buffer.append(line)
        path_match = re.search(r'name="([^"]+)"', line)
        if path_match:
            path = path_match.group(1)
            if re.search(r'nametype=PARENT', line):
                if path == "./":
                    capture = 0
                syscall_info['parent_path'] = path
            if re.search(r'nametype=NORMAL', line):
                syscall_info['file_path'] = path
            if re.search(r'name="4913"', line):
                capture = 0
                        
    elif capture and re.match(r'^type=PROCTITLE', line):
        buffer.append(line)
        if 'parent_path' in syscall_info and 'file_path' in syscall_info:
            full_path = f"{syscall_info['parent_path']}/{syscall_info['file_path']}"

            syscall_info['conclusion'] = 'Switch User'

            if openat == 1:
                if syscall_info['auid'] != syscall_info['uid']:
                    syscall_info['conclusion'] = f"{syscall_info['auid']} has edited {full_path} file as {syscall_info['uid']}"
                else:
                    syscall_info['conclusion'] = f"{syscall_info['auid']} has edited {full_path} file"

                human_readable_timestamp = datetime.fromtimestamp(float(syscall_info['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')
                        
                data_to_insert = [
                (syscall_info['conclusion'], human_readable_timestamp),
                ]

                # data_to_insert = [
                # (syscall_info['conclusion'], human_readable_timestamp, syscall_info['cmd'], syscall_info['Syscall'], syscall_info['auid'], syscall_info['uid'], full_path),
                # ]

                # print(data_to_insert)

                with open(output_path, 'a') as f:
                    # Convert the list of tuples into a string
                    for data_tuple in data_to_insert:
                        # Join the tuple elements into a single string, separated by commas
                        f.write(', '.join(map(str, data_tuple)) + '\n' + '\n')
                                    
            buffer.clear()
            capture = False  
            openat = False  

        else:
            buffer.append(line)

        return syscall_info, capture, buffer
    return syscall_info, capture, buffer

def process_entire_log(input_file, timestamp_backup, output_path):
    syscall_info = {}
    buffer = []
    capture = False

    with open(input_file, 'r') as infile:
        lines = infile.readlines()
                    
        for line in lines:
            syscall_info, capture, buffer = process_log_line(line, syscall_info, capture, buffer, timestamp_backup, output_path)

    # Ensure that any remaining data in the buffer is processed
    if buffer:
        process_log_line('', syscall_info, capture, buffer, timestamp_backup, output_path)

def process_file(directory, base_name):
    """Process files with the same base name in the given directory and save the differences."""
    latest_files = get_latest_files(directory)
    if latest_files:
        
        for file_pair in latest_files:

            file1, file2 = [os.path.join(directory, f) for f in file_pair]

            diff = compare_files(file1, file2)

            # Create diff file name and directory structure
            relative_dir = os.path.relpath(directory, backup_dir)
            timestamp_backup = file_pair[1].split('_')[-1]


            # print(timestamp_backup)
  

            diff_file_name = f'{file_pair[1]}_diff.txt'
            output_dir = os.path.join(diff_dir, relative_dir)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, diff_file_name)

            process_entire_log(input_file, timestamp_backup, output_path)  

            save_diff(diff, output_path)

             

def save_diff(diff, output_path):

    """Save the diff to a file."""
    with open(output_path, 'a') as f:
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
            time.sleep(0.5)
            process_file(directory, base_name)

if __name__ == "__main__":
    w = Watcher(backup_dir)
    w.run()
