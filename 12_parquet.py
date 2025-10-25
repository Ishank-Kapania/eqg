import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.model_selection import train_test_split

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def create_parquet_and_split(input_dir, resultant_dir, output_file, train_ratio=0.8):
    instruction = "You are a reviewer for a research paper. Generate a questionnaire that analyzes any potential ethical considerations with the practices done in the research paper."
    data = []
    file_names = []
    for root, _, files in os.walk(input_dir):
        rel_path = os.path.relpath(root, input_dir)
        resultant_subdir = os.path.join(resultant_dir, rel_path)
        for file in files:
            input_file = os.path.join(root, file)
            resultant_file = os.path.join(resultant_subdir, file)
            if os.path.exists(resultant_file):
                input_content = read_file_content(input_file)
                output_content = read_file_content(resultant_file)
                data.append({
                    'instruction': instruction,
                    'input': input_content,
                    'output': output_content
                })
                file_names.append(file)
    
    df = pd.DataFrame(data)
    
    # Create the full Parquet file
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_file)
    print(f"Parquet file '{output_file}' has been created successfully.")
    
    # Split the file names into train and test sets
    train_files, test_files = train_test_split(file_names, train_size=train_ratio, random_state=42)
    
    # Create a directory to store the output files
    output_dir = '/home2/ /my_code/split_data'
    os.makedirs(output_dir, exist_ok=True)
    # Save the train and test sets as Parquet files
    train_df = df.iloc[[file_names.index(file) for file in train_files]]
    test_df = df.iloc[[file_names.index(file) for file in test_files]]
    train_df.to_parquet(os.path.join(output_dir, 'train.parquet'))
    test_df.to_parquet(os.path.join(output_dir, 'test.parquet'))
    # Save the file names to train.txt and test.txt
    with open(os.path.join(output_dir, 'train.txt'), 'w') as f:
        for file in train_files:
            f.write(f"{file}\n")
    with open(os.path.join(output_dir, 'test.txt'), 'w') as f:
        for file in test_files:
            f.write(f"{file}\n")    
    print(f"Train set size: {len(train_files)}")
    print(f"Test set size: {len(test_files)}")
    print(f"Files saved in the '{output_dir}' directory.")

input_dir = "/home2/ /my_code/4_output"
resultant_dir = "/home2/ /my_code/resultant_numbered"
output_file = "/home2/ /my_code/output.parquet"
create_parquet_and_split(input_dir, resultant_dir, output_file)