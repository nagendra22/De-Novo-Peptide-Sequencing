#!/bin/bash
# Merge per-fraction NovoBoard-format CSVs into per-sample CSVs.
# Header taken from the first present input; data rows appended from
# all. Tolerates missing fractions (skips + logs).
#
# Sample groupings:
#   ecoli/Ecoli_EV               <-  Ecoli_EV_1, Ecoli_EV_2
#   wastewater/wastewater_Sample1   <-  wastewater_Sample1_1, wastewater_Sample1_2
#   wastewater/wastewater_Sample2   <-  wastewater_Sample2_1, wastewater_Sample2_2
#
# Output:
#   novoboard_in_merged/<tool>/{target,decoy}/<dataset>/<sample>.csv
#   ground_truth_merged/ecoli/Ecoli_EV.csv
#
# Usage:
#   bash merge_samples.sh

set -uo pipefail

# <merged_dataset>  <sample>              <fraction1>              <fraction2>
groupings=(
    "ecoli       Ecoli_EV              Ecoli_EV_1                Ecoli_EV_2"
    "wastewater  wastewater_Sample1    wastewater_Sample1_1      wastewater_Sample1_2"
    "wastewater  wastewater_Sample2    wastewater_Sample2_1      wastewater_Sample2_2"
)

tools=(casanovo instanovo instanovoplus novor)
runs=(target decoy)

merge_csvs() {
    local out="$1"; shift
    mkdir -p "$(dirname "$out")"
    : > "$out"
    local first=1
    for src in "$@"; do
        if [[ ! -f "$src" ]]; then
            echo "  SKIP (missing): $src"
            continue
        fi
        if (( first )); then
            cat "$src" >> "$out"
            first=0
        else
            tail -n +2 "$src" >> "$out"
        fi
    done
    if (( first )); then
        rm -f "$out"
        echo "  no inputs present — skipping $out"
        return 1
    fi
    echo "  merged → $out"
    return 0
}

# Predictions: tool × run × sample
for tool in "${tools[@]}"; do
    for run in "${runs[@]}"; do
        echo "=== ${tool} (${run}) ==="
        for grouping in "${groupings[@]}"; do
            read -r dataset sample f1 f2 <<< "$grouping"
            merge_csvs \
                "novoboard_in_merged/${tool}/${run}/${dataset}/${sample}.csv" \
                "novoboard_in/${tool}/${run}/${dataset}/${f1}.csv" \
                "novoboard_in/${tool}/${run}/${dataset}/${f2}.csv" \
                || true
        done
    done
done

# Ground truth (ecoli only — wastewater has no DB-search labels)
echo "=== ground truth (ecoli) ==="
merge_csvs \
    "ground_truth_merged/ecoli/Ecoli_EV.csv" \
    "ground_truth/ecoli/Ecoli_EV_1.csv" \
    "ground_truth/ecoli/Ecoli_EV_2.csv" \
    || true

echo "Done."
