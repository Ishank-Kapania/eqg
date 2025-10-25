import os
import json
from collections import defaultdict

def get_all_files(base_folders):
    """
    Get all files organized by subdirectory and filename
    Returns a dictionary with structure:
    {subdirectory: {filename: {folder: content}}}
    """
    file_structure = defaultdict(lambda: defaultdict(dict))

    for base_folder in base_folders:
        if not os.path.exists(base_folder):
            print(f"Warning: Folder '{base_folder}' does not exist")
            continue

        # Walk through all subdirectories
        for subdir in os.listdir(base_folder):
            subdir_path = os.path.join(base_folder, subdir)

            if os.path.isdir(subdir_path):
                # Process files in subdirectory
                for filename in os.listdir(subdir_path):
                    file_path = os.path.join(subdir_path, filename)

                    if os.path.isfile(file_path):
                        try:
                            # The folder name itself is used as the key for content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            file_structure[subdir][filename][base_folder] = content
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")

    return file_structure

def create_combined_json(file_structure, num_files):
    """
    Create a JSON structure combining files from all three folders
    and stops after processing 'num_files' entries.
    """
    combined_data = []
    file_count = 0

    # Iterate through subdirectories and files
    for subdir, files in file_structure.items():
        for filename, folder_contents in files.items():
            # Only include files that exist in all three folders (len == 3)
            if len(folder_contents) == 3:
                entry = {
                    "subdirectory": subdir,
                    "filename": filename,
                    # Get content from the three hardcoded folder names, or an empty string if missing
                    "4_output_count": folder_contents.get("4_output_count", ""),
                    "6_output": folder_contents.get("6_output", ""),
                    "resultant_numbered": folder_contents.get("resultant_numbered", "")
                }
                combined_data.append(entry)
                file_count += 1

            if file_count >= num_files:
                return combined_data

    return combined_data

# --- Main Execution ---

# Hardcoded values
base_folders = ["4_output_count", "6_output", "resultant_numbered"]
num_files = 3663 # Change this to the number of files you want
output_filename = "combined_output.json"

print(f"Processing folders: {', '.join(base_folders)}")
print(f"Requested number of files: {num_files}")

# Get all files from the folders
file_structure = get_all_files(base_folders)

# Count total available files (that exist in all three folders)
total_available = 0
for subdir, files in file_structure.items():
    for filename, folder_contents in files.items():
        if len(folder_contents) == 3: # File exists in all three folders
            total_available += 1

print(f"\nMaximum number of files available: {total_available}")

if num_files > total_available:
    print(f"Warning: Requested {num_files} files, but only {total_available} are available")
    print(f"Creating JSON with all {total_available} available files")
    num_files_to_process = total_available
else:
    num_files_to_process = num_files

# Create combined JSON
combined_data = create_combined_json(file_structure, num_files_to_process)

# Save to JSON file
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
except IOError as e:
    print(f"\nError saving JSON file: {e}")
    exit()

print(f"\nJSON file created: {output_filename}")
print(f"Number of entries in JSON: {len(combined_data)}")

# Print sample of the JSON structure
if combined_data:
    print("\nSample entry from JSON:")
    sample = json.dumps(combined_data[0], indent=2)
    # Truncate if the sample is very long
    if len(sample) > 500:
        print(sample[:500] + "\n...")
    else:
        print(sample)