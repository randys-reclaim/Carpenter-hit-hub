"""Turn rendered frames (+ narration, if present) into finished videos.

  video-16x9.mp4   the full episode for YouTube
  short-9x16.mp4   a vertical teaser under 60 s (cold open + Rule 1) for
                   Shorts, TikTok and Reels, ending on a "full notice" card

Each cue gets a slow push-in; captions change on every narration line.
Without narration the soundtrack is quiet room tone, timed from estimates.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

FPS = 30

def pause_after(raw):
    r = raw.rstrip()
    return 1.0 if r.endswith("//") else 0.5 if r.endswith("/") else 0.3

def timings(tl):
    for ln in tl["lines"]:
        ln["dur"] = round(ln["audio_dur"] + pause_after(ln["raw"]), 3) if "audio_dur" in ln else ln["est"]
    return tl["lines"]

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)

def cue_clip(ep, items, out, size):
    """items: [(image, seconds)] for one cue -> mp4 with a slow push-in."""
    w, h = size
    total = sum(d for _, d in items)
    frames = max(1, round(total * FPS))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for img, d in items:
            f.write(f"file '{(ep / img).resolve()}'\nduration {d}\n")
        f.write(f"file '{(ep / items[-1][0]).resolve()}'\n")
        lst = f.name
    zoom = f"1+0.035*on/{frames}"
    vf = (f"fps={FPS},scale={w*2}:{h*2}:flags=lanczos,"
          f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={FPS},format=yuv420p")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", vf, "-frames:v", str(frames),
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(FPS), str(out))
    Path(lst).unlink()
    return frames / FPS

def soundtrack(ep, lines, total, out):
    """Narration (if any) laid over low room tone."""
    tone = f"anoisesrc=color=brown:amplitude=0.035:duration={total},lowpass=f=180,volume=0.6"
    if not all("audio" in l for l in lines):
        ff("-f", "lavfi", "-i", tone, "-c:a", "aac", "-b:a", "160k", str(out))
        return
    inputs, parts = [], []
    for i, l in enumerate(lines):
        inputs += ["-i", str(ep / l["audio"])]
        pad = max(0.0, l["dur"] - l["audio_dur"])
        parts.append(f"[{i}:a]aformat=sample_rates=44100:channel_layouts=mono,apad=pad_dur={pad}[a{i}]")
    n = len(lines)
    graph = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[voice];"
    graph += f"{tone}[tone];[voice][tone]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5[out]"
    ff(*inputs, "-filter_complex", graph, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out))

def build(ep, lines, key, size, out_name, tail=None):
    ep = Path(ep)
    work = ep / "work"
    work.mkdir(exist_ok=True)
    cues, order = {}, []
    for l in lines:
        if l["cue"] not in cues:
            cues[l["cue"]] = []
            order.append(l["cue"])
        cues[l["cue"]].append((l[key], l["dur"]))
    if tail:
        cues["end"] = [tail]
        order.append("end")
    clips, total = [], 0.0
    for c in order:
        p = work / f"{out_name}-{c}.mp4"
        total += cue_clip(ep, cues[c], p, size)
        clips.append(p)
    lst = work / f"{out_name}.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in clips))
    silent = work / f"{out_name}-video.mp4"
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent))
    audio = work / f"{out_name}.m4a"
    soundtrack(ep, lines, total, audio)
    final = ep / f"{out_name}.mp4"
    ff("-i", str(silent), "-i", str(audio), "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(final))
    for p in clips + [lst, silent, audio]:
        p.unlink()
    print(f"  {final.name}: {int(total//60)}:{int(total%60):02d}")
    return final

def run(ep, which=("full", "short")):
    ep = Path(ep)
    tl = json.loads((ep / "timeline.json").read_text())
    lines = timings(tl)
    if "full" in which:
        build(ep, lines, "img", (1920, 1080), "video-16x9")
    if "short" in which:
        picked, t = [], 0.0
        for l in lines:
            if t + l["dur"] > 54 or (picked and l["scene"].startswith("RULE 2")):
                break
            picked.append(l)
            t += l["dur"]
        build(ep, picked, "vimg", (1080, 1920), "short-9x16", tail=("frames/9x16/end.png", 3.0))

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2:] or ("full", "short"))
