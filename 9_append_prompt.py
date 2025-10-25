import os

def process_files(input_directory, output_directory):
    intro_text = "Read this research paper for context, later I will ask you to do some task on it\n\n"

    few_shot_prompt = """ 
    The task
    Now I will be giving you ethical section of above paper again and I want you to convert its content into a series of questions. Each question should be directly based on information explicitly stated in the section that I give. Do not create questions that go beyond the scope of what is specifically mentioned in this section.  The goal is to transform the key points and considerations from this section into a set of clear, focused questions that reflect the ethical aspects discussed in the paper. Don't include unnecessary text like "here are the questions" in your responses. Only give the questions as a numbered list in this format.
    1- question 1 
    2- question 2 
    3- question 3 
    Now here is the snippet of ethical section from our research paper

    """

    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.endswith('.txt'):
                input_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_file_path, input_directory)
                output_file_path = os.path.join(output_directory, relative_path)
                
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace SEPARATOR with few-shot prompt
                few_shot_content = content.replace("SEPARATOR", few_shot_prompt)
                
                # Write few-shot file (without suffix)
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(intro_text + few_shot_content)
                
                print(f"Processed: {input_file_path}")
                print(f"Created: {output_file_path}")

    print("All files processed successfully.")

# Use the current directory as the starting point for input
input_directory = r'4_output'
output_directory = r'5_output'

process_files(input_directory, output_directory)