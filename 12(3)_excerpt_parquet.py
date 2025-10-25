import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def create_parquet(input_dir, resultant_dir, output_file):
    instruction = "You are a reviewer for a research paper. Generate a questionnaire that analyzes any potential ethical considerations with the practices done in the research paper."
    data = []

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

    df = pd.DataFrame(data)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_file)
    print(f"Parquet file '{output_file}' has been created successfully with {len(df)} records.")

# Example usage
input_dir = "/home2/ /my_code/5_training_source_remade"
resultant_dir = "/home2/ /my_code/resultant_numbered"
output_file = "/home2/ /my_code/output_excerpt.parquet"
create_parquet(input_dir, resultant_dir, output_file)
