# De-Novo-Peptide-Sequencing
De Novo Peptide Sequencing

## Preprocessing

### Convert mzML to mgf
convert_mzml_to_mgf.ps1

### Exploratory Data Analysis
Run the notebook
* eda.ipynb

### Build Ground truth

```
python build_groundtruth.py data/ecoli/Database_search_output_Ecoli_EV_1.xlsx Ecoli_EV_1 ground_truth/ecoli/Ecoli_EV_1.csv

python build_groundtruth.py data/ecoli/Database_search_output_Ecoli_EV_2.xlsx Ecoli_EV_2 ground_truth/ecoli/Ecoli_EV_2.csv
```

### Generate Decoy

```
# E Coli
python generate_decoy.py data_mgf/ecoli/Ecoli_EV_1.mgf data_mgf_decoy/ecoli/Ecoli_EV_1.decoy.mgf

python generate_decoy.py data_mgf/ecoli/Ecoli_EV_2.mgf data_mgf_decoy/ecoli/Ecoli_EV_2.decoy.mgf

# Wastewater
python generate_decoy.py data_mgf/wastewater/wastewater_Sample1_1.mgf data_mgf_decoy/wastewater/wastewater_Sample1_1.decoy.mgf

python generate_decoy.py data_mgf/wastewater/wastewater_Sample1_2.mgf data_mgf_decoy/wastewater/wastewater_Sample1_2.decoy.mgf

python generate_decoy.py data_mgf/wastewater/wastewater_Sample2_1.mgf data_mgf_decoy/wastewater/wastewater_Sample2_1.decoy.mgf

python generate_decoy.py data_mgf/wastewater/wastewater_Sample2_2.mgf data_mgf_decoy/wastewater/wastewater_Sample2_2.decoy.mgf
```

## Predict

### Novor

```
./run_novor.sh
```

### Casanovo

```
sudo docker build -t casanovo .

./run_casanovo.sh
```

### Instanovo, Instanovo+

Run the following in Colab (A100 GPU)
* instanovo/instanovo_colab_ecoli.ipynb
* instanovo/instanovo_colab_wastewater.ipynb

## Evaluate

### NovoBoard

```
./run_conversions.sh

./merge_samples.sh
```

Quick summary:
* evaluation.ipynb

run NovoBoard notebooks for more details
* novoboard/aa.fdr_github_ecoli.ipynb
* novoboard/aa.fdr_github_wastewater_sample1.ipynb
* novoboard/aa.fdr_github_wastewater_sample2.ipynb

### NovoBoard TODO:

Generate Decoy MGFs at (30/40/60/70%) for FDR Calibration validation. We have selected 1%, 5% and 10% FDR for evaluation but we are not sure of true or more accurate FDR. This will result in 4 inference runs for all samples for all tools and give better calibration.

## Map to biological source

### Unipept

```
python filter_for_unipept.py
```

## Finetune

### Annotate E. Coli mgf with ground truth

```
annotate_mgf.sh
```

### Split training and validation

```
./split_annotated_mgf.sh
```

### Run Finetune

```
./run_casanovo_finetune.sh
```

Run the following in colab (A100 GPU)
* instanovo/instanovo_colab_finetune.ipynb
* instanovo/instanovoplus_colab_finetune.ipynb

### Evaluate Finetune

```
./run_casanovo_finetune_eval.sh
```

Run the following in Colab (A100 GPU)
* instanovo/instanovo_colab_evaluate.ipynb
* instanovo/instanovoplus_colab_evaluate.ipynb

### Predict using finetuned model

```
./run_casanovo_finetune_predict.sh
```

Run the following in Colab (A 100)
* instanovo/instanovo_colab_ecoli_finetune.ipynb
* instanovo/instanovo_colab_wastewater_finetune.ipynb

### NovoBoard

```
./run_conversions_finetune.sh

./merge_samples_finetune.sh
```

run NovoBoard notebooks
* novoboard/aa.fdr_github_ecoli.ipynb
* novoboard/aa.fdr_github_wastewater_sample1.ipynb
* novoboard/aa.fdr_github_wastewater_sample2.ipynb
