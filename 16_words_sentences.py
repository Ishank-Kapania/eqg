import os
import re

def count_words_and_sentences(text):
    words = text.split()
    sentences = re.split(r'[.!?](?:\s|$)', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(words), len(sentences)

def analyze_folder(folder_path, output_lines):
    output_lines.append(f"\nAnalyzing folder: {folder_path}")
    total_words = 0
    total_sentences = 0
    total_files = 0

    for subdir in os.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir)
        if os.path.isdir(subdir_path):
            files = [f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))]
            output_lines.append(f"{subdir}: {len(files)} files")

            for file in files:
                file_path = os.path.join(subdir_path, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        words, sentences = count_words_and_sentences(content)
                        total_words += words
                        total_sentences += sentences
                        total_files += 1
                except Exception as e:
                    output_lines.append(f"Could not read {file_path}: {e}")

    if total_files > 0:
        avg_words = total_words / total_files
        avg_sentences = total_sentences / total_files
        output_lines.append(f"\nSummary for {folder_path}:")
        output_lines.append(f"Average words per file: {avg_words:.2f}")
        output_lines.append(f"Average sentences per file: {avg_sentences:.2f}")
    else:
        output_lines.append(f"No readable text files found in {folder_path}.")

# Collect all output lines
output_lines = []

# Run for both folders
analyze_folder("4_output_count", output_lines)
analyze_folder("6_output", output_lines)

# Save to file
with open("16_words_sentences.txt", "w", encoding="utf-8") as out_file:
    for line in output_lines:
        out_file.write(line + "\n")
