"""
convert_instanovo_to_novoboard.py

Parse an InstaNovo or InstaNovo+ predictions CSV and emit a
NovoBoard-format CSV:
    Source File, Scan, m/z, z, RT, Peptide, Score

- Maps InstaNovo's `scan_number` (0-based MGF file index) to the
  original mzML scan number using the source MGF's TITLE suffix.
- Translates ProForma UNIMOD codes (`[UNIMOD:35]`, `[UNIMOD:4]`,
  `[UNIMOD:7]`, `[UNIMOD:21]`) to PEAKS notation.
- Uses `log_probs` as the FDR-friendly Score column (higher = more
  confident, since these are log-probs).
- Works for both `instanovo transformer predict` and `instanovo
  diffusion predict` outputs (same CSV schema; the diffusion variant
  has an extra `unrefined_predictions` column we ignore).

Usage:
    python convert_instanovo_to_novoboard.py \
        --pred result_mgf/instanovo/ecoli/Ecoli_EV_1.csv \
        --mgf data_mgf/ecoli/Ecoli_EV_1.mgf \
        --output novoboard_in/instanovo/ecoli/Ecoli_EV_1.csv
"""
import argparse
import ast
import csv
import os
import re
import sys

from mgf_index import build_index_to_scan


UNIMOD_TO_PEAKS = {
    "[UNIMOD:35]":  "(+15.99)",  # oxidation
    "[UNIMOD:4]":   "(+57.02)",  # carbamidomethyl
    "[UNIMOD:7]":   "(+0.98)",   # deamidation
    "[UNIMOD:21]":  "(+79.97)",  # phospho
    # N-terminal mods InstaNovo can predict that NovoBoard's vocab does
    # not accept. build_groundtruth.py drops the equivalents from the
    # ground truth, so we strip them here too.
    "[UNIMOD:1]":   "",          # acetyl
    "[UNIMOD:5]":   "",          # carbamyl
    "[UNIMOD:385]": "",          # ammonia-loss
}

PROFORMA_MOD_RE = re.compile(r"\[[^\]]+\]")


def proforma_to_peaks(pep: str) -> tuple[str, list[str]]:
    out = pep
    for src, dst in UNIMOD_TO_PEAKS.items():
        out = out.replace(src, dst)
    if out.startswith("-"):
        out = out[1:]
    leftovers = [m.group(0) for m in PROFORMA_MOD_RE.finditer(out)]
    return out, leftovers


def to_float(s: str, default: float = float("nan")) -> float:
    if s is None or s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def to_int(s: str, default: int = 0) -> int:
    if s is None or s == "":
        return default
    try:
        return int(float(s))
    except ValueError:
        return default


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--pred", required=True, help="InstaNovo predictions CSV")
    ap.add_argument("--mgf",  required=True, help="source MGF (for index→scan)")
    ap.add_argument("--output", required=True, help="output NovoBoard CSV")
    ap.add_argument("--source-file", default=None,
                    help="value for the 'Source File' column "
                         "(default: basename of --mgf)")
    args = ap.parse_args()

    source_file = args.source_file or os.path.basename(args.mgf)

    print(f"[1/3] Building index → scan map from {args.mgf}")
    index_to_scan = build_index_to_scan(args.mgf)
    print(f"      {len(index_to_scan)} spectra indexed")

    print(f"[2/3] Reading predictions from {args.pred}")
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    rows_in = rows_out = no_scan = empty_pred = 0
    unmapped_mods: dict[str, int] = {}

    with open(args.pred, newline="") as fin, open(args.output, "w", newline="") as fout:
        reader = csv.DictReader(fin)
        required = ["scan_number", "predictions", "log_probs",
                    "precursor_mz", "precursor_charge"]
        missing = [c for c in required if c not in reader.fieldnames]
        if missing:
            sys.exit(f"missing columns in {args.pred}: {missing}")
        has_token_lp = "token_log_probs" in reader.fieldnames

        writer = csv.writer(fout)
        writer.writerow(["Source File", "Scan", "m/z", "z", "RT", "Peptide", "Score", "AA Score"])

        for row in reader:
            rows_in += 1
            try:
                idx = int(row["scan_number"])
            except (ValueError, TypeError):
                continue
            scan = index_to_scan.get(idx)
            if scan is None:
                no_scan += 1
                continue

            pep_raw = (row.get("predictions") or "").strip()
            if not pep_raw:
                empty_pred += 1
                continue
            pep, leftovers = proforma_to_peaks(pep_raw)
            for tag in leftovers:
                unmapped_mods[tag] = unmapped_mods.get(tag, 0) + 1

            mz = to_float(row.get("precursor_mz", ""))
            z = to_int(row.get("precursor_charge", ""))
            score = to_float(row.get("log_probs", ""))

            aa_score = ""
            if has_token_lp:
                tlp = (row.get("token_log_probs") or "").strip()
                if tlp:
                    try:
                        vals = ast.literal_eval(tlp)
                        aa_score = " ".join(f"{float(v):.6f}" for v in vals)
                    except (ValueError, SyntaxError):
                        aa_score = ""

            writer.writerow([source_file, scan, mz, z, 0, pep, score, aa_score])
            rows_out += 1

    print(f"[3/3] Done")
    print(f"      Rows read    : {rows_in}")
    print(f"      Rows written : {rows_out}")
    if no_scan:
        print(f"      Indices not in MGF map: {no_scan}")
    if empty_pred:
        print(f"      Empty predictions     : {empty_pred}")
    if unmapped_mods:
        print(f"      WARNING: UNIMOD codes with no PEAKS translation:")
        for tag, n in sorted(unmapped_mods.items(), key=lambda kv: -kv[1]):
            print(f"               {tag}  x{n}")


if __name__ == "__main__":
    main()
