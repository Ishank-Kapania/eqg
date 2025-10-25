import os
import json
from pathlib import Path
from collections import defaultdict

def find_common_files(base_directory, model_folders, num_files=50):
    """
    Find common files across all model folders, resultant_numbered, and 7_output_excerpt
    
    Args:
        base_directory: Path to the main directory
        model_folders: List of model folder names
        num_files: Number of files to extract (default: 50)
    
    Returns:
        List of tuples containing (relative_path, filename_without_extension)
    """
    base_path = Path(base_directory)
    
    # Dictionary to store file paths for each folder
    folder_files = {}
    
    # Get all folders to check (model folders + output folders)
    all_folders = model_folders + ['resultant_numbered', '7_output_excerpt']
    
    # Collect all files from each folder
    for folder in all_folders:
        folder_path = base_path / folder
        if not folder_path.exists():
            print(f"Warning: Folder {folder} does not exist")
            continue
            
        folder_files[folder] = set()
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.txt'):
                    # Get relative path from folder root
                    rel_path = os.path.relpath(os.path.join(root, file), folder_path)
                    folder_files[folder].add(rel_path)
    
    # Find common files across all folders
    common_files = None
    for folder in all_folders:
        if folder in folder_files:
            if common_files is None:
                common_files = folder_files[folder].copy()
            else:
                common_files = common_files.intersection(folder_files[folder])
    
    if common_files is None:
        return []
    
    # Convert to list and limit to specified number
    common_files_list = list(common_files)[:num_files]
    
    # Return as tuples of (relative_path, filename_without_extension)
    result = []
    for file_path in common_files_list:
        filename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(filename)[0]
        result.append((file_path, filename_without_ext))
    
    return result

def read_file_content(file_path):
    """
    Read content from a text file
    
    Args:
        file_path: Path to the file
    
    Returns:
        File content as string, or empty string if file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read file {file_path}: {e}")
        return ""

def strip_instruction_from_content(content, instruction):
    """
    Strip the instruction from the beginning of the content if it exists
    
    Args:
        content: The file content
        instruction: The instruction text to remove
    
    Returns:
        Content with instruction stripped from the beginning
    """
    # Remove leading/trailing whitespace for comparison
    content_stripped = content.strip()
    instruction_stripped = instruction.strip()
    
    # Check if content starts with the instruction
    if content_stripped.startswith(instruction_stripped):
        # Remove the instruction and any following whitespace
        remaining_content = content_stripped[len(instruction_stripped):].strip()
        return remaining_content
    
    # If instruction not found at the beginning, return original content
    return content

def generate_json(base_directory, model_folders, num_files=50, output_file="example.json"):
    """
    Generate the JSON file with the specified structure
    
    Args:
        base_directory: Path to the main directory
        model_folders: List of model folder names
        num_files: Number of files to extract (default: 50)
        output_file: Output JSON file name
    """
    base_path = Path(base_directory)
    
    # Find common files
    common_files = find_common_files(base_directory, model_folders, num_files)
    
    if not common_files:
        print("No common files found across all folders")
        return
    
    # Fixed instruction text
    instruction = "You are a reviewer for a research paper. Generate a questionnaire as a numbered list that analyzes any potential ethical considerations with the practices done in the research paper. Here is the research paper."
    
    # Generate JSON data
    json_data = []
    
    for file_path, file_id in common_files:
        # Read input from 7_output_excerpt
        input_file = base_path / "7_output_excerpt" / file_path
        input_content = read_file_content(input_file)
        
        # Strip instruction from input content for JSON only
        input_content_cleaned = strip_instruction_from_content(input_content, instruction)
        
        # Read output from resultant_numbered
        output_file_path = base_path / "resultant_numbered" / file_path
        output_content = read_file_content(output_file_path)
        
        # Read candidates from model folders
        candidates = []
        for model_folder in model_folders:
            candidate_file = base_path / model_folder / file_path
            candidate_content = read_file_content(candidate_file)
            
            candidates.append({
                "model": model_folder,
                "text": candidate_content
            })
        
        # Create entry
        entry = {
            "id": file_id,
            "instruction": instruction,
            "input": input_content_cleaned,  # Using cleaned content here
            "output": output_content,
            "candidates": candidates
        }
        
        json_data.append(entry)
    
    # Write JSON file to the base directory
    output_json_path = base_path / output_file
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {output_json_path} with {len(json_data)} entries")


if __name__ == "__main__":
    # Configuration
    BASE_DIRECTORY = "/home2/ /my_code"  # Update this path
    MODEL_FOLDERS = ["gemma_output", "gemma12_outputX", "gemma27_outputX"]    # Update with your model folder names
    NUM_FILES = 2  # Number of files to extract
    OUTPUT_FILE = "example.json"
    
    # Generate the JSON file
    generate_json(BASE_DIRECTORY, MODEL_FOLDERS, NUM_FILES, OUTPUT_FILE)