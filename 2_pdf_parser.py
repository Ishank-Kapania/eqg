import os
import requests
import scipdf
import json
from urllib.parse import urlparse
import warnings
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def download_pdf(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    return False

def parse_pdf(pdf_file):
    try:
        result = scipdf.parse_pdf_to_dict(pdf_file)
        if isinstance(result, tuple):
            return result[0], None
        else:
            return result, None
    except Exception as e:
        return None, str(e)

def save_ethics_section(json_data, output_file):
    ethics_sections = []
    for section in json_data.get('sections', []):
        if 'ethic' in section.get('heading', '').lower():
            ethics_sections.append(section)
   
    if ethics_sections:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ethics_sections, f, ensure_ascii=False, indent=4)
        print(f"Ethics section saved to: {output_file}")
    else:
        print("No ethics section found in the document.")

def log_error(pdf_name, error_message):
    with open('errors.txt', 'a') as f:
        f.write(f"{pdf_name}: {error_message}\n")

def process_url_file(file_path):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join('output', base_name)
    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, 'r') as f:
        urls = f.read().splitlines()
    for url in urls:
        parsed_url = urlparse(url)
        pdf_name = os.path.splitext(os.path.basename(parsed_url.path))[0]
        pdf_name = pdf_name.replace('.', '_')
        pdf_path = os.path.join(output_dir, f"{pdf_name}.pdf")
        if download_pdf(url, pdf_path):
            article_dict, error = parse_pdf(pdf_path)
            if article_dict is not None:
                json_output = os.path.join(output_dir, f"{pdf_name}.json")
                with open(json_output, 'w', encoding='utf-8') as f:
                    json.dump(article_dict, f, ensure_ascii=False, indent=4)
               
                ethics_output = os.path.join(output_dir, f"{pdf_name}_ethics.json")
                save_ethics_section(article_dict, ethics_output)
               
                print(f"Processed: {url}")
                print(f"Output saved to: {json_output}")
            else:
                print(f"Failed to parse PDF: {pdf_path}")
                log_error(pdf_name, error)
            
            os.remove(pdf_path)
            print(f"PDF file deleted: {pdf_path}")
        else:
            print(f"Failed to download: {url}")
            log_error(pdf_name, "Failed to download")

def main():
    dataset_dir = 'dataset'
    if not os.path.exists(dataset_dir):
        print(f"Error: '{dataset_dir}' directory not found.")
        return
    for file in os.listdir(dataset_dir):
        if file.endswith('.txt'):
            file_path = os.path.join(dataset_dir, file)
            print(f"Processing file: {file}")
            process_url_file(file_path)

if __name__ == "__main__":
    main()