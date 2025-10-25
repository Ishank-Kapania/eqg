import os
import json

def extract_content(json_data, excluded_sections):
    content = []
    ethics_sections = []
    
    if 'title' in json_data:
        content.append(f"Title: {json_data['title']}\n")
    #if 'authors' in json_data:
    #    content.append(f"Authors: {json_data['authors']}\n")
    #if 'abstract' in json_data:
    #    content.append(f"Abstract: {json_data['abstract']}\n\n")
    
    if 'sections' in json_data:
        for section in json_data['sections']:
            if section['heading'].lower() not in excluded_sections:
                section_content = f"{section['heading']}\n{section['text']}\n\n"
                if 'ethic' in section['heading'].lower():
                    ethics_sections.append(section_content)
                content.append(section_content)
    
    # Add ethics sections at the end
    if ethics_sections:
        content.append("SEPARATOR\n\n")
        content.extend(ethics_sections)
    
    return ''.join(content)

def process_json_files(input_dir, output_dir, excluded_sections):
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json') and 'ethics' not in file.lower():
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
            elif 'ethics' in file.lower():
                pass

# Main execution
if __name__ == "__main__":
    input_directory = "1(b)_output"
    output_directory = "2_output"
    excluded_sections = []  # Add more sections to exclude as needed
    process_json_files(input_directory, output_directory, excluded_sections)
    print("Extraction complete. Check the output folder for results.")