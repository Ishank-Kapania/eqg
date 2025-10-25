import os
import json
from collections import Counter
def extract_keys(json_data, keys_counter):
    keys_counter.update(json_data.keys())    
    if 'sections' in json_data:
        for section in json_data['sections']:
            keys_counter.update(section.keys())
def list_json_keys(input_dir):
    keys_counter = Counter()
    file_count = 0
    json_count = 0
    print(f"Starting to traverse directory: {input_dir}")
    for root, dirs, files in os.walk(input_dir):
        print(f"Current directory: {root}")
        print(f"Files found: {files}")
        for file in files:
            file_count += 1
            if file.endswith('.json') and 'ethics' not in file.lower():
                json_count += 1
                input_path = os.path.join(root, file)                
                try:
                    with open(input_path, 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                    extract_keys(json_data, keys_counter)
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error in file {input_path}: {str(e)}")
                except IOError as e:
                    print(f"I/O error({e.errno}): {e.strerror} - File: {input_path}")
                except Exception as e:
                    print(f"Unexpected error processing file {input_path}: {str(e)}")
            elif 'ethics' in file.lower():
                pass
    print(f"\nTotal files found: {file_count}")
    print(f"JSON files processed: {json_count}")
    return keys_counter
if __name__ == "__main__":
    input_directory = "1(a)_output"  # This is the directory containing your JSON files
    
    if not os.path.exists(input_directory):
        print(f"Error: The directory '{input_directory}' does not exist.")
    else:
        keys_counter = list_json_keys(input_directory)
        print("\nList of all keys found in JSON files:")
        for key, count in keys_counter.most_common():
            print(f"{key}: {count}")
        print("\nKey listing complete.")