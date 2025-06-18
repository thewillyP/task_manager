#!/bin/bash
set -e
ACTION=$1
SIF_DIR=$2
SIF_PATH=$3
DOCKER_URL=$4
OVERLAY_SIZE=$5
IMAGE=$6
BUILD_CPUS=$7
BUILD_MEMORY=$8
BUILD_TIME=$9
LOG_DIR=${10}

if [ "$ACTION" = "check" ]; then
    [ -f "$SIF_PATH" ] && echo "EXISTS" || echo "NOT_EXISTS"
else
    sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=build_${IMAGE}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=${BUILD_CPUS}
#SBATCH --mem=${BUILD_MEMORY}
#SBATCH --time=${BUILD_TIME}
#SBATCH --output=${LOG_DIR}/build_${IMAGE}-%j.out
#SBATCH --error=${LOG_DIR}/build_${IMAGE}-%j.err

mkdir -p ${SIF_DIR}
singularity build ${SIF_PATH} ${DOCKER_URL}
singularity overlay create --size ${OVERLAY_SIZE} ${SIF_PATH}
EOF
fi