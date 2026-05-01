"""
split_annotated_mgf.py

Peptide-level random split of an annotated MGF (one with SEQ= lines)
into train and val MGFs. All spectra for a given peptide land on the
same side — no peptide leakage between train and val.

The split ratio is targeted on the spectrum level, not the peptide
level (since peptide multiplicities vary). The actual split may
deviate from the target by 1–2 percentage points.

Usage:
    python split_annotated_mgf.py \\
        --input  data_mgf_annotated/ecoli/Ecoli_EV_1.casanovo.annotated.mgf \\
        --train-out data_mgf_annotated/ecoli/Ecoli_EV_1.train.casanovo.mgf \\
        --val-out   data_mgf_annotated/ecoli/Ecoli_EV_1.val.casanovo.mgf \\
        --train-ratio 0.85 \\
        --seed 42
"""
import argparse
import random
from collections import defaultdict
from pathlib import Path


def parse_blocks(mgf_path: Path):
    """Yield (peptide, full_block_text) tuples from an annotated MGF.

    Spectra without a SEQ= line are skipped (we can't put them in a
    labelled split — they belong in inference, not training).
    """
    with mgf_path.open() as f:
        block: list[str] = []
        seq: str | None = None
        in_block = False
        for line in f:
            if line.startswith("BEGIN IONS"):
                in_block = True
                block = [line]
                seq = None
            elif line.startswith("END IONS"):
                block.append(line)
                if seq is not None:
                    yield seq, "".join(block)
                in_block = False
            elif in_block:
                block.append(line)
                if line.startswith("SEQ="):
                    seq = line.split("=", 1)[1].strip()


def split_by_peptide(blocks_by_peptide: dict[str, list[str]],
                     train_ratio: float, seed: int):
    rng = random.Random(seed)
    peptides = list(blocks_by_peptide.keys())
    rng.shuffle(peptides)

    total_spectra = sum(len(v) for v in blocks_by_peptide.values())
    target_train = int(total_spectra * train_ratio)

    train_blocks: list[str] = []
    val_blocks: list[str] = []
    train_peps: set[str] = set()
    val_peps: set[str] = set()

    for pep in peptides:
        spectra = blocks_by_peptide[pep]
        if len(train_blocks) < target_train:
            train_blocks.extend(spectra)
            train_peps.add(pep)
        else:
            val_blocks.extend(spectra)
            val_peps.add(pep)

    return train_blocks, val_blocks, train_peps, val_peps


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--train-out", required=True, type=Path)
    ap.add_argument("--val-out", required=True, type=Path)
    ap.add_argument("--train-ratio", type=float, default=0.85,
                    help="target spectrum-level fraction for train (default 0.85)")
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed (default 42)")
    args = ap.parse_args()

    print(f"Reading {args.input}")
    blocks_by_peptide: dict[str, list[str]] = defaultdict(list)
    for pep, block in parse_blocks(args.input):
        blocks_by_peptide[pep].append(block)
    n_spectra = sum(len(v) for v in blocks_by_peptide.values())
    n_unique = len(blocks_by_peptide)
    print(f"  {n_spectra} labelled spectra, {n_unique} unique peptides")

    train_blocks, val_blocks, train_peps, val_peps = split_by_peptide(
        blocks_by_peptide, args.train_ratio, args.seed
    )

    overlap = train_peps & val_peps
    assert not overlap, f"BUG: peptide overlap between train and val: {overlap}"

    args.train_out.parent.mkdir(parents=True, exist_ok=True)
    args.val_out.parent.mkdir(parents=True, exist_ok=True)
    args.train_out.write_text("".join(train_blocks))
    args.val_out.write_text("".join(val_blocks))

    print(f"\nTrain: {len(train_blocks)} spectra "
          f"({len(train_blocks) / n_spectra * 100:.1f}%), "
          f"{len(train_peps)} unique peptides  →  {args.train_out}")
    print(f"Val:   {len(val_blocks)} spectra "
          f"({len(val_blocks) / n_spectra * 100:.1f}%), "
          f"{len(val_peps)} unique peptides  →  {args.val_out}")
    print(f"Overlap: 0 peptides (guaranteed by peptide-level split)")
    print(f"Seed: {args.seed} (re-run with same seed reproduces this split)")


if __name__ == "__main__":
    main()
