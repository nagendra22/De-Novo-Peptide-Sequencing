#!/bin/bash
# Convert per-tool prediction outputs into NovoBoard-format CSVs (one
# CSV per fraction). Output tree:
#   novoboard_in/<tool>/{target,decoy}/<dataset>/<fraction>.csv
#
# Tolerates missing inputs (e.g. InstaNovo decoys still on Colab) —
# logs SKIP and continues. Idempotent: outputs are overwritten on
# re-run.
#
# Usage:
#   bash run_conversions.sh

set -uo pipefail

samples_ecoli=(Ecoli_EV_1 Ecoli_EV_2)
samples_wastewater=(wastewater_Sample1_1 wastewater_Sample1_2 wastewater_Sample2_1 wastewater_Sample2_2)

# <tool>  <converter>                            <pred file ext>
# instanovoplus reuses the instanovo converter (same CSV schema).
tools=(
    "casanovo       convert_casanovo_to_novoboard.py    mztab"
    "instanovo      convert_instanovo_to_novoboard.py   csv"
    "instanovoplus  convert_instanovo_to_novoboard.py   csv"
    "novor          convert_novor_to_novoboard.py       csv"
)

run_one() {
    local converter="$1" pred="$2" mgf="$3" out="$4"
    if [[ ! -f "$pred" ]]; then
        echo "  SKIP (missing pred): $pred"
        return
    fi
    if [[ ! -f "$mgf" ]]; then
        echo "  SKIP (missing mgf):  $mgf"
        return
    fi
    mkdir -p "$(dirname "$out")"
    python "$converter" --pred "$pred" --mgf "$mgf" --output "$out" >/dev/null
    echo "  ok: $out"
}

for tool_spec in "${tools[@]}"; do
    read -r tool converter ext <<< "$tool_spec"

    echo "=== ${tool} (target) ==="
    for s in "${samples_ecoli[@]}"; do
        run_one "$converter" \
            "result_mgf/${tool}/ecoli/${s}.${ext}" \
            "data_mgf/ecoli/${s}.mgf" \
            "novoboard_in/${tool}/target/ecoli/${s}.csv"
    done
    for s in "${samples_wastewater[@]}"; do
        run_one "$converter" \
            "result_mgf/${tool}/wastewater/${s}.${ext}" \
            "data_mgf/wastewater/${s}.mgf" \
            "novoboard_in/${tool}/target/wastewater/${s}.csv"
    done

    echo "=== ${tool} (decoy) ==="
    for s in "${samples_ecoli[@]}"; do
        run_one "$converter" \
            "result_mgf_decoy/${tool}/ecoli/${s}.decoy.${ext}" \
            "data_mgf_decoy/ecoli/${s}.decoy.mgf" \
            "novoboard_in/${tool}/decoy/ecoli/${s}.csv"
    done
    for s in "${samples_wastewater[@]}"; do
        run_one "$converter" \
            "result_mgf_decoy/${tool}/wastewater/${s}.decoy.${ext}" \
            "data_mgf_decoy/wastewater/${s}.decoy.mgf" \
            "novoboard_in/${tool}/decoy/wastewater/${s}.csv"
    done
done

echo "Done."
