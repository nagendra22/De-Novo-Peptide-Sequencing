"""
convert_casanovo_to_novoboard.py

Parse a Casanovo .mztab and emit a NovoBoard-format CSV:
    Source File, Scan, m/z, z, RT, Peptide, Score

- Maps Casanovo's `spectra_ref = ms_run[1]:index=N` (0-based MGF file
  index) to the original mzML scan number using the source MGF's
  TITLE suffix.
- Translates ProForma mods (`C[Carbamidomethyl]`, `M[Oxidation]`,
  `N[Deamidated]`, `S[Phospho]`) to PEAKS notation
  (`C(+57.02)`, `M(+15.99)`, `N(+0.98)`, `S(+79.97)`).
- Uses `search_engine_score[1]` as the FDR-friendly Score column.

Usage:
    python convert_casanovo_to_novoboard.py \
        --pred result_mgf/casanovo/ecoli/Ecoli_EV_1.mztab \
        --mgf data_mgf/ecoli/Ecoli_EV_1.mgf \
        --output novoboard_in/casanovo/ecoli/Ecoli_EV_1.csv
"""
import argparse
import csv
import os
import re
import sys

from mgf_index import build_index_to_scan


PROFORMA_TO_PEAKS = {
    "[Carbamidomethyl]": "(+57.02)",
    "[Oxidation]":       "(+15.99)",
    "[Deamidated]":      "(+0.98)",
    "[Phospho]":         "(+79.97)",
    # N-terminal mods Casanovo can predict that NovoBoard's vocab does
    # not accept. build_groundtruth.py drops the equivalents from the
    # ground truth, so we strip them here too — otherwise predictions
    # would never match GT even when the underlying call is correct.
    "[Acetyl]":       "",
    "[Carbamyl]":     "",
    "[Ammonia-loss]": "",
}

PROFORMA_MOD_RE = re.compile(r"\[[^\]]+\]")
SPECTRA_REF_RE = re.compile(r"index=(\d+)")


def proforma_to_peaks(pep: str) -> tuple[str, list[str]]:
    out = pep
    for src, dst in PROFORMA_TO_PEAKS.items():
        out = out.replace(src, dst)
    # ProForma sometimes writes N-term mods as `[Mod]-PEPTIDE`; once the
    # mod is stripped to empty, a stray leading hyphen is left behind.
    if out.startswith("-"):
        out = out[1:]
    leftovers = [m.group(0) for m in PROFORMA_MOD_RE.finditer(out)]
    return out, leftovers


def parse_mztab_psms(path: str):
    header: list[str] | None = None
    with open(path) as f:
        for line in f:
            if line.startswith("PSH"):
                header = line.rstrip("\n").split("\t")
            elif line.startswith("PSM"):
                if header is None:
                    sys.exit(f"PSM row before PSH header in {path}")
                fields = line.rstrip("\n").split("\t")
                yield dict(zip(header, fields))


def to_float(s: str, default: float = float("nan")) -> float:
    if s is None or s == "" or s == "null":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def to_int(s: str, default: int = 0) -> int:
    if s is None or s == "" or s == "null":
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
    ap.add_argument("--pred", required=True, help="Casanovo .mztab file")
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

    print(f"[2/3] Parsing PSMs from {args.pred}")
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    rows_in = rows_out = no_index = no_scan = 0
    unmapped_mods: dict[str, int] = {}

    with open(args.output, "w", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["Source File", "Scan", "m/z", "z", "RT", "Peptide", "Score"])

        for psm in parse_mztab_psms(args.pred):
            rows_in += 1
            spec_ref = psm.get("spectra_ref", "")
            m = SPECTRA_REF_RE.search(spec_ref)
            if not m:
                no_index += 1
                continue
            idx = int(m.group(1))
            scan = index_to_scan.get(idx)
            if scan is None:
                no_scan += 1
                continue

            # Casanovo writes ProForma in opt_ms_run[1]_proforma; fall back
            # to `sequence` if that column isn't present.
            pep_raw = psm.get("opt_ms_run[1]_proforma") or psm.get("sequence", "")
            pep, leftovers = proforma_to_peaks(pep_raw)
            for tag in leftovers:
                unmapped_mods[tag] = unmapped_mods.get(tag, 0) + 1

            mz = to_float(psm.get("exp_mass_to_charge", ""))
            z = to_int(psm.get("charge", ""))
            rt = to_float(psm.get("retention_time", ""), default=0.0)
            score = to_float(psm.get("search_engine_score[1]", ""))

            writer.writerow([source_file, scan, mz, z, rt, pep, score])
            rows_out += 1

    print(f"[3/3] Done")
    print(f"      PSMs read              : {rows_in}")
    print(f"      Rows written           : {rows_out}")
    if no_index:
        print(f"      PSMs without index ref : {no_index}")
    if no_scan:
        print(f"      Indices not in MGF map : {no_scan}")
    if unmapped_mods:
        print(f"      WARNING: ProForma mods with no PEAKS translation:")
        for tag, n in sorted(unmapped_mods.items(), key=lambda kv: -kv[1]):
            print(f"               {tag}  x{n}")


if __name__ == "__main__":
    main()
