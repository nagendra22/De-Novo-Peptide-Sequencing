#!/bin/bash
# Merge per-fraction NovoBoard-format CSVs (fine-tuned predictions)
# into per-sample CSVs. Header taken from the first present input;
# data rows appended from all. Tolerates missing fractions
# (skips + logs).
#
# Sample groupings:
#   wastewater/wastewater_Sample1   <-  wastewater_Sample1_1, wastewater_Sample1_2
#   wastewater/wastewater_Sample2   <-  wastewater_Sample2_1, wastewater_Sample2_2
#
# Output:
#   novoboard_in_finetune_merged/<tool>/{target,decoy}/wastewater/<sample>.csv
#
# Note: ecoli has only one held-out fraction (EV_2) — no merge needed,
# so downstream tools read it directly from the per-fraction tree:
#   novoboard_in_finetune/<tool>/{target,decoy}/ecoli/Ecoli_EV_2.csv
# (produced by run_conversions_finetune.sh).
#
# (No GT merge here — ground truth is independent of fine-tuning and
# already merged by merge_samples.sh into ground_truth_merged/.)
#
# Usage:
#   bash merge_samples_finetune.sh

set -uo pipefail

# <merged_dataset>  <sample>              <fraction1>              <fraction2>
groupings=(
    "wastewater  wastewater_Sample1    wastewater_Sample1_1      wastewater_Sample1_2"
    "wastewater  wastewater_Sample2    wastewater_Sample2_1      wastewater_Sample2_2"
)

# Novor removed (closed source, not fine-tunable).
tools=(
    casanovo
    instanovo
    instanovoplus
)
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
                "novoboard_in_finetune_merged/${tool}/${run}/${dataset}/${sample}.csv" \
                "novoboard_in_finetune/${tool}/${run}/${dataset}/${f1}.csv" \
                "novoboard_in_finetune/${tool}/${run}/${dataset}/${f2}.csv" \
                || true
        done
    done
done

echo "Done."
