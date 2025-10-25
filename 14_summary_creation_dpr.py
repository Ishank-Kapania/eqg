import os
import argparse
import openai
import time
import random


# Set your API key
openai.api_key = ''

# Directories
papers_dir = "/home2/ /my_code/7_output_complete"    # Input: research papers (.txt)
output_dir = "/home2/ /my_code/7_output_sum"   # Output: final summaries

def load_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def save_output(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

MODEL_NAME = "gpt-4o-mini"  # ← switch to "gpt-4o" if needed

def call_chatbot(messages, retries=5, backoff_base=2):
    """Call OpenAI chat completion with retry and throttling."""
    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model=MODEL_NAME,
                messages=messages
            )
            time.sleep(1.1)  # throttle to stay within rate limits
            return response.choices[0].message.content.strip()
        except openai.RateLimitError:
            wait = backoff_base ** attempt + random.uniform(0, 1)
            print(f"[RateLimit] Retrying in {wait:.2f} seconds...")
            time.sleep(wait)
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(2)  # Short cooldown before next retry
    return "An error occurred: Max retries exceeded."


def process_paper(paper_path, output_path):
    paper_content = load_file(paper_path)

    prompt = f"""Give a detailed summary of this research paper , give no filler text except the summary:

{paper_content}"""

    messages = [{"role": "user", "content": prompt}]
    response = call_chatbot(messages)

    if "An error occurred" in response:
        print(f"Error for {paper_path}: {response}")
        return False

    save_output(output_path, response)
    print(f"Saved: {output_path}")
    return True

def find_paper_files():
    paper_files = []
    for root, _, files in os.walk(papers_dir):
        for file in files:
            if file.endswith('.txt'):
                paper_path = os.path.join(root, file)
                rel_path = os.path.relpath(paper_path, papers_dir)
                output_path = os.path.join(output_dir, rel_path)
                paper_files.append((paper_path, output_path))
    return paper_files

def main():
    os.makedirs(output_dir, exist_ok=True)

    paper_files = find_paper_files()
    if not paper_files:
        print("No papers found!")
        return

    print(f"Found {len(paper_files)} papers to process")

    for paper_path, output_path in paper_files:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if os.path.exists(output_path):
            print(f"Skipping {output_path} (already exists)")
            continue

        try:
            rel_path = os.path.relpath(paper_path, papers_dir)
            print(f"Processing: {rel_path}")
            process_paper(paper_path, output_path)
        except Exception as e:
            print(f"Error processing {paper_path}: {e}")

if __name__ == "__main__":
    main()
