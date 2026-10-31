"""Cut a narration recording into one clip per caption line by matching the
words, not the pauses. Use this for ElevenLabs website downloads or any take
without clear pauses between lines.

  python align_recording.py ../episodes/001-doorbell narration.mp3 [part2.mp3 ...]

Uses pocketsphinx forced alignment (its English model ships inside the pip
package, so no downloads): given the exact script, it finds when every word
is spoken. Writes audio/0001.mp3, 0002.mp3... for assemble.py.
"""
import json, re, subprocess, sys
from pathlib import Path
from pocketsphinx import Decoder

RATE = 16000
SPELL = {"3:12": "three twelve", "3:33": "three thirty three", "6:12": "six twelve", "6:01": "six oh one",
         "a.m.": "a m", "déjà": "deja", "kettle's": "kettles", "peephole": "peep hole", "11,402": "eleven thousand four hundred two",
         "25:00": "twenty five hundred", "4:00": "four", "$2.00": "two dollars"}

def words(text, vocab):
    t = text.lower()
    for k, v in SPELL.items():
        t = t.replace(k, v)
    out = []
    for w in re.findall(r"[a-z0-9']+", t):
        w = w.strip("'")
        if not w:
            continue
        if w not in vocab and w.endswith("'s") and w[:-2] in vocab:
            w = w[:-2]
        if w not in vocab:
            w = re.sub(r"'", "", w)
        if w in vocab:
            out.append(w)
    return out

def load_audio(paths, out_wav):
    ins = sum((["-i", str(p)] for p in paths), [])
    n = len(paths)
    graph = "".join(f"[{i}:a]aformat=sample_rates={RATE}:channel_layouts=mono,apad=pad_dur=0.8[p{i}];" for i in range(n))
    graph += "".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "[a]", "-ar", str(RATE), "-ac", "1", str(out_wav)], check=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out_wav), "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-"], capture_output=True, check=True).stdout
    return raw

def align(raw, word_list):
    dec = Decoder(samprate=RATE, loglevel="FATAL")
    dec.set_align_text(" ".join(word_list))
    dec.start_utt()
    dec.process_raw(raw, full_utt=True)
    dec.end_utt()
    segs = [(s.word.split("(")[0], s.start_frame / 100, (s.end_frame + 1) / 100) for s in dec.seg()]
    return [s for s in segs if s[0] not in ("<s>", "</s>", "<sil>", "[NOISE]") and not s[0].startswith("+")]

def run(ep_dir, *recordings):
    ep_dir = Path(ep_dir)
    import pocketsphinx
    vocab = {l.split()[0].split("(")[0] for l in open(Path(pocketsphinx.get_model_path()) / "en-us/cmudict-en-us.dict")}
    lines = json.loads((ep_dir / "timeline.json").read_text())["lines"]
    per_line = [words(l["text"], vocab) for l in lines]
    wav = ep_dir / "narration-16k.wav"
    raw = load_audio(recordings, wav)
    segs = align(raw, [w for ws in per_line for w in ws])
    total_words = sum(len(ws) for ws in per_line)
    if len(segs) != total_words:
        sys.exit(f"Alignment matched {len(segs)} of {total_words} words. Check the recording reads the whole script in order.")
    # word timings -> line start/end
    spans, i = [], 0
    for ws in per_line:
        spans.append((segs[i][1], segs[i + len(ws) - 1][2]))
        i += len(ws)
    src = recordings[0] if len(recordings) == 1 else wav
    out = ep_dir / "audio"
    out.mkdir(exist_ok=True)
    for k, (ln, (a, b)) in enumerate(zip(lines, spans)):
        nxt = spans[k + 1][0] if k + 1 < len(spans) else b + 0.5
        a2, b2 = max(0, a - 0.06), min(b + 0.18, nxt - 0.02)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a2:.3f}", "-to", f"{b2:.3f}", "-i", str(src),
                        "-af", "afade=t=in:d=0.02,areverse,afade=t=in:d=0.04,areverse",
                        "-ac", "1", "-ar", "44100", "-b:a", "160k", str(out / f'{ln["line"]:04d}.mp3')], check=True)
    wav.unlink(missing_ok=True)
    print(f"aligned {total_words} words into {len(lines)} clips in {out}")
    for ln, (a, b) in list(zip(lines, spans))[:3] + list(zip(lines, spans))[-3:]:
        print(f"  {ln['line']:4d}  {a:7.2f}-{b:7.2f}s  {ln['text'][:55]}")

if __name__ == "__main__":
    run(sys.argv[1], *sys.argv[2:])
