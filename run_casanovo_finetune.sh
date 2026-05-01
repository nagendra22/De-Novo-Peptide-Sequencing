#!/bin/bash

# Prereq:
#   - Docker image tagged `casanovo` available locally.
#   - bin/casanovo/casanovo_v5_0_0_v5_0_0.ckpt extracted from the
#     image's /root/.cache/casanovo/ directory.

sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v "$(pwd)/data_mgf_annotated:/data_in:ro" \
    -v "$(pwd)/bin/casanovo:/ckpt:ro" \
    -v "$(pwd)/config/finetune:/config:ro" \
    -v "$(pwd)/model_finetune/casanovo:/out" \
    casanovo casanovo train \
        --validation_peak_path /data_in/ecoli/Ecoli_EV_1.casanovo.val.mgf \
        --model /ckpt/casanovo_v5_0_0_v5_0_0.ckpt \
        --config /config/casanovo.yaml \
        --output_dir /out \
        /data_in/ecoli/Ecoli_EV_1.casanovo.train.mgf \
    2>&1 | tee "${OUT_DIR}train.log"

# Files written by the container are root-owned on the host. Restore ownership.
sudo chown -R "$(id -u):$(id -g)" model_finetune
