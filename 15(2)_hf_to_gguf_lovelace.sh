#!/bin/bash
#SBATCH -n 27
#SBATCH -A kcis
#SBATCH --gres=gpu:1
#SBATCH --mincpus=7
#SBATCH --mem-per-cpu=4000M
#SBATCH --output=op_file.txt
#SBATCH --mail-type=END,FAIL
#SBATCH -w gnode120
#SBATCH --partition=lovelace
#SBATCH --time=4-00:00:00
#SBATCH --mail-user= @research. .ac.in

#one time step 
#https://www.geeksforgeeks.org/how-to-convert-any-huggingface-model-to-gguf-file-format/
#conda create --name conversion python=3.10
#git clone https://github.com/ggerganov/llama.cpp
#cd llama.cpp
#pip install -r requirements.txt

source activate conversion
cd my_code

mkdir -p /scratch/ik #this is pretty important otherwise ollama might not run (also , ollama runs on particular node for example on node10 but did not ran on node21)
process_model() {
    local model_name=$1
    local model_dir="/scratch/ik/$model_name"
    local gguf_file="/scratch/ik/$model_name.gguf"
    if [ ! -d "$model_dir" ]; then
        echo "Copying $model_name from ada..."
        scp -o StrictHostKeyChecking=no -r ada:/share1/ /$model_name /scratch/ik

    else
        echo "$model_name directory already exists in /scratch/ik, skipping copy."
    fi
    if [ ! -f "$gguf_file" ]; then
        echo "Converting $model_name to GGUF..."
        python /home2/ /my_code/llama_new/llama.cpp/convert_hf_to_gguf.py "$model_dir" --outfile "$gguf_file" --outtype f16
    else
        echo "$model_name.gguf already exists in /scratch/ik, skipping conversion."
    fi
}
process_model "gemma"
process_model "llamabase"
process_model "llamainstruct"
process_model "mistral"
process_model "phi"


module load u22/singularity-ce/4.2.2

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
#singularity shell --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif
#you might need to run a ollama serve command the above shell command
#gemma , you need to download tokenizer.model from official and place it (already done)
singularity exec instance://ollama_instance ollama create gemma -f /home2/ /my_code/15_Modelfile_gemma
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/gemma_output gemma
singularity exec instance://ollama_instance ollama rm gemma
singularity instance stop ollama_instance

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create llamabase -f /home2/ /my_code/15_Modelfile_llamabase
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/llamabase_output llamabase
singularity exec instance://ollama_instance ollama rm llamabase
singularity instance stop ollama_instance


singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create llamainstruct -f /home2/ /my_code/15_Modelfile_llamainstruct
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/llamainstruct_output llamainstruct
singularity exec instance://ollama_instance ollama rm llamainstruct
singularity instance stop ollama_instance



singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create mistral -f /home2/ /my_code/15_Modelfile_mistral
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/mistral_output mistral
singularity exec instance://ollama_instance ollama rm mistral
singularity instance stop ollama_instance

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create phi -f /home2/ /my_code/15_Modelfile_phi
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/phi_output phi
singularity exec instance://ollama_instance ollama rm phi
singularity instance stop ollama_instance



python3 "16_rougefinal.py"