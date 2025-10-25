import requests
import json
import os
import hashlib
import sys
import time
from datetime import datetime
from requests.exceptions import Timeout
import spacy
from transformers import BertTokenizer
from typing import List, Tuple


class TextChunker:
    """A class for intelligently splitting text into chunks based on semantic boundaries."""
    
    def __init__(self, tokenizer_name: str = 'bert-base-uncased', spacy_model: str = "en_core_web_sm"):
        """
        Initialize the TextChunker with required models.
        
        Args:
            tokenizer_name (str): Name of the BERT tokenizer to use
            spacy_model (str): Name of the spaCy model to use
        """
        print("Loading spaCy model...")
        self.nlp = spacy.load(spacy_model)
        
        print("Loading BERT tokenizer...")
        self.tokenizer = BertTokenizer.from_pretrained(tokenizer_name)
        
        # Cache for tokenized sentences to avoid recomputation
        self.tokens_for_sentence = {}
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize the text using BERT tokenizer with caching.
        
        Args:
            text (str): Text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        if text not in self.tokens_for_sentence:
            self.tokens_for_sentence[text] = self.tokenizer.tokenize(text)
        return self.tokens_for_sentence[text]
    
    def get_token_count(self, text: str) -> int:
        """
        Get token count for text with caching.
        
        Args:
            text (str): Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        return len(self.tokenize(text))
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using spaCy's sentence boundary detection.
        
        Args:
            text (str): Text to split into sentences
            
        Returns:
            List[str]: List of sentences
        """
        doc = self.nlp(text)
        sentences = []
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if sentence_text and len(sentence_text) > 10:  # Filter out very short sentences
                sentences.append(sentence_text)
        return sentences
    
    def split_paragraph_improved(self, paragraph: str, max_length: int = 600, min_length: int = 200) -> List[str]:
        """
        Improved paragraph splitting with better load balancing and boundary handling.
        
        Args:
            paragraph (str): The paragraph to split
            max_length (int): Maximum tokens per chunk
            min_length (int): Minimum tokens per chunk (for filtering)
        
        Returns:
            List[str]: List of text chunks, each being a string
        """
        if not paragraph.strip():
            return []
        
        # Split into sentences
        sentences = self.split_into_sentences(paragraph)
        if not sentences:
            return []
        
        # Calculate token counts for each sentence
        sentence_tokens = []
        total_tokens = 0
        
        for sentence in sentences:
            token_count = self.get_token_count(sentence)
            sentence_tokens.append((sentence, token_count))
            total_tokens += token_count
        
        # If the entire paragraph is too short, return as is (unless explicitly filtered)
        if total_tokens < min_length:
            return [paragraph] if total_tokens >= 50 else []  # Very short threshold
        
        # If the paragraph fits in one chunk, return as is
        if total_tokens <= max_length:
            return [paragraph]
        
        # Calculate optimal number of chunks
        num_chunks = max(1, (total_tokens + max_length - 1) // max_length)  # Ceiling division
        target_tokens_per_chunk = total_tokens // num_chunks
        
        chunks = []
        current_chunk_sentences = []
        current_chunk_tokens = 0
        
        for i, (sentence, token_count) in enumerate(sentence_tokens):
            # Check if adding this sentence would exceed reasonable bounds
            projected_tokens = current_chunk_tokens + token_count
            
            # Decision logic for chunk boundaries
            should_start_new_chunk = False
            
            if current_chunk_sentences:  # Not the first sentence in chunk
                # Start new chunk if:
                # 1. We'd exceed max_length, OR
                # 2. We're past target size and have at least min_length tokens, OR
                # 3. We're significantly over target and there are remaining sentences
                remaining_sentences = len(sentence_tokens) - i
                chunks_remaining = num_chunks - len(chunks)
                
                if (projected_tokens > max_length or 
                    (projected_tokens > target_tokens_per_chunk and current_chunk_tokens >= min_length) or
                    (projected_tokens > target_tokens_per_chunk * 1.2 and remaining_sentences > chunks_remaining)):
                    should_start_new_chunk = True
            
            if should_start_new_chunk:
                # Finalize current chunk
                if current_chunk_sentences:
                    chunks.append(' '.join(current_chunk_sentences))
                
                # Start new chunk
                current_chunk_sentences = [sentence]
                current_chunk_tokens = token_count
            else:
                # Add to current chunk
                current_chunk_sentences.append(sentence)
                current_chunk_tokens = projected_tokens
        
        # Add the final chunk
        if current_chunk_sentences:
            chunks.append(' '.join(current_chunk_sentences))
        
        # Post-processing: merge very small chunks with adjacent ones
        chunks = self._merge_small_chunks(chunks, min_length, max_length)
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[str], min_length: int, max_length: int) -> List[str]:
        """
        Merge chunks that are too small with adjacent chunks.
        
        Args:
            chunks (List[str]): List of text chunks
            min_length (int): Minimum length threshold
            max_length (int): Maximum length threshold
            
        Returns:
            List[str]: Merged chunks
        """
        if len(chunks) <= 1:
            return chunks
        
        merged_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            current_tokens = self.get_token_count(current_chunk)
            
            # If chunk is too small, try to merge with next chunk
            if current_tokens < min_length and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                next_tokens = self.get_token_count(next_chunk)
                combined_tokens = current_tokens + next_tokens
                
                # Merge if combined size is reasonable
                if combined_tokens <= max_length * 1.1:  # Allow slight overflow for merging
                    merged_chunks.append(current_chunk + ' ' + next_chunk)
                    i += 2  # Skip next chunk as it's been merged
                    continue
            
            merged_chunks.append(current_chunk)
            i += 1
        
        return merged_chunks
    
    def process_text_improved(self, text: str, max_length: int = 600, min_length: int = 200) -> List[str]:
        """
        Improved text processing with better paragraph handling.
        
        Args:
            text (str): Input text to process
            max_length (int): Maximum tokens per chunk
            min_length (int): Minimum tokens per chunk
        
        Returns:
            List[str]: List of text chunks
        """
        if not text.strip():
            return []
        
        # Split by double newlines for paragraphs, then by single newlines
        paragraphs = []
        
        # First split by double newlines (paragraph breaks)
        double_newline_splits = text.split('\n\n')
        
        for section in double_newline_splits:
            if section.strip():
                # Further split by single newlines within each section
                single_newline_splits = section.split('\n')
                current_paragraph = []
                
                for line in single_newline_splits:
                    line = line.strip()
                    if line:
                        current_paragraph.append(line)
                    else:
                        # Empty line - finalize current paragraph if it exists
                        if current_paragraph:
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                
                # Don't forget the last paragraph
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
        
        # Process each paragraph
        all_chunks = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            paragraph_tokens = self.get_token_count(paragraph)
            
            # Handle very short paragraphs by merging with next
            if paragraph_tokens < min_length // 2 and all_chunks:
                # Try to merge with previous chunk if it won't be too long
                prev_chunk = all_chunks[-1]
                prev_tokens = self.get_token_count(prev_chunk)
                
                if prev_tokens + paragraph_tokens <= max_length:
                    all_chunks[-1] = prev_chunk + ' ' + paragraph
                    continue
            
            # Split the paragraph
            chunks = self.split_paragraph_improved(paragraph, max_length, min_length)
            all_chunks.extend(chunks)
        
        # Final filtering - remove chunks that are still too small
        final_chunks = []
        for chunk in all_chunks:
            token_count = self.get_token_count(chunk)
            if token_count >= 50:  # Absolute minimum threshold
                final_chunks.append(chunk)
        
        return final_chunks
    
    def chunk_text(self, text: str, max_tokens: int = 600, min_tokens: int = 200) -> List[str]:
        """
        Main public method to chunk text into smaller pieces.
        
        Args:
            text (str): The text to chunk
            max_tokens (int): Maximum tokens per chunk
            min_tokens (int): Minimum tokens per chunk
            
        Returns:
            List[str]: List of text chunks
        """
        return self.process_text_improved(text, max_tokens, min_tokens)


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


