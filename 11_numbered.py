import os
import re

def clean_questions(input_text):
    # Regular expression to match numbered questions
    pattern = r'^\d+\.\s.*?$'
    
    # Find all matches in the input text
    matches = re.findall(pattern, input_text, re.MULTILINE)
    
    # Join the matches into a single string
    return '\n'.join(matches)

def process_directory(input_dir, output_dir):
    print(f"Processing directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Walk through the directory structure
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.txt'):
                input_path = os.path.join(root, file)
                print(f"Processing file: {input_path}")
                
                # Create a corresponding output path
                rel_path = os.path.relpath(root, input_dir)
                output_path = os.path.join(output_dir, rel_path, file)
                
                # Create necessary subdirectories in the output
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Process the file
                with open(input_path, 'r') as infile:
                    content = infile.read()
                    
                cleaned_content = clean_questions(content)
                
                # Write the cleaned content to the output file
                with open(output_path, 'w') as outfile:
                    outfile.write(cleaned_content)
                
                print(f"Wrote cleaned content to: {output_path}")

if __name__ == "__main__":
    # Usage
    input_directory = '/home2/ /my_code/resultant'
    output_directory = '/home2/ /my_code/resultant_numbered'
    
    print("Starting script execution...")
    process_directory(input_directory, output_directory)
    print("Script execution completed.")