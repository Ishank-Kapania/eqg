import re
import os

def is_nonsensical_string(text):
    # Pattern to match sequences of characters separated by spaces
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
    # Check if it's not a common valid sequence (like a table of contents)
    if re.match(r'^[0-9.]+$', ''.join(parts)):
        return False
    return True

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return is_nonsensical_string(content)
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return []

def process_directory(directory, collection_file):
    with open(collection_file, 'w', encoding='utf-8') as cf:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    nonsensical_strings = process_file(file_path)
                    if nonsensical_strings:
                        print(f"Nonsensical string(s) found in: {file_path}")
                        cf.write(f"File: {file_path}\n")
                        for string in nonsensical_strings:
                            cf.write(f"Nonsensical string: {string}\n")
                        cf.write("\n")
    print(f"Results written to {collection_file}")

# Main execution
output_directory = os.path.join(os.getcwd(), 'processed_output')
collection_file = 'nonsensical_strings.txt'
process_directory(output_directory, collection_file)