def clean_text(text):
    """Remove the standard prompt prefix from the text"""
    prefix_to_remove = "You are a reviewer for a research paper. Generate a questionnaire as a numbered list that analyzes any potential ethical considerations with the practices done in the research paper. Here is the research paper."
    
    if text.strip().startswith(prefix_to_remove):
        return text[len(prefix_to_remove):].strip()
    return text


def get_summary_text(file_path, input_dir):
    """Get corresponding summary from 7_output_sum directory"""
    try:
        # Get relative path from input directory
        relative_path = os.path.relpath(file_path, input_dir)
        
        # Construct path to summary file in 7_output_sum
        summary_dir = "7_output_sum"
        summary_path = os.path.join(summary_dir, relative_path)
        
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                return f.read().strip()
        else:
            print(f"Warning: Summary file not found at {summary_path}")
            return "Summary not available for this research paper."
    except Exception as e:
        print(f"Error reading summary file: {str(e)}")
        return "Summary not available for this research paper."


def make_api_request(prompt, model_name):
    """Make API request to Ollama with timeout handling"""
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=80)
    except Timeout:
        return None, "Hard timeout"
    
    # Check if more than 20 seconds have passed
    if time.time() - start_time > 20:
        return None, "Soft timeout"
    
    if response.status_code == 200:
        response_text = response.text
        data = json.loads(response_text)
        return data["response"], None
    else:
        return None, f"HTTP Error {response.status_code}: {response.text}"


