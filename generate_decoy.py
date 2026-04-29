"""
Generate decoy MGFs from target MGFs using NovoBoard's 'random' peak sampling.
Replicates cell 4 of NovoBoard's notebook.

Usage: python generate_decoys.py input.mgf output.mgf [sampling_rate]
Default sampling_rate = 0.5
"""
import sys
import re
import random
import numpy as np


def collect_peak_distribution(mgf_path):
    """Collect all peaks from the MGF for noise sampling."""
    peaks_distr = []
    with open(mgf_path) as f:
        for line in f:
            if line and line[0].isdigit():
                parts = re.split(r' |\r|\n', line)
                if len(parts) >= 2:
                    try:
                        peaks_distr.append([float(parts[0]), float(parts[1])])
                    except ValueError:
                        pass
    return peaks_distr


def generate_decoy(input_mgf, output_mgf, sampling_rate=0.5):
    print(f"Generating decoy: {input_mgf} -> {output_mgf}")
    print(f"  Sampling rate: {sampling_rate} (keep {int(sampling_rate*100)}% of peaks)")
    
    print("  Collecting peak distribution...")
    peaks_distr = collect_peak_distribution(input_mgf)
    print(f"  Total peaks in distribution: {len(peaks_distr)}")
    
    n_spectra = 0
    sampling_peaks_distr = []
    noise_peaks_distr = []
    
    with open(input_mgf, 'r') as f_in, open(output_mgf, 'w') as f_out:
        while True:
            line = f_in.readline()
            if not line:  # EOF
                break
            if line == '\n':
                continue
            
            peak_list = []
            
            # Process spectrum block
            while not "END IONS" in line:
                # Header line
                if 'BEGIN IONS' in line or '=' in line:
                    f_out.write(line)
                    line = f_in.readline()
                    continue
                # Peak line
                parts = re.split(r' |\r|\n', line)
                if len(parts) >= 2:
                    try:
                        peak_list.append([float(parts[0]), float(parts[1])])
                    except ValueError:
                        pass
                line = f_in.readline()
            
            num_peaks = len(peak_list)
            num_sampling = int(num_peaks * sampling_rate)
            num_noise = num_peaks - num_sampling
            
            # Match notebook behavior: seed inside loop
            random.seed(99)
            np.random.seed(99)
            
            # Random peak sampling
            sampling_peaks = random.sample(peak_list, num_sampling) if num_sampling > 0 else []
            noise_peaks = random.sample(peaks_distr, num_noise) if num_noise > 0 else []
            
            sampling_peaks_distr += sampling_peaks
            noise_peaks_distr += noise_peaks
            
            # Write peaks sorted by m/z
            sorted_peaks = sorted(sampling_peaks + noise_peaks, key=lambda x: x[0])
            for x, y in sorted_peaks:
                f_out.write(f"{x:.5f} {y:.5f}\n")
            
            f_out.write(line)  # "END IONS" line
            blank = f_in.readline()
            if blank:
                f_out.write(blank)
            
            n_spectra += 1
    
    print(f"  Wrote {n_spectra} decoy spectra")
    print(f"  Sampled peaks: {len(sampling_peaks_distr)}")
    print(f"  Noise peaks: {len(noise_peaks_distr)}")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python generate_decoys.py input.mgf output.mgf [sampling_rate]')
        sys.exit(1)
    
    rate = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    generate_decoy(sys.argv[1], sys.argv[2], rate)