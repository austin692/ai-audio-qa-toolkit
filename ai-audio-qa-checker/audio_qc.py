import os
import numpy as np
import soundfile as sf
import csv
import pyloudnorm as pyln
from scipy.signal import butter, sosfilt


folder = "."

def measure_noise_floor(audio, sr, cutoff=400):
    sos = butter(4, cutoff, btype="highpass", fs=sr, output="sos")
    filtered = sosfilt(sos, audio)
    chunk = int(sr * 0.1)
    rms_values = [np.sqrt(np.mean(filtered[i:i + chunk] ** 2)) for i in range(0, len(filtered) - chunk + 1, chunk)]
    return float(np.percentile(rms_values, 10))

# QA Checker
rows = []
for name in os.listdir(folder):
    if name.endswith(".wav"):
        audio, sr = sf.read(name)
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))

        noise_floor = measure_noise_floor(audio, sr)

        flags = []
        if peak >= 0.99:
            flags.append("clipping")
        if loudness < -19:
            flags.append("too quiet")
        if loudness > -14:
            flags.append("too loud")
        if noise_floor > 0.007:
            flags.append("noisy")

        verdict = "PASS" if not flags else "FLAG: " + ", ".join(flags)
        rows.append([name, round(peak, 2), round(rms, 2), round(noise_floor, 4), round(loudness, 1), verdict])
        print(f"{name} - peak {peak:.2f} - loudness {loudness:.1f} - floor {noise_floor:.4f} - {verdict}")

# Write results to CSV
with open("qc_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["File", "Peak", "RMS", "Floor", "Loudness", "Verdict"])
    writer.writerows(rows)