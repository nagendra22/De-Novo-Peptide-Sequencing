"""
filter_for_unipept.py

For each (sample, tool) pair, read the NovoBoard FDR CSV produced by
the notebooks, keep target rows below the FDR cutoff, strip PEAKS mod
tags, dedupe the peptide list, and write a plain text file ready for
Unipept's Metaproteomics Analysis upload.

Output:
    unipept_in/<sample>/<tool>_<fdr_label>.txt    one peptide per line

Usage:
    python filter_for_unipept.py                  # FDR <= 1% (default)
    python filter_for_unipept.py --fdr 0.05       # FDR <= 5%
"""
import argparse
import csv
import re
from pathlib import Path

# Strip every parenthesised mod tag, e.g. C(+57.02), M(+15.99), etc.
MOD_TAG_RE = re.compile(r"\([^)]*\)")


def strip_mods(peptide: str) -> str:
    return MOD_TAG_RE.sub("", peptide)


def filter_one(fdr_csv: Path, out_path: Path, fdr_cutoff: float) -> tuple[int, int]:
    """Returns (n_psms_kept, n_unique_peptides)."""
    kept_peptides: set[str] = set()
    n_kept = 0
    with fdr_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("is_target", "").strip().lower() != "true":
                continue
            try:
                est_fdr = float(row["estimated_fdr"])
            except (KeyError, ValueError):
                continue
            if est_fdr > fdr_cutoff:
                continue
            pep = strip_mods((row.get("Peptide") or "").strip())
            if not pep:
                continue
            kept_peptides.add(pep)
            n_kept += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sorted(kept_peptides)) + "\n")
    return n_kept, len(kept_peptides)


def filter_gt(gt_csv: Path, out_path: Path) -> tuple[int, int]:
    """Process the DB-search ground truth.

    GT is already filtered at PEP <= 0.01 by build_groundtruth.py, so
    no extra FDR step is needed — just strip mods and dedupe.
    """
    kept_peptides: set[str] = set()
    n_psms = 0
    with gt_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pep = strip_mods((row.get("Peptide") or "").strip())
            if not pep:
                continue
            kept_peptides.add(pep)
            n_psms += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sorted(kept_peptides)) + "\n")
    return n_psms, len(kept_peptides)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--fdr", type=float, default=0.01,
                    help="FDR cutoff (default 0.01 = 1%%)")
    ap.add_argument("--in-root", default="novoboard_out",
                    help="root containing <sample>/<tool>.fdr.csv files")
    ap.add_argument("--out-root", default="unipept_in",
                    help="root for the per-(sample,tool) peptide lists")
    args = ap.parse_args()

    fdr_label = f"{int(round(args.fdr * 100))}pct"
    in_root = Path(args.in_root)
    out_root = Path(args.out_root)

    samples = ["ecoli", "wastewater_Sample1", "wastewater_Sample2"]
    tools = ["casanovo", "instanovo", "instanovoplus", "novor"]

    # Map sample -> path of merged DB-search ground truth (only ecoli has one).
    gt_paths = {
        "ecoli": Path("ground_truth_merged/ecoli/Ecoli_EV.csv"),
    }

    print(f"FDR cutoff: <= {args.fdr*100:.1f}%   (label: {fdr_label})\n")
    print(f"{'sample':<22}{'tool':<16}{'PSMs':>10}{'unique pep':>14}")
    print("-" * 62)

    for sample in samples:
        for tool in tools:
            fdr_csv = in_root / sample / f"{tool}.fdr.csv"
            out_path = out_root / sample / f"{tool}_{fdr_label}.txt"
            if not fdr_csv.exists():
                print(f"{sample:<22}{tool:<16}{'(missing)':>10}")
                continue
            n_psms, n_unique = filter_one(fdr_csv, out_path, args.fdr)
            print(f"{sample:<22}{tool:<16}{n_psms:>10}{n_unique:>14}")

        gt_path = gt_paths.get(sample)
        if gt_path and gt_path.exists():
            out_path = out_root / sample / "groundtruth.txt"
            n_psms, n_unique = filter_gt(gt_path, out_path)
            print(f"{sample:<22}{'groundtruth':<16}{n_psms:>10}{n_unique:>14}")
        elif gt_path:
            print(f"{sample:<22}{'groundtruth':<16}{'(missing)':>10}")

    print(f"\nWrote peptide lists to {out_root}/")


if __name__ == "__main__":
    main()
