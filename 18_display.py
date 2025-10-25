import json
import pandas as pd

# Load your JSON file
with open("18_TIGERScore-main/example_result.json", "r") as f:
    data = json.load(f)

# Initialize results dictionary
scores = {}

# Loop through entries
for entry in data:
    for cand in entry.get("candidates", []):
        model = cand.get("model")
        if model not in scores:
            scores[model] = {"Completeness":0, "Clarity":0, "Relevance":0,
                             "Objectivity":0, "Coherence":0, "Accuracy":0, "Total":0}
        
        for resp in cand.get("responses", []):
            if isinstance(resp, dict) and "errors" in resp:
                for _, err in resp["errors"].items():
                    aspect = err.get("error_aspect", "")
                    penalty = err.get("score_reduction", 0)
                    if aspect in scores[model]:
                        scores[model][aspect] += penalty
                        scores[model]["Total"] += penalty

# Convert to DataFrame
df = pd.DataFrame(scores).T  # Models as rows
df = df[["Completeness","Clarity","Relevance","Objectivity","Coherence","Accuracy","Total"]]

# Print table nicely in terminal
print(df.to_string())
