import os
import json

def process_ethics_files(source_dir, target_dir):
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if 'ethics' in file and file.endswith('.json'):
                # Construct the full file path
                source_file = os.path.join(root, file)
                # Create the new filename without 'ethics' and change extension to .txt
                new_filename = file.replace('_ethics', '').replace('.json', '.txt')
                # Construct the new file path in the target directory
                relative_path = os.path.relpath(root, source_dir)
                target_path = os.path.join(target_dir, relative_path)
                target_file = os.path.join(target_path, new_filename)
                # Create the directory structure if it doesn't exist
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                # Read the JSON file
                with open(source_file, 'r') as json_file:
                    data = json.load(json_file)
                # Extract heading and text
                heading = data[0].get('heading', '')
                text = data[0].get('text', '')

                # Write to the new text file
                with open(target_file, 'w') as txt_file:
                    txt_file.write(f"{heading}\n\n{text}")
                print(f"Processed {source_file} to {target_file}")
source_directory = "1(a)_output"
target_directory = "6_output"

process_ethics_files(source_directory, target_directory)