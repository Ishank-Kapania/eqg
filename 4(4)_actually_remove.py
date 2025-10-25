import os
import json

# Set source and destination folders
input_dir = '1(a)_output'
output_dir = '1(b)_output'

# Define the list of section headings to exclude
exclude_headings = {
'Introduction', 'Conclusion', 'Related Work', 'Acknowledgements', 'Limitations', 'Acknowledgments', 'Baselines', 'Conclusions', 'A Appendix', 'Acknowledgement', 'Background', 'Conclusion and Future Work', 'Related work', 'Related Works', 'Preliminaries', 'Overview', 'Appendix', 'Conclusions and Future Work', 'Bibliographical References', 'Acknowledgment', 'Baseline Models', 'Preliminary', 'Annotation', 'ACL 2023 Responsible NLP Checklist', 'Limitation', 'Background and Related Work', 'Baseline Methods', 'Baseline', 'A Appendices', 'Annotation Process', 'Future Work', 'B1. Did you cite the creators of artifacts you used?', 'Data Annotation', 'Summary', 'Reference', 'B Did you use or create scientific artifacts?', 'Appendices', 'Conclusion & Future Work', 'Limitations and Future Work', 'A. Appendix', 'Annotation Guidelines', 'Quantitative Results', 'B Additional Results', 'C Additional Results', 'Qualitative Results', 'Inter-Annotator Agreement', 'References', 'Related works', 'Result', 'Annotation Procedure', 'Annotation Scheme', 'Summarization', 'Conclusion and future work', 'Previous Work', 'A4. Have you used AI writing assistants when working on this paper?', 'Human Annotation', 'A2. Did you discuss any potential risks of your work?', 'A1. Did you describe the limitations of your work?', 'As shown in', 'Baseline Systems', 'Notations', 'Notation', 'Baseline models'
}

# Traverse through all files in the directory tree
for root, dirs, files in os.walk(input_dir):
    for filename in files:
        if filename.endswith(".json"):
            input_path = os.path.join(root, filename)
            
            # Determine output path by mirroring structure in output_dir
            relative_path = os.path.relpath(input_path, input_dir)
            output_path = os.path.join(output_dir, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Read original JSON file
            with open(input_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON: {input_path}")
                    continue

            # Filter out sections with headings in the exclusion list
            if isinstance(data, dict) and "sections" in data:
                data["sections"] = [
                    section for section in data["sections"]
                    if section.get("heading") not in exclude_headings
                ]

            # Write the modified JSON to new location
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

print(" All eligible JSON files processed into 1_5_output.")
