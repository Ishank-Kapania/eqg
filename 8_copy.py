import os
import shutil
def process_files(source_dir, target_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if 'ethics' in file:
                new_filename = file.replace('_ethics', '')
                new_filename = new_filename.replace('.json','.txt')
                rel_path = os.path.relpath(root, source_dir)
                target_file_path = os.path.join(target_dir, rel_path, new_filename)
                if os.path.exists(target_file_path):
                    output_subdir = os.path.join(output_dir, rel_path)
                    if not os.path.exists(output_subdir):
                        os.makedirs(output_subdir)
                    output_file_path = os.path.join(output_subdir, new_filename)
                    shutil.copy2(target_file_path, output_file_path)
                    print(f"Copied {target_file_path} to {output_file_path}")
source_directory = "1(b)_output"
target_directory = "3_output"
output_directory = "4_output"
process_files(source_directory, target_directory, output_directory)