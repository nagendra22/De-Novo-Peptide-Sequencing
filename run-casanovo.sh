#!/bin/bash

samples_ecoli=(Ecoli_EV_1 Ecoli_EV_2)
samples_wastewater=(wastewater_Sample1_1 wastewater_Sample1_2 wastewater_Sample2_1 wastewater_Sample2_2)

# mzML
for sample in "${samples_ecoli[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data:/data \
    -v $(pwd)/result:/result \
    casanovo casanovo sequence /data/ecoli/${sample}.mzML \
    --output_dir /result/casanovo/ecoli \
    --output_root ${sample}
done

for sample in "${samples_wastewater[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data:/data \
    -v $(pwd)/result:/result \
    casanovo casanovo sequence /data/wastewater/${sample}.mzML \
    --output_dir /result/casanovo/wastewater \
    --output_root ${sample}
done

# MGF
for sample in "${samples_ecoli[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf:/data \
    -v $(pwd)/result_mgf:/result \
    casanovo casanovo sequence /data/ecoli/${sample}.mgf \
    --output_dir /result/casanovo/ecoli \
    --output_root ${sample}
done

for sample in "${samples_wastewater[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf:/data \
    -v $(pwd)/result_mgf:/result \
    casanovo casanovo sequence /data/wastewater/${sample}.mgf \
    --output_dir /result/casanovo/wastewater \
    --output_root ${sample}
done

# Decoy
for sample in "${samples_ecoli[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf_decoy:/data \
    -v $(pwd)/result_mgf_decoy:/result \
    casanovo casanovo sequence /data/ecoli/${sample}.decoy.mgf \
    --output_dir /result/casanovo/ecoli \
    --output_root ${sample}.decoy
done

for sample in "${samples_wastewater[@]}"; do
  sudo docker run --rm --runtime=nvidia \
    --shm-size=2g --ulimit memlock=-1 \
    -v $(pwd)/data_mgf_decoy:/data \
    -v $(pwd)/result_mgf_decoy:/result \
    casanovo casanovo sequence /data/wastewater/${sample}.decoy.mgf \
    --output_dir /result/casanovo/wastewater \
    --output_root ${sample}.decoy
done