#!/bin/bash
set -e
IMAGE=$1
JOBS_TO_SUBMIT=$2
DEPLOY_CPUS=$3
DEPLOY_GPUS=$4
DEPLOY_MEMORY=$5
DEPLOY_TIME=$6
LOG_DIR=$7
SIF_PATH=$8
SWEEP_ID=$9
BUILD_ARCHETYPE=${10}
TASK_ARCHETYPE=${11}
WANDB_API_KEY=${12}
SWEEP_HOST=${13}
SWEEP_PORT=${14}
BIND_MAPPINGS=${15}
BUILD_JOB_ID=${16}

sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=deploy_${IMAGE}
#SBATCH --array=1-${JOBS_TO_SUBMIT}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${DEPLOY_CPUS}
#SBATCH --gpus=${DEPLOY_GPUS}
#SBATCH --mem=${DEPLOY_MEMORY}
#SBATCH --time=${DEPLOY_TIME}
#SBATCH --output=${LOG_DIR}/deploy_${IMAGE}-%A_%a.out
#SBATCH --error=${LOG_DIR}/deploy_${IMAGE}-%A_%a.err
#SBATCH --dependency=afterok:${BUILD_JOB_ID}

singularity run --nv --containall --cleanenv --writable-tmpfs \
  --env SWEEP_ID=${SWEEP_ID} \
  --env BUILD_ARCHETYPE='${BUILD_ARCHETYPE}' \
  --env TASK_ARCHETYPE='${TASK_ARCHETYPE}' \
  --env WANDB_API_KEY=${WANDB_API_KEY} \
  --env SWEEP_HOST=${SWEEP_HOST} \
  --env SWEEP_PORT=${SWEEP_PORT} \
  ${BIND_MAPPINGS:+"--bind ${BIND_MAPPINGS}"} \
  ${SIF_PATH}
EOF