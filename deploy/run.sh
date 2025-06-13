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



OVERLAY_TYPE="overlay-25GB-500K.ext3"
cp -rp /scratch/work/public/overlay-fs-ext3/${OVERLAY_TYPE}.gz "/scratch/${USER}/task_manager.ext3.gz"
gunzip -f "/scratch/${USER}/task_manager.ext3.gz"

singularity build --force /scratch/${USER}/images/task_manager.sif docker://thewillyp/task_manager:latest

singularity run --containall --cleanenv --no-home \
  --overlay /scratch/${USER}/task_manager.ext3:rw \
  --bind /home/$USER/.ssh \
  --bind /scratch/$USER/task_manager:/app \
  /scratch/${USER}/images/task_manager.sif