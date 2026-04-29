"""
build_groundtruth.py
Convert a MaxQuant msms (xlsx) export into a NovoBoard-ready ground-truth CSV.

The CSV has the exact columns WorkerTest._get_target() in NovoBoard reads:
    Source File, Scan, m/z, z, RT, Peptide
Peptide is in PEAKS notation (M(+15.99), C(+57.02), ...) which is the only
form NovoBoard's parse_raw_sequence accepts.

Usage:
    python build_groundtruth.py <msms.xlsx> <run_id> <output.csv>

Example:
    python build_groundtruth.py \
        data/ecoli/Database_search_output_Ecoli_EV_1.xlsx \
        Ecoli_EV_1 \
        ground_truth/ecoli/Ecoli_EV_1_groundtruth.csv
"""
import sys
import re
import os
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PEP_CUTOFF = 0.01     # MaxQuant per-PSM confidence
MIN_SCORE  = 0        # set >0 to apply an Andromeda score floor

# Carbamidomethyl on C is a *fixed* modification in MaxQuant, so it does NOT
# appear inside 'Modified sequence' (bare C is implied to be CAM). NovoBoard's
# vocab only recognizes C(Carbamidomethylation), not bare C, so we annotate
# every C with (+57.02) before feeding it to NovoBoard's parser.
# Set False if the search ran without fixed CAM on C (very rare).
ASSUME_FIXED_CAM_C = True

# ---------------------------------------------------------------------------
# Modification translation: MaxQuant 'Modified sequence' -> PEAKS notation
#   _IAATM(Oxidation (M))ENAQK_         -> IAATM(+15.99)ENAQK
#   _(Acetyl (Protein N-term))AGER_     -> AGER  (NovoBoard has no N-term Ac)
#   bare C (when ASSUME_FIXED_CAM_C)    -> C(+57.02)
# ---------------------------------------------------------------------------
MAXQUANT_OX_RE     = re.compile(r"\(Oxidation \(M\)\)")
MAXQUANT_ACETYL_RE = re.compile(r"\(Acetyl \(Protein N-term\)\)")
PAREN_GROUP_RE     = re.compile(r"\([^)]+\)")

KNOWN_PEAKS_TAGS = {"(+15.99)", "(+57.02)", "(+0.98)", "(+79.97)"}


def to_peaks(modseq: str) -> str:
    s = modseq.strip("_")
    s = MAXQUANT_OX_RE.sub("(+15.99)", s)
    s = MAXQUANT_ACETYL_RE.sub("", s)
    if ASSUME_FIXED_CAM_C:
        # Annotate any C not already followed by '('
        s = re.sub(r"C(?!\()", "C(+57.02)", s)
    return s


def has_unknown_mod(peaks_seq: str) -> bool:
    return any(m.group(0) not in KNOWN_PEAKS_TAGS
               for m in PAREN_GROUP_RE.finditer(peaks_seq))


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def load_and_filter(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    n0 = len(df)

    if "Contaminant" in df.columns:
        df = df[df["Contaminant"].isna() |
                (df["Contaminant"].astype(str).str.upper() != "+")]

    df = df[df["PEP"] <= PEP_CUTOFF]
    if MIN_SCORE > 0:
        df = df[df["Score"] >= MIN_SCORE]

    df = df.sort_values("Score", ascending=False).drop_duplicates("Scan number", keep="first")
    df = df.sort_values("Scan number").reset_index(drop=True)

    print(f"  Loaded {n0} PSMs -> {len(df)} after filtering "
          f"(no contaminants, PEP<={PEP_CUTOFF}, dedupe by scan)")
    return df


def write_novoboard_csv(df: pd.DataFrame, out_path: str, run_id: str) -> None:
    peptides = df["Modified sequence"].apply(to_peaks)

    unknown = peptides.apply(has_unknown_mod)
    if unknown.any():
        examples = peptides[unknown].head(5).tolist()
        print(f"  WARNING: {unknown.sum()} rows contain modifications not "
              f"translated to PEAKS notation.")
        print(f"           NovoBoard's parser will silently drop these rows.")
        print(f"           Examples: {examples}")
        print(f"           Add a translator in to_peaks() if you need them.")

    out = pd.DataFrame({
        "Source File": f"{run_id}.mgf",
        "Scan":        df["Scan number"].astype(int),
        "m/z":         0,
        "z":           df["Charge"].astype(int),
        "RT":          0,
        "Peptide":     peptides,
    })
    out.to_csv(out_path, index=False)
    print(f"  Wrote {len(out)} rows -> {out_path}")


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

    print(f"\n[2/2] Writing NovoBoard ground-truth CSV")
    write_novoboard_csv(df, out_path, run_id)

    print(f"\nDone -> {out_path}")


if __name__ == "__main__":
    main()
