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
    if tl.get("narration"):  # one continuous recording: each line lasts until the next one starts
        ls = tl["lines"]
        for k, ln in enumerate(ls):
            a = 0.0 if k == 0 else ln["start"]
            b = ls[k + 1]["start"] if k + 1 < len(ls) else tl["narration"]["duration"] + 1.0
            ln["dur"] = round(max(0.1, b - a), 3)
        return ls
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
    # smooth push-in: rescale every frame with lanczos (sub-pixel), then crop the centre.
    # zoompan snaps to whole pixels, which made text shimmer and look soft.
    z = f"(1+0.035*n/{frames})"
    vf = (f"fps={FPS},scale=w='trunc({w}*{z}/2)*2':h='trunc({h}*{z}/2)*2':eval=frame:flags=lanczos+accurate_rnd+full_chroma_int,"
          f"crop={w}:{h},scale=out_color_matrix=bt709:out_range=tv:flags=lanczos,format=yuv420p")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", vf, "-frames:v", str(frames),
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "animation",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
       "-r", str(FPS), str(out))
    Path(lst).unlink()
    return frames / FPS

def soundtrack(ep, lines, total, out, narration=None, voice_end=None):
    """Narration (if any) laid over low room tone."""
    tone = f"anoisesrc=color=brown:amplitude=0.035:duration={total},lowpass=f=180,volume=0.6"
    if narration:  # continuous recording, played untouched from the start
        graph = (f"[0:a]aformat=sample_rates=44100:channel_layouts=mono,atrim=0:{voice_end or total},afade=t=out:st={max(0,(voice_end or total)-0.25)}:d=0.25,apad=whole_dur={total}[voice];"
                 f"{tone}[tone];[voice][tone]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5[out]")
        ff("-i", str(ep / narration), "-filter_complex", graph, "-map", "[out]", "-t", f"{total}", "-c:a", "aac", "-b:a", "192k", str(out))
        return
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

def build(ep, lines, key, size, out_name, tail=None, narration=None, voice_end=None):
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
    soundtrack(ep, lines, total, audio, narration, voice_end)
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
    nar = tl.get("narration", {}).get("file")
    if "full" in which:
        build(ep, lines, "img", (1920, 1080), "video-16x9", narration=nar)
    if "short" in which:
        picked, t = [], 0.0
        for l in lines:
            if t + l["dur"] > 54 or (picked and l["scene"].startswith("RULE 2")):
                break
            picked.append(l)
            t += l["dur"]
        # with a continuous recording, the short's voice stops where its last line ends; the end card plays over room tone
        build(ep, picked, "vimg", (1080, 1920), "short-9x16", tail=("frames/9x16/end.png", 3.0), narration=nar,
              voice_end=sum(l["dur"] for l in picked) if nar else None)

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2:] or ("full", "short"))
