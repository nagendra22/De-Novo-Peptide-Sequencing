# De-Novo-Peptide-Sequencing
De Novo Peptide Sequencing

## Preprocessing

### Convert mzML to mgf
convert_mzml_to_mgf.ps1

### Build Ground truth
```
python build_groundtruth.py data/ecoli/Database_search_output_Ecoli_EV_1.xlsx Ecoli_EV_1 ground_truth/ecoli/Ecoli_EV_1.csv
python build_groundtruth.py data/ecoli/Database_search_output_Ecoli_EV_2.xlsx Ecoli_EV_2 ground_truth/ecoli/Ecoli_EV_2.csv
```

### Generate Decoy
```
python generate_decoy.py data_mgf/ecoli/Ecoli_EV_1.mgf data_mgf_decoy/ecoli/Ecoli_EV_1.mgf
python generate_decoy.py data_mgf/ecoli/Ecoli_EV_2.mgf data_mgf_decoy/ecoli/Ecoli_EV_2.mgf

python generate_decoy.py data_mgf/wastewater/wastewater_Sample1_1.mgf data_mgf_decoy/wastewater/wastewater_Sample1_1.mgf
python generate_decoy.py data_mgf/wastewater/wastewater_Sample1_2.mgf data_mgf_decoy/wastewater/wastewater_Sample1_2.mgf
python generate_decoy.py data_mgf/wastewater/wastewater_Sample2_1.mgf data_mgf_decoy/wastewater/wastewater_Sample2_1.mgf
python generate_decoy.py data_mgf/wastewater/wastewater_Sample2_2.mgf data_mgf_decoy/wastewater/wastewater_Sample2_2.mgf
```