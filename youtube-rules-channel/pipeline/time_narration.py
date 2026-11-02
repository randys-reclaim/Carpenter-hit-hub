"""Time the pictures to one continuous narration track (no cutting).

  python time_narration.py ../episodes/001-doorbell narration.mp3

Finds when every script line starts in the recording (Whisper word timings,
matched to the script, so ad-libs or a repeated line don't throw it off), writes each line's "start" into
timeline.json and copies the recording to <episode>/narration.mp3.
assemble.py then plays the recording untouched and switches each picture and
caption on at its line's start, so the voice can't drift ahead of the screen.
"""
import difflib, json, re, shutil, subprocess, sys
from pathlib import Path
import numpy as np

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("’", "'"))

def heard_words(recording):
    """Word timings from Whisper (base.en, CPU). Audio is decoded with ffmpeg."""
    from faster_whisper import WhisperModel
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(recording), "-f", "s16le", "-ar", "16000", "-ac", "1", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, _ = WhisperModel("base.en", device="cpu", compute_type="int8").transcribe(audio, word_timestamps=True)
    return [(norm(w.word), float(w.start), float(w.end)) for s in segs for w in s.words if norm(w.word)]

def run(ep_dir, recording):
    ep_dir = Path(ep_dir)
    tl = json.loads((ep_dir / "timeline.json").read_text())
    lines = tl["lines"]
    heard = heard_words(recording)
    script, owner = [], []
    for k, ln in enumerate(lines):
        for w in re.findall(r"[A-Za-z0-9'’]+", ln["text"]):
            if norm(w):
                script.append(norm(w)); owner.append(k)
    sm = difflib.SequenceMatcher(None, script, [h[0] for h in heard], autojunk=False)
    times = {}
    for a, b, n in sm.get_matching_blocks():
        for j in range(n):
            times[a + j] = heard[b + j]
    matched = len(times) / max(1, len(script))
    if matched < 0.8:
        sys.exit(f"Only {matched:.0%} of the script's words were found in the recording. Is it the right recording?")
    for k, ln in enumerate(lines):
        idx = [i for i, o in enumerate(owner) if o == k and i in times]
        if idx:
            ln["start"], ln["end"] = round(times[idx[0]][1], 3), round(times[idx[-1]][2], 3)
    for k, ln in enumerate(lines):  # lines with no matched words sit between their neighbours
        if "start" not in ln:
            prev = lines[k - 1]["end"] if k else 0.0
            ln["start"] = ln["end"] = prev
    for k in range(1, len(lines)):  # keep the order strictly increasing
        lines[k]["start"] = max(lines[k]["start"], lines[k - 1]["start"] + 0.1)
    for ln in lines:
        ln.pop("audio", None); ln.pop("audio_dur", None)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(recording)],
                               capture_output=True, text=True).stdout)
    tl["narration"] = {"file": "narration.mp3", "duration": round(dur, 3)}
    if Path(recording).resolve() != (ep_dir / "narration.mp3").resolve():
        shutil.copyfile(recording, ep_dir / "narration.mp3")
    (ep_dir / "timeline.json").write_text(json.dumps(tl, indent=1))
    print(f"timed {len(lines)} lines to {dur:.1f}s of narration ({matched:.0%} of script words heard)")
    for ln in lines[:3] + lines[-3:]:
        print(f"  {ln['line']:4d}  {ln['start']:7.2f}s  {ln['text'][:55]}")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
