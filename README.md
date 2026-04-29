# De-Novo-Peptide-Sequencing
De Novo Peptide Sequencing

## Preprocessing

### Convert mzML to mgf
convert_mzml_to_mgf.ps1

### Build Ground truth
```
python build_groundtruth.py data/ecoli/Database_search_output_Ecoli_EV_1.xlsx Ecoli_EV_1 ground_truth/ecoli/Ecoli_EV_1.csv
```
```
python build_groundtruth.py data/ecoli/Database_search_output_Ecoli_EV_2.xlsx Ecoli_EV_1 ground_truth/ecoli/Ecoli_EV_2.csv
```