"""
annotate_mgf.py
Inject SEQ= ground-truth labels into an MGF for use with
`casanovo evaluate` / `instanovo --evaluate`.

Maps spectra by the scan number embedded in the ProteoWizard MGF TITLE
suffix (".firstScan.lastScan.charge") against the ground-truth CSV's
"Scan" column.

The ground-truth CSV is assumed to be in PEAKS notation (as produced by
build_groundtruth.py: C(+57.02), M(+15.99), ...). Use --notation to pick
the SEQ= form written into the output:

    peaks    (default)  C(+57.02), M(+15.99)   <- InstaNovo / NovoBoard
    casanovo            C+57.021,  M+15.995    <- Casanovo

Usage:
    python annotate_mgf.py \
        --mgf data_mgf/ecoli/Ecoli_EV_1.mgf \
        --groundtruth ground_truth/ecoli/Ecoli_EV_1.csv \
        --output data_mgf_annotated/ecoli/Ecoli_EV_1.instanovo.annotated.mgf \
        --notation peaks

By default unlabelled spectra are dropped (the evaluators only score
labelled ones, and keeping unlabelled spectra dilutes throughput with no
benefit). Pass --keep-unlabelled to retain them.
"""
import argparse
import csv
import os
import re
import sys


TITLE_SCAN_RE = re.compile(r"\.(\d+)\.(\d+)\.(\d+)\s*$")

# PEAKS-rounded mass deltas -> Casanovo's canonical 3-decimal masses.
# Keys match the tags that build_groundtruth.py writes.
PEAKS_TO_CASANOVO = {
    "(+15.99)": "+15.995",
    "(+57.02)": "+57.021",
    "(+0.98)":  "+0.984",
    "(+79.97)": "+79.966",
}

LEFTOVER_PAREN_RE = re.compile(r"\([^)]+\)")


def to_casanovo_notation(pep: str) -> tuple[str, list[str]]:
    out = pep
    for src, dst in PEAKS_TO_CASANOVO.items():
        out = out.replace(src, dst)
    leftovers = LEFTOVER_PAREN_RE.findall(out)
    return out, leftovers


def load_groundtruth(path: str, notation: str) -> dict[int, str]:
    scan_to_pep: dict[int, str] = {}
    unmapped: dict[str, int] = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if "Scan" not in reader.fieldnames or "Peptide" not in reader.fieldnames:
            sys.exit(f"ground truth must have 'Scan' and 'Peptide' columns, "
                     f"got {reader.fieldnames}")
        for row in reader:
            scan = int(row["Scan"])
            pep = row["Peptide"].strip()
            if not pep:
                continue
            if notation == "casanovo":
                pep, leftovers = to_casanovo_notation(pep)
                for tag in leftovers:
                    unmapped[tag] = unmapped.get(tag, 0) + 1
            scan_to_pep[scan] = pep

    if unmapped:
        print(f"  WARNING: {sum(unmapped.values())} peptides contain "
              f"PEAKS tags with no Casanovo translation:")
        for tag, n in sorted(unmapped.items(), key=lambda kv: -kv[1]):
            print(f"           {tag}  x{n}")
        print(f"           Add an entry to PEAKS_TO_CASANOVO if Casanovo "
              f"should score these.")
    return scan_to_pep


def parse_scan_from_title(title_line: str) -> int | None:
    """TITLE=<base>.<MS1_precursor>.<MS2_scan>.<charge> -> MS2_scan.

    MaxQuant's 'Scan number' is the MS2 scan, which lives in the middle
    group of the trailing three-number suffix.
    """
    m = TITLE_SCAN_RE.search(title_line)
    return int(m.group(2)) if m else None


def annotate(mgf_in: str, mgf_out: str, scan_to_pep: dict[int, str],
             keep_unlabelled: bool) -> tuple[int, int, int]:
    total = labelled = no_title_match = 0
    os.makedirs(os.path.dirname(mgf_out) or ".", exist_ok=True)

    with open(mgf_in) as fin, open(mgf_out, "w") as fout:
        block: list[str] = []
        in_block = False
        block_seq: str | None = None
        block_scan: int | None = None

        for line in fin:
            if line.startswith("BEGIN IONS"):
                in_block = True
                block = [line]
                block_seq = None
                block_scan = None
                continue

            if not in_block:
                fout.write(line)
                continue

            block.append(line)

            if line.startswith("TITLE="):
                block_scan = parse_scan_from_title(line)
                if block_scan is None:
                    no_title_match += 1
                elif block_scan in scan_to_pep:
                    block_seq = scan_to_pep[block_scan]

            if line.startswith("END IONS"):
                total += 1
                if block_seq is not None:
                    labelled += 1
                    # Insert SEQ= immediately after TITLE= (or at top of
                    # header if no TITLE was found).
                    out_lines: list[str] = []
                    inserted = False
                    for bl in block:
                        out_lines.append(bl)
                        if not inserted and bl.startswith("TITLE="):
                            out_lines.append(f"SEQ={block_seq}\n")
                            inserted = True
                    if not inserted:
                        out_lines.insert(1, f"SEQ={block_seq}\n")
                    fout.writelines(out_lines)
                elif keep_unlabelled:
                    fout.writelines(block)
                in_block = False

    return total, labelled, no_title_match


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mgf", required=True, help="input MGF")
    ap.add_argument("--groundtruth", required=True, help="ground-truth CSV (Scan, Peptide columns)")
    ap.add_argument("--output", required=True, help="output annotated MGF")
    ap.add_argument("--keep-unlabelled", action="store_true",
                    help="retain spectra without a ground-truth label "
                         "(default: drop them)")
    ap.add_argument("--notation", choices=["peaks", "casanovo"],
                    default="peaks",
                    help="SEQ= notation: peaks for InstaNovo/NovoBoard "
                         "(default), casanovo for `casanovo evaluate`")
    args = ap.parse_args()

    print(f"[1/3] Loading ground truth: {args.groundtruth}  "
          f"(notation={args.notation})")
    scan_to_pep = load_groundtruth(args.groundtruth, args.notation)
    print(f"      {len(scan_to_pep)} labelled scans")

    print(f"[2/3] Annotating {args.mgf} -> {args.output}")
    total, labelled, no_match = annotate(
        args.mgf, args.output, scan_to_pep, args.keep_unlabelled
    )

    print(f"[3/3] Done")
    print(f"      spectra in MGF        : {total}")
    print(f"      labelled (SEQ= added) : {labelled}")
    print(f"      unlabelled            : {total - labelled} "
          f"({'kept' if args.keep_unlabelled else 'dropped'})")
    if no_match:
        print(f"      TITLEs without a parseable scan: {no_match}")
    coverage = (labelled / len(scan_to_pep) * 100) if scan_to_pep else 0
    print(f"      ground-truth coverage : {labelled}/{len(scan_to_pep)} "
          f"({coverage:.1f}%)")


if __name__ == "__main__":
    main()
