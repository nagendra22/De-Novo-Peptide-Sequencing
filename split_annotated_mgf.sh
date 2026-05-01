#!/bin/bash

python split_annotated_mgf.py \
    --input data_mgf_annotated/ecoli/Ecoli_EV_1.casanovo.annotated.mgf \
    --train-out data_mgf_annotated/ecoli/Ecoli_EV_1.casanovo.train.mgf \
    --val-out data_mgf_annotated/ecoli/Ecoli_EV_1.casanovo.val.mgf \
    --train-ratio 0.85 \
    --seed 42

python split_annotated_mgf.py \
    --input data_mgf_annotated/ecoli/Ecoli_EV_1.instanovo.annotated.mgf \
    --train-out data_mgf_annotated/ecoli/Ecoli_EV_1.instanovo.train.mgf \
    --val-out data_mgf_annotated/ecoli/Ecoli_EV_1.instanovo.val.mgf \
    --train-ratio 0.85 \
    --seed 42