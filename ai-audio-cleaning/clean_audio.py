import os
import subprocess
import sys
import csv
import glob
import shutil
import soundfile as sf

# Settings - change these to taste
TARGET_SR = 16000       # target sample rate, 16000 for Whisper-native
TARGET_LUFS = -16       # target loudness, podcast standard
DENOISE_NR = 20         # afftdn strength, 12 is gentler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, "..", "ai-audio-qa-checker", "test-episodes")
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "cleaned-episodes")
CHECKER = os.path.join(SCRIPT_DIR, "..", "ai-audio-qa-checker", "audio_qc.py")

# Wipe the output folder so each run starts clean (files only, keep the folder)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
for name in os.listdir(OUTPUT_FOLDER):
    path = os.path.join(OUTPUT_FOLDER, name)
    if os.path.isfile(path):
        os.remove(path)

# Read the checker's results
results = {}
csv_path = os.path.join(INPUT_FOLDER, "qc_results.csv")
if os.path.exists(csv_path):
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            results[row["File"]] = row
else:
    print("No qc_results.csv found. Run the checker first.")
    raise SystemExit

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for input_path in sorted(glob.glob(os.path.join(INPUT_FOLDER, "*.wav"))):
    name = os.path.basename(input_path)
    output_path = os.path.join(OUTPUT_FOLDER, name)
    info = sf.info(input_path)
    row = results.get(name, {})
    verdict = row.get("Verdict", "")
    loudness = float(row.get("Loudness", -99)) if row.get("Loudness") else -99

    needs_rate = info.samplerate != TARGET_SR
    needs_mono = info.channels > 1
    needs_denoise = "noisy" in verdict
    needs_level = loudness < -19 or loudness > -14

    if not (needs_rate or needs_mono or needs_denoise or needs_level):
        print(f"{name} - already clean, copying as-is")
        shutil.copy2(input_path, output_path)
        continue

    filters = []
    if needs_rate:
        filters.append(f"aresample={TARGET_SR}")
    if needs_mono:
        filters.append("pan=mono|c0=0.5*c0+0.5*c1")
    if needs_denoise:
        filters.append(f"afftdn=nr={DENOISE_NR}")
    if needs_level:
        filters.append(f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11")
        filters.append(f"aresample={TARGET_SR}")

    cmd = ["ffmpeg", "-y", "-i", input_path]
    if filters:
        cmd += ["-af", ",".join(filters)]
    if needs_mono:
        cmd += ["-ac", "1"]
    cmd += [output_path]

    print(f"{name} - fixing: " + ", ".join(
        x for x, needed in [
            ("sample rate", needs_rate),
            ("mono", needs_mono),
            ("denoise", needs_denoise),
            ("level", needs_level),
        ] if needed
    ))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"{name} - FAILED, skipping")

print("Cleaning done. Re-checking the cleaned files...")
try:
    subprocess.run([sys.executable, CHECKER], cwd=OUTPUT_FOLDER, check=True)
except subprocess.CalledProcessError:
    print("Re-check failed. Run the checker yourself from the cleaned-episodes folder.")