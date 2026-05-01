#!/bin/bash

samples_ecoli=(Ecoli_EV_1 Ecoli_EV_2)

for sample in "${samples_ecoli[@]}"; do
    python annotate_mgf.py \
        --mgf data_mgf/ecoli/${sample}.mgf \
        --groundtruth ground_truth/ecoli/${sample}.csv \
        --output data_mgf_annotated/ecoli/${sample}.casanovo.annotated.mgf \
        --notation casanovo

    python annotate_mgf.py \
        --mgf data_mgf/ecoli/${sample}.mgf \
        --groundtruth ground_truth/ecoli/${sample}.csv \
        --output data_mgf_annotated/ecoli/${sample}.instanovo.annotated.mgf \
        --notation peaks
done