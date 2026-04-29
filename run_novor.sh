#!/bin/bash

samples_ecoli=(Ecoli_EV_1 Ecoli_EV_2)
samples_wastewater=(wastewater_Sample1_1 wastewater_Sample1_2 wastewater_Sample2_1 wastewater_Sample2_2)

# mkdir -p result/novor/ecoli result/novor/wastewater
mkdir -p result_mgf/novor/ecoli result_mgf/novor/wastewater
mkdir -p result_mgf_decoy/novor/ecoli result_mgf_decoy/novor/wastewater

# # mzML
# for sample in "${samples_ecoli[@]}"; do
#   java -jar bin/novor/novor.jar \
#     -p config/novor_params.txt \
#     -o result/novor/ecoli/${sample}.csv \
#     data/ecoli/${sample}.mzML \
#     -f
# done

# for sample in "${samples_wastewater[@]}"; do
#   java -jar bin/novor/novor.jar \
#     -p config/novor_params.txt \
#     -o result/novor/wastewater/${sample}.csv \
#     data/wastewater/${sample}.mzML \
#     -f
# done

# MGF
for sample in "${samples_ecoli[@]}"; do
  java -jar bin/novor/novor.jar \
    -p config/novor_params.txt \
    -o result_mgf/novor/ecoli/${sample}.csv \
    data_mgf/ecoli/${sample}.mgf \
    -f
done

for sample in "${samples_wastewater[@]}"; do
  java -jar bin/novor/novor.jar \
    -p config/novor_params.txt \
    -o result_mgf/novor/wastewater/${sample}.csv \
    data_mgf/wastewater/${sample}.mgf \
    -f
done

# Decoy
for sample in "${samples_ecoli[@]}"; do
  java -jar bin/novor/novor.jar \
    -p config/novor_params.txt \
    -o result_mgf_decoy/novor/ecoli/${sample}.decoy.csv \
    data_mgf_decoy/ecoli/${sample}.decoy.mgf \
    -f
done

for sample in "${samples_wastewater[@]}"; do
  java -jar bin/novor/novor.jar \
    -p config/novor_params.txt \
    -o result_mgf_decoy/novor/wastewater/${sample}.decoy.csv \
    data_mgf_decoy/wastewater/${sample}.decoy.mgf \
    -f
done
