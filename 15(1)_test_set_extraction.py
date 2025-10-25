import os
import shutil
from pathlib import Path

def add_reviewer_prompt(file_path):
    """Add reviewer prompt at the start of the file."""
    prompt = "You are a reviewer for a research paper. Generate a questionnaire as a numbered list that analyzes any potential ethical considerations with the practices done in the research paper. Here is the research paper. \n\n"
    
    # Read the existing content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Write the prompt and original content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(prompt + content)

def extract_files(source_dir, target_files_path, output_dir):
    # Read the list of target filenames
    with open(target_files_path, 'r') as f:
        target_files = set(line.strip() for line in f if line.strip())
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Walk through the source directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file in target_files:
                # Get the relative path from source directory
                rel_path = os.path.relpath(root, source_dir)
                
                # Construct the destination path
                dest_dir = os.path.join(output_dir, rel_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                # Copy the file
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dest_file)
                
                # If the output directory is "7_output", add the reviewer prompt
                if output_dir == "7_output":
                    add_reviewer_prompt(dest_file)
                
                print(f"Copied and modified: {src_file} -> {dest_file}")

def main():
    try:
        extract_files("4_output", "split_data/test.txt", "7_output")
        print("Extraction completed successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        extract_files("6_output", "split_data/test.txt", "8_output")
        print("Extraction completed successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input("Ensure 5_output does not have ethic section (5_json_to_txt_woethics.py is ran)")
    main()