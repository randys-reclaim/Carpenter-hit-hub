"""Split one continuous voice-over recording into one clip per caption line.

Read the voiceover/*.txt script top to bottom with a short pause (about a
second) between lines, then:

  python split_recording.py ../episodes/001-doorbell my-recording.m4a

The recording is cut at the longest pauses, exactly as many cuts as there
are lines, and saved as audio/0001.mp3, 0002.mp3... Then run
make_episode.py (or assemble.py) to build the narrated video.
"""
import json, re, subprocess, sys
from pathlib import Path

def silences(path, noise="-35dB", min_len=0.35):
    r = subprocess.run(["ffmpeg", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={min_len}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(starts, ends))

def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def run(ep_dir, recording):
    ep_dir, recording = Path(ep_dir), Path(recording)
    lines = json.loads((ep_dir / "timeline.json").read_text())["lines"]
    total = duration(recording)
    gaps = [(s, e) for s, e in silences(recording) if s > 0.2 and e < total - 0.2]
    need = len(lines) - 1
    if len(gaps) < need:
        sys.exit(f"Found {len(gaps)} pauses but need {need}. Re-record with a clear pause between lines, "
                 f"or check the recording isn't noisy.")
    cuts = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:need])
    bounds, start = [], 0.0
    for s, e in cuts:
        bounds.append((start, s + 0.08))
        start = e - 0.08
    bounds.append((start, total))
    out = ep_dir / "audio"
    out.mkdir(exist_ok=True)
    for ln, (a, b) in zip(lines, bounds):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(recording),
                        "-af", "silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=-1:stop_duration=0.3:stop_threshold=-40dB",
                        "-ac", "1", "-ar", "44100", "-b:a", "160k", str(out / f'{ln["line"]:04d}.mp3')], check=True)
    print(f"split into {len(lines)} clips in {out}")
    for ln, (a, b) in list(zip(lines, bounds))[:3] + list(zip(lines, bounds))[-2:]:
        print(f"  {ln['line']:4d}  {a:7.2f}-{b:7.2f}s  {ln['text'][:50]}")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
