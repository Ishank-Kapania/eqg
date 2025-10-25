import os
import argparse
import openai
import time
import random

# Set your API key
openai.api_key = ''

# Directories
papers_dir = "/home2/ /my_code/7_output_complete"              # Input papers with header line
output_dir = "/home2/ /my_code/7_output_excerpt"      # Output folder after 3-stage processing

# The fixed header line to strip and re-attach
HEADER_LINE = "You are a reviewer for a research paper. Generate a questionnaire as a numbered list that analyzes any potential ethical considerations with the practices done in the research paper. Here is the research paper."

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


def process_paper(paper_path, output_path, verbose=False):
    """Processes one research paper through 3 updated stages."""
    
    # Load full text and strip the header line
    full_text = load_file(paper_path)
    if full_text.startswith(HEADER_LINE):
        paper_content = full_text[len(HEADER_LINE):].lstrip()
    else:
        print(f"Warning: Expected header line not found in {paper_path}")
        paper_content = full_text

    # === STAGE 1 ===
    stage1_prompt = f"""I am a reviewer focusing on the ethical aspects of the research paper below. Based on both the contents of this paper and your prior training on research methodologies, ethical issues in AI/ML, and best practices from published papers, please identify and highlight specific excerpts or sections I should examine closely for potential ethical concerns or implications.

Research Paper:
{paper_content}"""

    messages = [{"role": "user", "content": stage1_prompt}]
    stage1_response = call_chatbot(messages)
    if "An error occurred" in stage1_response:
        print(f"Stage 1 error for {paper_path}: {stage1_response}")
        return False

    # === STAGE 2 ===
    stage2_prompt = "From your previous response, please provide only the excerpts from the research paper - no ethical statement lines, no filler text, no explanations, just the raw excerpts themselves."

    messages.append({"role": "assistant", "content": stage1_response})
    messages.append({"role": "user", "content": stage2_prompt})
    stage2_response = call_chatbot(messages)
    if "An error occurred" in stage2_response:
        print(f"Stage 2 error for {paper_path}: {stage2_response}")
        return False

    # === STAGE 3 === (fresh chat)
    stage3_prompt = f"""Here is a research paper:
{paper_content}

Here are key excerpts from this paper:
{stage2_response}

Please provide a comprehensive summary of this research paper, ensuring that the provided excerpts are naturally integrated into your summary. Give no filler text except the summary"""
    stage3_response = call_chatbot([{"role": "user", "content": stage3_prompt}])
    if "An error occurred" in stage3_response:
        print(f"Stage 3 error for {paper_path}: {stage3_response}")
        return False

    # Add the header line back to final output
    final_output = f"{HEADER_LINE}\n\n{stage3_response.strip()}"

    # Save final summary
    save_output(output_path, final_output)
    print(f"Saved: {output_path}")

    # Save verbose log (without reattaching the header)
    if verbose:
        verbose_content = f"""=== STAGE 1: ETHICAL EXCERPT IDENTIFICATION ===
{stage1_response}

=== STAGE 2: RAW EXCERPTS ONLY ===
{stage2_response}

=== STAGE 3: FINAL SUMMARY ===
{stage3_response}"""
        base_name = os.path.splitext(output_path)[0]
        verbose_path = f"{base_name}_verbose.txt"
        save_output(verbose_path, verbose_content)
        print(f"Saved verbose: {verbose_path}")

    return True

def find_paper_files():
    """Returns all .txt file paths in the papers_dir."""
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
    parser = argparse.ArgumentParser(description='Ethical review and summarization pipeline with header handling')
    parser.add_argument('-v', '--verbose', action='store_true', help='Save all stages in verbose mode')
    args = parser.parse_args()

    os.makedirs(output_dir, exist_ok=True)

    paper_files = find_paper_files()
    if not paper_files:
        print("No papers found!")
        return

    print(f"Found {len(paper_files)} papers to process")

    for paper_path, output_path in paper_files:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if os.path.exists(output_path):
            verbose_path = f"{os.path.splitext(output_path)[0]}_verbose.txt"
            if not args.verbose or os.path.exists(verbose_path):
                print(f"Skipping {output_path} (already exists)")
                continue

        try:
            rel_path = os.path.relpath(paper_path, papers_dir)
            print(f"Processing: {rel_path}")
            process_paper(paper_path, output_path, args.verbose)
        except Exception as e:
            print(f"Error processing {paper_path}: {e}")

if __name__ == "__main__":
    main()
