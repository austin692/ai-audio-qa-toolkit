import os
import numpy as np
import soundfile as sf
import csv

folder = "."

# QA Checker
rows = []
for name in os.listdir(folder):
    if name.endswith(".wav"):
        audio, sr = sf.read(name)
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
        if rms < 0.05:
            flags.append("too quiet")
        if rms > 0.5:
            flags.append("too loud")
        if noise_floor > 0.01:
            flags.append("noisy")

        verdict = "PASS" if not flags else "FLAG: " + ", ".join(flags)
        rows.append([name, round(peak, 2), round(rms, 2), round(noise_floor, 4), verdict])
        print(f"{name} - peak {peak:.2f} - rms {rms:.2f} - floor {noise_floor:.4f} - {verdict}")

# Write results to CSV
with open("qc_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["File", "Peak", "RMS", "Floor", "Verdict"])
    writer.writerows(rows)