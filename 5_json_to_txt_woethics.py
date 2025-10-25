import os
import json

def extract_content(json_data, excluded_sections):
    content = []
    
    if 'title' in json_data:
        content.append(f"Title: {json_data['title']}\n")
    #if 'authors' in json_data:
    #    content.append(f"Authors: {json_data['authors']}\n")
    #if 'abstract' in json_data:
    #    content.append(f"Abstract: {json_data['abstract']}\n\n")
    
    if 'sections' in json_data:
        for section in json_data['sections']:
            if 'ethic' not in section['heading'].lower() and section['heading'].lower() not in excluded_sections:
                section_content = f"{section['heading']}\n{section['text']}\n\n"
                content.append(section_content)
    
    return ''.join(content)

def process_json_files(input_dir, output_dir, excluded_sections):
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json'):
                input_path = os.path.join(root, file)
                
                # Create corresponding output directory
                relative_path = os.path.relpath(root, input_dir)
                output_subdir = os.path.join(output_dir, relative_path)
                os.makedirs(output_subdir, exist_ok=True)
                
                output_path = os.path.join(output_subdir, f"{os.path.splitext(file)[0]}.txt")
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as json_file:
                        json_data = json.load(json_file)
                    
                    content = extract_content(json_data, excluded_sections)
                    
                    with open(output_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(content)
                except Exception as e:
                    print(f"Error processing file {input_path}: {str(e)}")

# Main execution
if __name__ == "__main__":
    to_use = input('To use the complete research paper (human evaluation) , or the research paper with redundant sections removed (finetuning) (1 or 2)\n')
    if to_use == '1':
        input_directory = "1(a)_output"
    elif to_use == '2':
        input_directory = "1(b)_output"

    output_directory = "2_output"
    excluded_sections = []  # Add more sections to exclude as needed
    process_json_files(input_directory, output_directory, excluded_sections)
    print("Extraction complete. Check the output folder for results.")