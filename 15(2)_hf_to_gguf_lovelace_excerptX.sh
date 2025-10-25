#!/bin/bash
#SBATCH -n 27
#SBATCH -A kcis
#SBATCH --gres=gpu:1
#SBATCH --mincpus=7
#SBATCH --mem-per-cpu=4000M
#SBATCH --output=op_file.txt
#SBATCH --mail-type=END,FAIL
#SBATCH -w gnode119
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

process_model "llamaexcerpt"
process_model "gemmaexcerpt"
process_model "mistralexcerpt"



module load u22/singularity-ce/4.2.2

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
#singularity shell --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif
#gemma , you need to download tokenizer.model from official and place it (already done)
singularity exec instance://ollama_instance ollama create gemmaexcerpt -f /home2/ /my_code/15_Modelfile_gemmaexcerptX
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output_excerpt /home2/ /my_code/gemmaexcerpt_outputX gemmaexcerpt
singularity exec instance://ollama_instance ollama rm gemmaexcerpt
singularity instance stop ollama_instance

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create  -f /home2/ /my_code/15_Modelfile_mistralexcerptX
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output_excerpt /home2/ /my_code/mistralexcerpt_outputX mistralexcerpt
singularity exec instance://ollama_instance ollama rm mistralexcerpt
singularity instance stop ollama_instance

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create  -f /home2/ /my_code/15_Modelfile_llamaexcerptX
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output_excerpt /home2/ /my_code/llamaexcerpt_outputX llamaexcerpt
singularity exec instance://ollama_instance ollama rm llamaexcerpt
singularity instance stop ollama_instance
