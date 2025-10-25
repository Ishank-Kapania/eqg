
import re
import os
import shutil
import chardet

def is_nonsensical_string(text):
    pattern = r'(?<!\S)(?:(?:[^\s])\s){15,}(?:[^\s])(?!\S)'
    matches = re.finditer(pattern, text)
    return [match.group() for match in matches if is_valid_match(match.group())]

def is_valid_match(match):
    parts = match.split()
    if len(parts) < 15:
        return False
    if not all(len(part) == 1 for part in parts):
        return False
    unique_chars = set(parts)
    if len(unique_chars) < 3:
        return False
    if re.match(r'^[0-9.]+$', ''.join(parts)):
        return False
    return True

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def process_file(input_file_path, output_file_path):
    try:
        # Check if output file already exists
        if os.path.exists(output_file_path):
            #print(f"Skipping {input_file_path} as output file already exists.")
            return False

        # Detect file encoding
        encoding = detect_encoding(input_file_path)
        
        with open(input_file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        nonsensical_strings = is_nonsensical_string(content)
        
        if nonsensical_strings:
            for nonsense in nonsensical_strings:
                content = content.replace(nonsense, '')
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)  
        else:
            shutil.copy2(input_file_path, output_file_path)
        return True
    except PermissionError:
        print(f"Permission denied: Unable to read or write {input_file_path}")
    except FileNotFoundError:
        print(f"File not found: {input_file_path}")
    except IsADirectoryError:
        print(f"Is a directory, not a file: {input_file_path}")
    except OSError as e:
        print(f"OS error occurred while processing {input_file_path}: {str(e)}")
    except Exception as e:
        print(f"Unexpected error processing {input_file_path}: {str(e)}")
    return False

def process_directory(input_directory, output_directory):
    processed_count = 0
    skipped_count = 0
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.endswith('.txt'):
                input_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_file_path, input_directory)
                output_file_path = os.path.join(output_directory, relative_path)
                
                if process_file(input_file_path, output_file_path):
                    processed_count += 1
                else:
                    skipped_count += 1
    
    print(f"Processing complete. Output directory: {output_directory}")
    print(f"Files processed: {processed_count}")
    print(f"Files skipped: {skipped_count}")

# Main execution
input_directory = os.path.join(os.getcwd(), '2_output')  # Change this to your input directory path
output_directory = os.path.join(os.getcwd(), '3_output')  # Change this to your desired output directory path

process_directory(input_directory, output_directory)