#!/bin/bash
#SBATCH -n 27
#SBATCH -A kcis
#SBATCH --gres=gpu:1
#SBATCH --mincpus=7
#SBATCH --mem-per-cpu=4000M
#SBATCH --output=op_file.txt
#SBATCH --mail-type=END,FAIL
#SBATCH -w gnode121
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
module load u22/singularity-ce/4.2.2

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
#singularity shell --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif
#gemma , you need to download tokenizer.model from official and place it (already done)
singularity exec instance://ollama_instance ollama create gemma27 -f /home2/ /my_code/15_Modelfile_gemma27X
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/gemma27_outputX gemma27
singularity exec instance://ollama_instance ollama rm gemma27
singularity instance stop ollama_instance

singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance
singularity exec instance://ollama_instance ollama create  -f /home2/ /my_code/15_Modelfile_llama70X
singularity exec instance://ollama_instance python3 /home2/ /my_code/15\(3\)_ollama.py /home2/ /my_code/7_output /home2/ /my_code/llama70_outputX llama70
singularity exec instance://ollama_instance ollama rm llama70
singularity instance stop ollama_instance

