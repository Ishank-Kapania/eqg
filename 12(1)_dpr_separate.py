import os
import shutil

source_dir = '4_output_finetuning'
dest_dir = '5_output_dpr'
train_file_list = 'split_data/train.txt'

# Load the list of filenames to copy (just filenames, no paths)
with open(train_file_list, 'r', encoding='utf-8') as f:
    target_filenames = set(line.strip() for line in f if line.strip())

# Walk through source_dir recursively
for root, _, files in os.walk(source_dir):
    for file in files:
        if file in target_filenames:
            source_file_path = os.path.join(root, file)

            # Compute relative path from source_dir
            rel_path = os.path.relpath(source_file_path, source_dir)
            dest_file_path = os.path.join(dest_dir, rel_path)

            # Ensure destination subdirectory exists
            os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

            # Copy the file
            shutil.copy2(source_file_path, dest_file_path)
