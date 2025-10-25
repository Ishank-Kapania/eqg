import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertTokenizer
import spacy
import torch
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class EthicalQuestionMatcher:
    def __init__(self):
        """Initialize the matcher with required models and configurations."""
        # Set up device
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Load models
        print("Loading SBERT model...")
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.sbert_model.to(self.device)
        
        print("Loading spaCy model...")
        self.nlp = spacy.load("en_core_web_sm")
        
        print("Loading BERT tokenizer...")
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        
        # Cache for tokenized sentences to avoid recomputation
        self.tokens_for_sentence = {}
        
        # Fixed instruction text
        self.instruction = "You are a reviewer for a research paper. Generate 1–2 questions for this specific paragraph that analyze any potential ethical considerations related to the practices described in this segment."
    
    def tokenize(self, text):
        """Tokenize the text using BERT tokenizer with caching."""
        if text not in self.tokens_for_sentence:
            self.tokens_for_sentence[text] = self.tokenizer.tokenize(text)
        return self.tokens_for_sentence[text]
    
    def get_token_count(self, text):
        """Get token count for text with caching."""
        return len(self.tokenize(text))
    
    def split_into_sentences(self, text):
        """Split text into sentences using spaCy's sentence boundary detection."""
        doc = self.nlp(text)
        sentences = []
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if sentence_text and len(sentence_text) > 10:  # Filter out very short sentences
                sentences.append(sentence_text)
        return sentences
    
    def split_paragraph_improved(self, paragraph, max_length=600, min_length=200):
        """
        Improved paragraph splitting with better load balancing and boundary handling.
        
        Args:
            paragraph (str): The paragraph to split
            max_length (int): Maximum tokens per chunk
            min_length (int): Minimum tokens per chunk (for filtering)
        
        Returns:
            list: List of text chunks, each being a string
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
    
    def _merge_small_chunks(self, chunks, min_length, max_length):
        """Merge chunks that are too small with adjacent chunks."""
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
    
    def process_text_improved(self, text, max_length=600, min_length=200):
        """
        Improved text processing with better paragraph handling.
        
        Args:
            text (str): Input text to process
            max_length (int): Maximum tokens per chunk
            min_length (int): Minimum tokens per chunk
        
        Returns:
            list: List of text chunks
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
    
    def encode_texts(self, texts):
        """Encode texts using SBERT model."""
        if not texts:
            return np.array([])
        return self.sbert_model.encode(texts, convert_to_tensor=False)
    
    def find_top_3_passages_for_question(self, question, passages):
        """
        Find the top 3 most semantically similar passages for a given question.
        
        Args:
            question (str): The ethical question
            passages (list): List of text passages (strings)
            
        Returns:
            dict: Dictionary containing top 3 passages and their similarities
        """
        if not passages:
            return {}
        
        # Remove duplicates while preserving order
        unique_passages = []
        seen = set()
        for passage in passages:
            if passage not in seen:
                unique_passages.append(passage)
                seen.add(passage)
        
        if not unique_passages:
            return {}
        
        # Encode question and passages
        question_embedding = self.encode_texts([question])
        passage_embeddings = self.encode_texts(unique_passages)
        
        # Calculate similarities
        similarities = cosine_similarity(question_embedding, passage_embeddings)[0]
        
        # Get top 3 indices
        top_indices = np.argsort(similarities)[::-1][:3]
        
        # Prepare results
        result = {}
        rank_names = ['most_relevant', 'second_most_relevant', 'third_most_relevant']
        
        for i, idx in enumerate(top_indices):
            if i < len(rank_names) and similarities[idx] > 0:  # Only include positive similarities
                result[rank_names[i]] = {
                    'passage': unique_passages[idx],
                    'similarity': float(similarities[idx])
                }
        
        return result
    
    def read_file_content(self, filepath):
        """Read and return file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return ""
    
    def read_questions_from_file(self, filepath):
        """Read ethical questions from file, one per line."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f.readlines() if line.strip()]
            return questions
        except Exception as e:
            print(f"Error reading questions from {filepath}: {e}")
            return []
    
    def process_single_file(self, paper_path, questions_path):
        """
        Process a single pair of paper and questions files.
        
        Args:
            paper_path (str): Path to the research paper file
            questions_path (str): Path to the ethical questions file
            
        Returns:
            list: List of dictionaries for parquet rows
        """
        # Read paper content and process into passages
        paper_content = self.read_file_content(paper_path)
        if not paper_content:
            print(f"Warning: Empty or unreadable paper file: {paper_path}")
            return []
        
        # Use improved text processing
        passages = self.process_text_improved(paper_content, max_length=600, min_length=200)
        if not passages:
            print(f"Warning: No passages found in paper: {paper_path}")
            return []
        
        print(f"Generated {len(passages)} passages from {os.path.basename(paper_path)}")
        
        # Read ethical questions
        questions = self.read_questions_from_file(questions_path)
        if not questions:
            print(f"Warning: No questions found in: {questions_path}")
            return []
        
        rows = []
        print(f"Processing {len(questions)} questions from {os.path.basename(questions_path)}")
        
        for question in tqdm(questions, desc="Processing questions", leave=False):
            # Find top 3 most similar passages
            top_passages = self.find_top_3_passages_for_question(question, passages)
            
            # Create rows for each of the top 3 passages
            for rank_key, passage_info in top_passages.items():
                rows.append({
                    'instruction': self.instruction,
                    'input': passage_info['passage'],
                    'output': question
                })
        
        return rows
    
    def get_matching_files(self, dpr_dir, numbered_dir):
        """
        Get matching file pairs between the two directories.
        
        Returns:
            list: List of tuples (paper_path, questions_path, relative_path)
        """
        matching_files = []
        
        for root, dirs, files in os.walk(numbered_dir):
            for file in files:
                if file.endswith('.txt'):
                    # Get relative path from numbered_dir
                    rel_path = os.path.relpath(os.path.join(root, file), numbered_dir)
                    
                    # Construct corresponding paths
                    questions_path = os.path.join(numbered_dir, rel_path)
                    paper_path = os.path.join(dpr_dir, rel_path)
                    
                    # Check if both files exist
                    if os.path.exists(paper_path) and os.path.exists(questions_path):
                        matching_files.append((paper_path, questions_path, rel_path))
                    else:
                        print(f"Warning: Missing matching file for {rel_path}")
                        if not os.path.exists(paper_path):
                            print(f"  Missing paper: {paper_path}")
                        if not os.path.exists(questions_path):
                            print(f"  Missing questions: {questions_path}")
        
        return matching_files
    
    def process_directories(self, dpr_dir, numbered_dir, output_file):
        """
        Process all matching files in the directories and create parquet output.
        
        Args:
            dpr_dir (str): Path to 5_output_dpr directory
            numbered_dir (str): Path to resultant_numbered directory
            output_file (str): Path for output parquet file
        """
        print(f"Scanning directories for matching files...")
        print(f"DPR directory: {dpr_dir}")
        print(f"Numbered directory: {numbered_dir}")
        
        # Get all matching file pairs
        matching_files = self.get_matching_files(dpr_dir, numbered_dir)
        
        if not matching_files:
            print("No matching files found!")
            return
        
        print(f"Found {len(matching_files)} matching file pairs")
        
        all_rows = []
        
        # Process each file pair
        for paper_path, questions_path, rel_path in tqdm(matching_files, desc="Processing files"):
            print(f"\nProcessing: {rel_path}")
            rows = self.process_single_file(paper_path, questions_path)
            all_rows.extend(rows)
            print(f"Generated {len(rows)} rows")
        
        # Create DataFrame and save as parquet
        if all_rows:
            df = pd.DataFrame(all_rows)
            print(f"\nTotal rows generated: {len(df)}")
            print(f"Saving to: {output_file}")
            df.to_parquet(output_file, index=False)
            print("✅ Processing complete!")
            
            # Display sample of the output
            print("\nSample of generated data:")
            print(df.head(3).to_string())
            
            # Display statistics
            print(f"\nDataset statistics:")
            print(f"- Total rows: {len(df)}")
            print(f"- Unique questions: {df['output'].nunique()}")
            print(f"- Unique inputs: {df['input'].nunique()}")
        else:
            print("No data generated!")

def main():
    """Main function to run the processing."""
    # Directory paths
    dpr_dir = "5_output_dpr"
    numbered_dir = "resultant_numbered"
    output_file = "/home2/ /my_code/dpr.parquet"
    
    # Check if directories exist
    if not os.path.exists(dpr_dir):
        print(f"Error: Directory {dpr_dir} does not exist!")
        return
    
    if not os.path.exists(numbered_dir):
        print(f"Error: Directory {numbered_dir} does not exist!")
        return
    
    # Initialize matcher and process
    matcher = EthicalQuestionMatcher()
    matcher.process_directories(dpr_dir, numbered_dir, output_file)

if __name__ == "__main__":
    main()