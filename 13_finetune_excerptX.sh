#!/bin/bash
#SBATCH -n 27
#SBATCH -A kcis
#SBATCH --gres=gpu:1
#SBATCH --mincpus=4
#SBATCH --mem-per-cpu=4000M
#SBATCH --output=op_file.txt
#SBATCH --mail-type=END,FAIL
#SBATCH -w gnode121
#SBATCH --partition=lovelace
#SBATCH --time=4-00:00:00
#SBATCH --mail-user= @research. .ac.in

source activate unsloth

# Set the environment variable
export HF_TOKEN=""

rm -rf .cache
python3 /home2/ /my_code/13_gemmaexcerptX.py

rm -rf .cache
python3 /home2/ /my_code/13_llamaexcerptX.py

rm -rf .cache
python3 /home2/ /my_code/13_mistralexcerptX.py

