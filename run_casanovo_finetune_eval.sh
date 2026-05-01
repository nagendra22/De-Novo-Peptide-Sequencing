#!/bin/bash

# Prereq:
#   - Docker image tagged `casanovo` available locally.
#   - bin/casanovo/casanovo_v5_0_0_v5_0_0.ckpt extracted from the
#     image's /root/.cache/casanovo/ directory.

CKPT="epoch=9-step=310.ckpt"

sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf_annotated:/data_in:ro \
    -v $(pwd)/bin/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune/casanovo:/out \
    casanovo casanovo sequence --evaluate \
      --model /ckpt/casanovo_v5_0_0_v5_0_0.ckpt \
      --output_dir /out --output_root Ecoli_EV_2 \
      /data_in/ecoli/Ecoli_EV_2.casanovo.annotated.mgf

sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf_annotated:/data_in:ro \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune/casanovo:/out \
    casanovo casanovo sequence --evaluate \
      --model "/ckpt/${CKPT}" \
      --output_dir /out --output_root Ecoli_EV_2.finetuned \
      /data_in/ecoli/Ecoli_EV_2.casanovo.annotated.mgf

# Files written by the container are root-owned on the host. Restore ownership.
sudo chown -R "$(id -u):$(id -g)" result_finetune
