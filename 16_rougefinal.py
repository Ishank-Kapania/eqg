import os
import sys
from typing import Dict, Set
import pandas as pd
from tqdm import tqdm
from rouge import Rouge
from bert_score import score
import torch

def is_file_empty(filepath: str) -> bool:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return len(content.strip()) == 0
    except Exception as e:
        print(f"Error checking file {filepath}: {e}")
        return True

def get_files_recursive(folder: str) -> Dict[str, str]:
    file_dict = {}
    for root, _, files in os.walk(folder):
        for file in files:
            file_dict[file] = os.path.join(root, file)
    return file_dict

def find_common_files(folders: Dict[str, str]) -> Set[str]:
    file_sets = []
    folder_files = {}

    for name, folder in folders.items():
        if os.path.exists(folder):
            files = get_files_recursive(folder)
            folder_files[name] = files
            file_sets.append(set(files.keys()))
        else:
            print(f"Warning: Folder {folder} does not exist")
            file_sets.append(set())
            folder_files[name] = {}

    common_files = set.intersection(*file_sets) if file_sets else set()
    print(f"Found {len(common_files)} common files before filtering.")

    valid_files = set()
    for filename in common_files:
        if any(is_file_empty(folder_files[name].get(filename, "")) for name in folders):
            continue
        valid_files.add(filename)

    print(f"{len(valid_files)} files remain after filtering out empty ones.")
    return valid_files

def calculate_scores(text1: str, text2: str) -> Dict[str, float]:
    rouge = Rouge()
    rouge_scores = rouge.get_scores(text1, text2)[0]

    P, R, F1 = score([text1], [text2], lang="en", device="cuda" if torch.cuda.is_available() else "cpu")
    bert_score = F1.mean().item()

    return {
        "rouge-1": rouge_scores["rouge-1"]["f"],
        "rouge-2": rouge_scores["rouge-2"]["f"],
        "rouge-l": rouge_scores["rouge-l"]["f"],
        "bert-score": bert_score
    }

def evaluate_model(reference_folder: str, model_folder: str, common_files: Set[str]) -> pd.DataFrame:
    files1 = get_files_recursive(reference_folder)
    files2 = get_files_recursive(model_folder)

    results = []

    for filename in tqdm(common_files, desc=f"Evaluating {model_folder}"):
        path1 = files1[filename]
        path2 = files2[filename]

        try:
            with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
                text1 = f1.read()
                text2 = f2.read()

            scores = calculate_scores(text1, text2)
            result = {
                "filename": filename,
                **scores
            }
            results.append(result)
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return pd.DataFrame(results)

def compare_models(model_dfs: Dict[str, pd.DataFrame]) -> None:
    model_averages = {
        model: df[['rouge-1', 'rouge-2', 'rouge-l', 'bert-score']].mean()
        for model, df in model_dfs.items() if not df.empty
    }

    if not model_averages:
        print("No data to compare.")
        return

    scores_df = pd.DataFrame(model_averages)
    best_models = scores_df.idxmax(axis=1)
    overall_best = best_models.mode().values[0]

    print("\nAverage Scores:")
    print(scores_df.round(4))

    print("\nBest Model Per Metric:")
    print(best_models)

    print(f"\nOverall Best Model: {overall_best}")

    print("\nDetailed Comparison:")
    for metric in scores_df.index:
        best_model = best_models[metric]
        best_score = scores_df.loc[metric, best_model]
        print(f"{metric}:")
        print(f"  Best: {best_model} ({best_score:.4f})")
        for model in scores_df.columns:
            if model != best_model:
                score_ = scores_df.loc[metric, model]
                diff = best_score - score_
                print(f"  {model}: {score_:.4f} (Diff: {diff:.4f})")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python evaluate_models.py <model1> <model2> ... <output_file.txt>")
        sys.exit(1)

    # Last argument is output file name
    output_file = sys.argv[-1]
    if not output_file.endswith(".txt"):
        print("Error: Last argument must be the output filename ending with .txt")
        sys.exit(1)

    # All other arguments are model names
    model_names = sys.argv[1:-1]

    # Redirect stdout to file
    sys.stdout = open(output_file, "w", encoding="utf-8")

    reference_folder = "8_output"
    model_folders = {name: f"{name}_output" for name in model_names}
    folders = {"reference": reference_folder, **model_folders}

    common_files = find_common_files(folders)
    if not common_files:
        print("No common non-empty files found.")
        sys.exit(1)

    model_results = {}
    for model, folder in model_folders.items():
        if not os.path.exists(folder):
            #print(f"Skipping {model}: folder '{folder}' does not exist.")
            continue
        df = evaluate_model(reference_folder, folder, common_files)
        model_results[model] = df

    compare_models(model_results)
#python evaluate_models.py llamabase gemma phi llamainstruct mistral 16_small.txt

#execute a shell command that removes X at last from 

#llama70_outputX , gemma27_outputX , gemma3_outputX , phi4_outputX 
#llamadpr_outputX,gemmadpr_outputX , mistraldpr_outputX 
#mistralexcerpt_outputX,llamaexcerpt_outputX,gemmaexcerpt_outputX

#python evaluate_models.py gemma3 phi4 llama70 gemma27 16_large.txt
#python evaluate_models.py mistraldpr llamadpr gemmadpr 16_dpr.txt 
#python evaluate_models.py mistralexcerpt llamaexcerpt gemmaexcerpt 16_sum.txt

#shell command to put X back