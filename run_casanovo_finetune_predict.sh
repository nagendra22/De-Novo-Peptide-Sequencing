#!/bin/bash

# Prereq:
#   - Docker image tagged `casanovo` available locally.
#   - bin/casanovo/casanovo_v5_0_0_v5_0_0.ckpt extracted from the
#     image's /root/.cache/casanovo/ directory.
#   - finetuned checkpoint model_finetune/casanovo/epoch=9-step=310.ckpt

CKPT="epoch=9-step=310.ckpt"
samples_ecoli=(Ecoli_EV_2)
samples_wastewater=(wastewater_Sample1_1 wastewater_Sample1_2 wastewater_Sample2_1 wastewater_Sample2_2)

mkdir -p result_finetune/casanovo/ecoli result_finetune/casanovo/wastewater
mkdir -p result_finetune_mgf/casanovo/ecoli result_finetune_mgf/casanovo/wastewater
mkdir -p result_finetune_mgf_decoy/casanovo/ecoli result_finetune_mgf_decoy/casanovo/wastewater

# mzML
for sample in "${samples_ecoli[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data:/data \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune:/result \
    casanovo casanovo sequence /data/ecoli/${sample}.mzML \
    --model /ckpt/${CKPT} \
    --output_dir /result/casanovo/ecoli \
    --output_root ${sample}
done

for sample in "${samples_wastewater[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data:/data \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune:/result \
    casanovo casanovo sequence /data/wastewater/${sample}.mzML \
    --model /ckpt/${CKPT} \
    --output_dir /result/casanovo/wastewater \
    --output_root ${sample}
done

# MGF
for sample in "${samples_ecoli[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf:/data \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune_mgf:/result \
    casanovo casanovo sequence /data/ecoli/${sample}.mgf \
    --model /ckpt/${CKPT} \
    --output_dir /result/casanovo/ecoli \
    --output_root ${sample}
done

for sample in "${samples_wastewater[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf:/data \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune_mgf:/result \
    casanovo casanovo sequence /data/wastewater/${sample}.mgf \
    --model /ckpt/${CKPT} \
    --output_dir /result/casanovo/wastewater \
    --output_root ${sample}
done

# Decoy
for sample in "${samples_ecoli[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf_decoy:/data \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune_mgf_decoy:/result \
    casanovo casanovo sequence /data/ecoli/${sample}.decoy.mgf \
    --model /ckpt/${CKPT} \
    --output_dir /result/casanovo/ecoli \
    --output_root ${sample}.decoy
done

for sample in "${samples_wastewater[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf_decoy:/data \
    -v $(pwd)/model_finetune/casanovo:/ckpt:ro \
    -v $(pwd)/result_finetune_mgf_decoy:/result \
    casanovo casanovo sequence /data/wastewater/${sample}.decoy.mgf \
    --model /ckpt/${CKPT} \
    --output_dir /result/casanovo/wastewater \
    --output_root ${sample}.decoy
done

sudo chown -R "$(id -u):$(id -g)" result_finetune result_finetune_mgf result_finetune_mgf_decoy