def process_file_enhanced(file_path, output_path, model_name, input_dir, verbose=False):
    """Enhanced file processing with chunking and consolidation"""
    print(f"Currently on: {file_path}")
    
    try:
        # Read and clean the file
        with open(file_path, 'r', encoding='utf-8') as file:
            original_text = file.read()
        
        cleaned_text = clean_text(original_text)
        
        if not cleaned_text.strip():
            print(f"Warning: No content after cleaning for {file_path}")
            return False
        
        # Initialize chunker
        chunker = TextChunker()
        
        # Chunk the text
        chunks = chunker.chunk_text(cleaned_text, max_tokens=600, min_tokens=200)
        
        if not chunks:
            print(f"Warning: No chunks generated for {file_path}")
            return False
        
        print(f"Generated {len(chunks)} chunks for {file_path}")
        
        # Prepare verbose logging
        verbose_content = []
        if verbose:
            verbose_content.append(f"=== PROCESSING FILE: {file_path} ===\n")
            verbose_content.append(f"Original text length: {len(original_text)} characters")
            verbose_content.append(f"Cleaned text length: {len(cleaned_text)} characters")
            verbose_content.append(f"Number of chunks: {len(chunks)}\n")
        
        # Process each chunk
        chunk_responses = []
        chunk_prefix = "This is a segment from a research paper. Give 1-2 ethical questions (single line) that analyzes any potential ethical considerations with the practices done in the research paper.\n\n"
        
        for i, chunk in enumerate(chunks):
            chunk_prompt = chunk_prefix + chunk
            
            if verbose:
                verbose_content.append(f"\n--- CHUNK {i+1} ---")
                verbose_content.append(f"Chunk content ({chunker.get_token_count(chunk)} tokens):")
                verbose_content.append(chunk)
                verbose_content.append(f"\nChunk prompt:")
                verbose_content.append(chunk_prompt)
            
            # Make API request
            response, error = make_api_request(chunk_prompt, model_name)
            
            if error:
                print(f"Error processing chunk {i+1} of {file_path}: {error}")
                log_exception(file_path, model_name, f"Chunk {i+1} - {error}")
                if verbose:
                    verbose_content.append(f"\nChunk {i+1} response: ERROR - {error}")
                continue
            
            chunk_responses.append(response)
            if verbose:
                verbose_content.append(f"\nChunk {i+1} response:")
                verbose_content.append(response)
        
        if not chunk_responses:
            print(f"No successful chunk responses for {file_path}")
            return False
        
        # Get summary
        summary = get_summary_text(file_path, input_dir)
        
        # Create consolidation prompt
        all_questions = "\n".join(chunk_responses)
        consolidation_prompt = f"""Here is summary of research paper:
{summary}

And here are the relevant ethical questions for this paper:
{all_questions}

From this give final 7-8 ethical questions as a numbered list 
1- 
2- 
3- 
....
Remove redundant questions and choose the questions you best see fit if things are exceeding."""
        
        if verbose:
            verbose_content.append(f"\n\n=== CONSOLIDATION PHASE ===")
            verbose_content.append(f"Summary used:")
            verbose_content.append(summary)
            verbose_content.append(f"\nAll chunk questions combined:")
            verbose_content.append(all_questions)
            verbose_content.append(f"\nFinal consolidation prompt:")
            verbose_content.append(consolidation_prompt)
        
        # Make consolidation request
        final_response, error = make_api_request(consolidation_prompt, model_name)
        
        if error:
            print(f"Error in consolidation for {file_path}: {error}")
            log_exception(file_path, model_name, f"Consolidation - {error}")
            return False
        
        if verbose:
            verbose_content.append(f"\nFinal consolidated response:")
            verbose_content.append(final_response)
            verbose_content.append(f"\n=== END OF PROCESSING ===")
        
        # Save main output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(final_response)
        
        # Save verbose output if requested
        if verbose:
            verbose_path = output_path.replace('.txt', '_verbose.txt')
            with open(verbose_path, 'w', encoding='utf-8') as verbose_file:
                verbose_file.write('\n'.join(verbose_content))
        
        print(f"Successfully processed: {file_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        log_exception(file_path, model_name, f"Error: {str(e)}")
        return False


def process_directory(input_dir, output_dir, model_name, verbose=False):
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
                
                success = process_file_enhanced(input_path, output_path, model_name, input_dir, verbose)
                if success:
                    processed_files[relative_path] = file_hash
                    save_processed_files(processed_files_path, processed_files)


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python3 ollama.py <input_directory> <output_directory> <model_name> [-v]")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    model_name = sys.argv[3]
    verbose = len(sys.argv) == 5 and sys.argv[4] == '-v'
    
    if verbose:
        print("Verbose mode enabled - detailed logs will be saved")
    
    # Verify that 7_output_sum directory exists
    if not os.path.exists("7_output_sum"):
        print("Warning: 7_output_sum directory not found. Summary integration may not work properly.")
    
    print("Initializing text chunker...")
    # This will load the models once at startup
    try:
        test_chunker = TextChunker()
        print("Text chunker initialized successfully")
    except Exception as e:
        print(f"Error initializing text chunker: {e}")
        print("Please ensure spacy and transformers are installed:")
        print("pip install spacy transformers")
        print("python -m spacy download en_core_web_sm")
        sys.exit(1)
    
    process_directory(input_directory, output_directory, model_name, verbose)