"""
mgf_index.py
Build a mapping from MGF file index (0-based spectrum position) to the
original mzML MS2 scan number, parsed from the ProteoWizard TITLE
suffix '.<MS1_precursor>.<MS2_scan>.<charge>'.

Used by the per-tool converter scripts to translate position-based
prediction outputs (Casanovo's spectra_ref index, InstaNovo's
scan_number, Novor's id) into the actual mzML scan numbers that match
the ground-truth CSV (which carries MS2 scan numbers from MaxQuant).
"""
import re

# Three trailing numeric segments: <MS1_precursor>.<MS2_scan>.<charge>.
# We want the middle group — the MS2 scan number, which is what
# MaxQuant reports as "Scan number".
TITLE_SCAN_RE = re.compile(r"\.(\d+)\.(\d+)\.(\d+)\s*$")


def build_index_to_scan(mgf_path: str) -> dict[int, int]:
    """Return {file_index_0_based: mzml_scan_number} for every MS2 in the MGF.

    Indexing follows the order of BEGIN IONS blocks. A spectrum whose
    TITLE doesn't match the ProteoWizard suffix is skipped (no entry in
    the map), so callers should treat a missing key as a hard miss
    rather than a default-of-zero.
    """
    index_to_scan: dict[int, int] = {}
    idx = -1
    with open(mgf_path) as f:
        for line in f:
            if line.startswith("BEGIN IONS"):
                idx += 1
            elif line.startswith("TITLE="):
                m = TITLE_SCAN_RE.search(line)
                if m:
                    index_to_scan[idx] = int(m.group(2))
    return index_to_scan
