import os
import argparse
import openai
import time
import random

# Hardcoded configuration
openai.api_key = ''
papers_dir = "/home2/ /my_code/5_training_source"  # Directory containing research papers
ethics_dir = "/home2/ /my_code/6_output"  # Directory containing ethical statements  
output_dir = "/home2/ /my_code/5_training_source_remade"  # Output directory

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




def process_paper(paper_path, ethics_path, output_path, verbose=False):
    """Process a single paper through the three-stage pipeline."""
    
    # Load input files
    paper_content = load_file(paper_path)
    ethics_content = load_file(ethics_path)
    
    # Stage 1: Analyze ethical statements against research paper
    stage1_prompt = f"""Here is the complete research paper:
{paper_content}

Here is the ethical statement for this research paper:
{ethics_content}

Analyze each line of the ethical statement and, for each one, identify the most relevant excerpt(s) from the research paper that support or directly relate to it. """
    
    messages = [{"role": "user", "content": stage1_prompt}]
    stage1_response = call_chatbot(messages)
    
    if "An error occurred" in stage1_response:
        print(f"Stage 1 error for {paper_path}: {stage1_response}")
        return False
    
    # Stage 2: Extract clean excerpts
    stage2_prompt = """From your previous response, please provide only the excerpts from the research paper - no ethical statement lines, no filler text, no explanations, just the raw excerpts themselves."""
    
    messages.append({"role": "assistant", "content": stage1_response})
    messages.append({"role": "user", "content": stage2_prompt})
    stage2_response = call_chatbot(messages)
    
    if "An error occurred" in stage2_response:
        print(f"Stage 2 error for {paper_path}: {stage2_response}")
        return False
    
    # Stage 3: Generate summary (fresh conversation)
    stage3_prompt = f"""Here is a research paper:
{paper_content}

Here are key excerpts from this paper:
{stage2_response}

Please provide a comprehensive summary of this research paper, ensuring that the provided excerpts are naturally integrated into your summary. Give no filler text except the summary"""
    
    fresh_messages = [{"role": "user", "content": stage3_prompt}]
    stage3_response = call_chatbot(fresh_messages)
    
    if "An error occurred" in stage3_response:
        print(f"Stage 3 error for {paper_path}: {stage3_response}")
        return False
    
    # Save final output
    save_output(output_path, stage3_response)
    print(f"Saved: {output_path}")
    
    # Save verbose output if requested
    if verbose:
        verbose_content = f"""=== STAGE 1: ETHICAL ANALYSIS ===
{stage1_response}

=== STAGE 2: EXTRACTED EXCERPTS ===
{stage2_response}

=== STAGE 3: FINAL SUMMARY ===
{stage3_response}"""
        
        base_name = os.path.splitext(output_path)[0]
        verbose_path = f"{base_name}_verbose.txt"
        save_output(verbose_path, verbose_content)
        print(f"Saved verbose: {verbose_path}")
    
    return True

def find_paper_files():
    """Find all paper files and their corresponding ethics files."""
    paper_files = []
    
    for root, dirs, files in os.walk(papers_dir):
        for file in files:
            if file.endswith('.txt'):
                paper_path = os.path.join(root, file)
                
                # Create corresponding ethics path
                rel_path = os.path.relpath(paper_path, papers_dir)
                ethics_path = os.path.join(ethics_dir, rel_path)
                
                # Create corresponding output path
                output_path = os.path.join(output_dir, rel_path)
                
                if os.path.exists(ethics_path):
                    paper_files.append((paper_path, ethics_path, output_path))
                else:
                    print(f"Warning: No matching ethics file for {paper_path}")
    
    return paper_files

def main():
    parser = argparse.ArgumentParser(description='Process research papers through three-stage ethics pipeline')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Save detailed output showing all three stages')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all paper files
    paper_files = find_paper_files()
    
    if not paper_files:
        print("No matching paper-ethics file pairs found!")
        return
    
    print(f"Found {len(paper_files)} paper-ethics pairs to process")
    
    # Process each file
    for paper_path, ethics_path, output_path in paper_files:
        # Create output directory structure
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Skip if already exists (unless verbose and verbose file doesn't exist)
        if os.path.exists(output_path):
            verbose_path = f"{os.path.splitext(output_path)[0]}_verbose.txt"
            if not args.verbose or os.path.exists(verbose_path):
                print(f"Skipping {output_path} (already exists)")
                continue
        
        try:
            rel_path = os.path.relpath(paper_path, papers_dir)
            print(f"Processing: {rel_path}")
            process_paper(paper_path, ethics_path, output_path, args.verbose)
        except Exception as e:
            print(f"Error processing {paper_path}: {e}")

if __name__ == "__main__":
    main()