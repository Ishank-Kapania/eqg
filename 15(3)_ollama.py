
import requests
import json
import os
import hashlib
import sys
import time
from datetime import datetime
from requests.exceptions import Timeout

def get_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_processed_files(processed_files_path):
    if os.path.exists(processed_files_path):
        with open(processed_files_path, 'r') as f:
            return json.load(f)
    return {}

def save_processed_files(processed_files_path, processed_files):
    with open(processed_files_path, 'w') as f:
        json.dump(processed_files, f)

def log_exception(file_path, model_name, reason="Timeout"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("exceptions.txt", "a") as f:
        f.write(f"{timestamp} - {reason} processing: {file_path} - Model: {model_name}\n")

def process_file(file_path, output_path, model_name):
    print(f"Currently on: {file_path}")
    start_time = time.time()
    
    try:
        with open(file_path, 'r') as file:
            prompt = file.read()
        
        url = "http://localhost:11434/api/generate"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        # Set a hard timeout of 60 seconds for the request
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)
        except Timeout:
            print(f"Request timed out for {file_path}")
            log_exception(file_path, model_name, "Hard timeout")
            return False
        
        # Check if more than 20 seconds have passed
        if time.time() - start_time > 20:
            log_exception(file_path, model_name, "Soft timeout")
            return False
        
        if response.status_code == 200:
            response_text = response.text
            data = json.loads(response_text)
            actual_response = data["response"]
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as out_file:
                out_file.write(actual_response)
            print(f"Processed: {file_path}")
            return True
        else:
            print(f"Error processing {file_path}:", response.status_code, response.text)
            log_exception(file_path, model_name, f"HTTP Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        log_exception(file_path, model_name, f"Error: {str(e)}")
        return False

def process_directory(input_dir, output_dir, model_name):
    processed_files_path = os.path.join(output_dir, "processed_files.json")
    processed_files = load_processed_files(processed_files_path)
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.txt'):
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, relative_path)
                file_hash = get_file_hash(input_path)
                
                if relative_path in processed_files and processed_files[relative_path] == file_hash:
                    print(f"Skipping already processed file: {relative_path}")
                    continue
                
                success = process_file(input_path, output_path, model_name)
                if success:
                    processed_files[relative_path] = file_hash
                    save_processed_files(processed_files_path, processed_files)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 /scratch/ik/10_ollama.py <input_directory> <output_directory> <model_name>")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    model_name = sys.argv[3]
    
    process_directory(input_directory, output_directory, model_name)

