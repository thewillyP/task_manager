#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=4G
#SBATCH --time=06:00:00
#SBATCH --job-name=task_manager
#SBATCH --error=/vast/wlp9800/logs/%x-%A-%a.err
#SBATCH --output=/vast/wlp9800/logs/%x-%A-%a.out
#SBATCH --gres=gpu:0
#SBATCH --cpus-per-task=2

singularity run --nv --containall --cleanenv --no-home \
  --bind /home/$USER/.ssh \
  --bind /scratch/$USER/task_manager:/app \
  docker://thewillyp/task_manager:main-1