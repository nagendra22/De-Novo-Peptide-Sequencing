"""
build_groundtruth.py
Convert a MaxQuant msms.txt (Excel) export into a clean ground-truth TSV
for NovoBoard.

Usage:
  python build_groundtruth.py <msms.xlsx> <run_id> <output.tsv>

Example:
  python build_groundtruth.py \
    data/ecoli/Database_search_output_Ecoli_EV_1.xlsx \
    Ecoli_EV_1 \
    ground_truth/ecoli/Ecoli_EV_1_groundtruth.tsv
"""
import sys
import re
import os
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PEP_CUTOFF = 0.01       # 1% PEP — standard MaxQuant per-PSM confidence
MIN_SCORE  = 0          # set >0 if you want a stricter Andromeda score floor

# ---------------------------------------------------------------------------
# PTM translation
# MaxQuant 'Modified sequence' notation is like:  _IAATM(Oxidation (M))ENAQK_
# We strip leading/trailing underscores and rewrite modifications into
# each downstream tool's preferred notation.
# ---------------------------------------------------------------------------
MAXQUANT_OX_RE     = re.compile(r"\(Oxidation \(M\)\)")
MAXQUANT_ACETYL_RE = re.compile(r"\(Acetyl \(Protein N-term\)\)")

def to_casanovo(modseq: str) -> str:
    s = modseq.strip("_")
    s = MAXQUANT_OX_RE.sub("+15.995", s)
    s = MAXQUANT_ACETYL_RE.sub("", s)
    return s

def to_instanovo(modseq: str) -> str:
    s = modseq.strip("_")
    s = MAXQUANT_OX_RE.sub("(+15.99)", s)
    s = MAXQUANT_ACETYL_RE.sub("", s)
    return s

def to_novoboard(modseq: str) -> str:
    """Matches NovoBoard config.py vocab: M(Oxidation)"""
    s = modseq.strip("_")
    s = MAXQUANT_OX_RE.sub("(Oxidation)", s)
    s = MAXQUANT_ACETYL_RE.sub("", s)
    return s

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def load_and_filter(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    n0 = len(df)

    # Drop contaminants (Contaminant column has '+' for contaminant rows)
    if "Contaminant" in df.columns:
        df = df[df["Contaminant"].isna() |
                (df["Contaminant"].astype(str).str.upper() != "+")]

    # Confidence filter
    df = df[df["PEP"] <= PEP_CUTOFF]
    if MIN_SCORE > 0:
        df = df[df["Score"] >= MIN_SCORE]

    # Keep highest-scoring PSM per scan
    df = df.sort_values("Score", ascending=False).drop_duplicates("Scan number", keep="first")
    df = df.sort_values("Scan number").reset_index(drop=True)

    print(f"  Loaded {n0} PSMs -> {len(df)} after filtering "
          f"(no contaminants, PEP<={PEP_CUTOFF}, dedupe by scan)")
    return df

def write_groundtruth(df: pd.DataFrame, out_path: str, run_id: str) -> None:
    out = pd.DataFrame({
        "spectrum_id":       [f"{run_id}.scan{s}" for s in df["Scan number"]],
        "run_id":            run_id,
        "scan":              df["Scan number"].astype(int),
        "charge":            df["Charge"].astype(int),
        "peptide_plain":     df["Sequence"],
        "peptide_casanovo":  df["Modified sequence"].apply(to_casanovo),
        "peptide_instanovo": df["Modified sequence"].apply(to_instanovo),
        "peptide_novoboard": df["Modified sequence"].apply(to_novoboard),
        "score":             df["Score"],
        "PEP":               df["PEP"],
    })
    out.to_csv(out_path, sep="\t", index=False)
    print(f"  Wrote {len(out)} ground-truth rows -> {out_path}")

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    xlsx_path, run_id, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print(f"\n[1/2] Loading and filtering {xlsx_path}")
    df = load_and_filter(xlsx_path)

    print(f"\n[2/2] Writing ground-truth TSV")
    write_groundtruth(df, out_path, run_id)

    print(f"\nDone -> {out_path}")

if __name__ == "__main__":
    main()