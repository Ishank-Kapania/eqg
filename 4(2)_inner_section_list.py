import os
import json
from collections import Counter

def extract_headings_from_json(json_path):
    """Extract headings from a JSON file, supporting both dict and list root structures."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    headings = []

    if isinstance(data, dict):
        sections = data.get('sections', [])
        if isinstance(sections, list):
            headings = [section['heading'] for section in sections if isinstance(section, dict) and 'heading' in section]
    elif isinstance(data, list):
        # Sometimes the root is a list of sections directly
        headings = [section['heading'] for section in data if isinstance(section, dict) and 'heading' in section]
    else:
        print(f"Skipped {json_path}: unsupported root type {type(data).__name__}")

    return headings

def collect_headings(directory):
    """Walk through all subdirectories and collect headings from all JSON files."""
    heading_counter = Counter()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                try:
                    headings = extract_headings_from_json(json_path)
                    heading_counter.update(headings)
                except Exception as e:
                    print(f"Error reading {json_path}: {e}")
    # Sort the dictionary by frequency in descending order
    sorted_headings = dict(sorted(heading_counter.items(), key=lambda x: x[1], reverse=True))
    return sorted_headings

# Replace this with your actual directory path
your_directory = '1(a)_output'
heading_counts = collect_headings(your_directory)

# Save to a file named '4_section_heading.txt'
output_path = '4_section_heading.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(heading_counts, f, indent=4, ensure_ascii=False)

print(f"Saved heading counts to {output_path}")
