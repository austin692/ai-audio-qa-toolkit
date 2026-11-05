import os
import numpy as np
import soundfile as sf
import csv
import pyloudnorm as pyln


folder = "."

# QA Checker
rows = []
for name in os.listdir(folder):
    if name.endswith(".wav"):
        audio, sr = sf.read(name)
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))

        chunk = int(sr * 0.1)
        levels = []
        for start in range(0, len(audio), chunk):
            piece = audio[start:start + chunk]
            levels.append(np.sqrt(np.mean(piece ** 2)))
        noise_floor = np.percentile(levels, 10)

        flags = []
        if peak >= 0.99:
            flags.append("clipping")
        if loudness < -18:
            flags.append("too quiet")
        if loudness > -14:
            flags.append("too loud")
        if noise_floor > 0.01:
            flags.append("noisy")

        verdict = "PASS" if not flags else "FLAG: " + ", ".join(flags)
        rows.append([name, round(peak, 2), round(rms, 2), round(noise_floor, 4), round(loudness, 1), verdict])
        print(f"{name} - peak {peak:.2f} - loudness {loudness:.1f} - floor {noise_floor:.4f} - {verdict}")

# Write results to CSV
with open("qc_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["File", "Peak", "RMS", "Floor", "Loudness", "Verdict"])
    writer.writerows(rows)