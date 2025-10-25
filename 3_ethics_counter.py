import os
import json

def count_papers_and_ethics():
    output_dir = '1(a)_output'
    total_papers = 0
    total_ethics_sections = 0

    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.json') and not file.endswith('_ethics.json'):
                total_papers += 1
            elif file.endswith('_ethics.json'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    ethics_data = json.load(f)
                    if ethics_data:  # Check if the ethics file is not empty
                        total_ethics_sections += 1

    return total_papers, total_ethics_sections

def main():
    papers, ethics = count_papers_and_ethics()
    print(f"Total research papers extracted: {papers}")
    print(f"Total ethics sections extracted: {ethics}")

if __name__ == "__main__":
    main()