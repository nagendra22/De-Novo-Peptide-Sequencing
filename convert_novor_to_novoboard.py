"""
convert_novor_to_novoboard.py

Parse a Novor predictions CSV and emit a NovoBoard-format CSV:
    Source File, Scan, m/z, z, RT, Peptide, Score

- Maps Novor's `id` column (1-based MGF spectrum index) to the original
  mzML scan number using the source MGF's TITLE suffix. The `scanNum`
  column is unreliable here because the source MGFs have no `SCANS=`
  field — Novor reports 0 for every row in that case — so we use `id`
  and convert to a 0-based index for the lookup.
- Translates Novor's mod tags to PEAKS notation:
    (Cam) -> (+57.02)   carbamidomethyl
    (O)   -> (+15.99)   oxidation
    (N)   -> (+0.98)    deamidation
    (P)   -> (+79.97)   phospho
- Uses Novor's `score` column (per-PSM, higher = better).

Usage:
    python convert_novor_to_novoboard.py \
        --pred result_mgf/novor/ecoli/Ecoli_EV_1.csv \
        --mgf data_mgf/ecoli/Ecoli_EV_1.mgf \
        --output novoboard_in/novor/ecoli/Ecoli_EV_1.csv
"""
import argparse
import csv
import os
import re
import sys

from mgf_index import build_index_to_scan


NOVOR_TO_PEAKS = {
    "(Cam)": "(+57.02)",
    "(O)":   "(+15.99)",
    "(N)":   "(+0.98)",
    "(P)":   "(+79.97)",
}

# After translation, anything in parens that starts with a letter is an
# untranslated Novor tag. PEAKS tags start with + or - and won't match.
LEFTOVER_PAREN_RE = re.compile(r"\([A-Za-z][^)]*\)")


def novor_to_peaks(pep: str) -> tuple[str, list[str]]:
    out = pep
    for src, dst in NOVOR_TO_PEAKS.items():
        out = out.replace(src, dst)
    leftovers = LEFTOVER_PAREN_RE.findall(out)
    return out, leftovers


def parse_novor_csv(path: str):
    """Yield dicts of {column: stripped_value} for each PSM row.

    Novor's column header is itself a `#` comment line that starts with
    '# id, scanNum, RT, ...'. Body rows are comma-separated with leading
    whitespace on each field.
    """
    header: list[str] | None = None
    with open(path) as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith("#"):
                if header is None and "id" in line and "scanNum" in line:
                    header = [c.strip() for c in line.lstrip("#").split(",")]
                    header = [c for c in header if c]
                continue
            if header is None:
                continue
            fields = [f.strip() for f in line.split(",")]
            yield dict(zip(header, fields))


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
    ap.add_argument("--pred", required=True, help="Novor predictions CSV")
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

    rows_in = rows_out = no_id = no_scan = empty_pred = 0
    unmapped_mods: dict[str, int] = {}

    with open(args.output, "w", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["Source File", "Scan", "m/z", "z", "RT", "Peptide", "Score", "AA Score"])

        for row in parse_novor_csv(args.pred):
            rows_in += 1
            try:
                novor_id = int(row.get("id", ""))
            except ValueError:
                no_id += 1
                continue
            idx = novor_id - 1
            scan = index_to_scan.get(idx)
            if scan is None:
                no_scan += 1
                continue

            pep_raw = row.get("peptide", "").strip()
            if not pep_raw:
                empty_pred += 1
                continue
            pep, leftovers = novor_to_peaks(pep_raw)
            for tag in leftovers:
                unmapped_mods[tag] = unmapped_mods.get(tag, 0) + 1

            mz = to_float(row.get("mz(data)", ""))
            z = to_int(row.get("z", ""))
            rt = to_float(row.get("RT", ""), default=0.0)
            score = to_float(row.get("score", ""))
            aa_score = (row.get("aaScore") or "").replace("-", " ").strip()

            writer.writerow([source_file, scan, mz, z, rt, pep, score, aa_score])
            rows_out += 1

    print(f"[3/3] Done")
    print(f"      Rows read    : {rows_in}")
    print(f"      Rows written : {rows_out}")
    if no_id:
        print(f"      Rows without parseable id: {no_id}")
    if no_scan:
        print(f"      Novor IDs not in MGF map : {no_scan}")
    if empty_pred:
        print(f"      Empty predictions        : {empty_pred}")
    if unmapped_mods:
        print(f"      WARNING: Novor mod tags with no PEAKS translation:")
        for tag, n in sorted(unmapped_mods.items(), key=lambda kv: -kv[1]):
            print(f"               {tag}  x{n}")


if __name__ == "__main__":
    main()
