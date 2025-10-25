#!/bin/bash
#SBATCH -n 10
#SBATCH --gres=gpu:3
#SBATCH --mincpus=29
#SBATCH --mem-per-cpu=2G
#SBATCH --output=op_file.txt
#SBATCH --mail-type=END,FAIL
#SBATCH --qos=medium
#SBATCH --nodelist=gnode021
#SBATCH --time=4-00:00:00

module load u22/singularity-ce/4.2.2

# Start Singularity instance
mkdir /scratch/ik #this is really important , otherwise their will be a silent error even if you re-execute the below singularity instance command
singularity instance start --nv --bind /scratch/ik:/scratch/ik /home2/ /ollama.sif ollama_instance

# Run commands inside the Singularity instance
singularity exec instance://ollama_instance ollama create llama_70k -f /home2/ /my_code/10_Modelfile
singularity exec instance://ollama_instance ollama pull llama_70k
singularity exec instance://ollama_instance python3 /scratch/ik/10_ollama.py

# Stop Singularity instance
singularity instance stop ollama_instance
