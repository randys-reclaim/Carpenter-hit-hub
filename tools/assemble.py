#!/usr/bin/env python3
"""Assemble a Heartwarming Holly short from generated clips + a voiceover.

Usage:
  python3 tools/assemble.py <project_dir> [--reveal real.mp4] [--reveal-seconds 3]
                            [--watermark "HEARTWARMING HOLLY"] [--clip-volume 0.15]

<project_dir> must contain:
  clips/      generated scene clips, sorted by name (01.mp4, 02.mp4, ...)
  vo.mp3      your voiceover (any audio format ffmpeg reads: vo.*)
  script.txt  the VO script. Mark caption keywords:
                !word  -> red   (bad / tension)
                +word  -> teal  (good / payoff)
              Example:  For four years his only job was handing out !towels.

Writes <project_dir>/out/:
  final.mp4     1080x1920, 30fps, captions burned in, watermark, optional reveal
  captions.srt  plain captions to import into CapCut if you'd rather edit there
  captions.ass  styled captions used for the burn-in

Caption timing is estimated from word length across the VO duration. It is close,
not perfect. Nudge the .srt in CapCut if a caption lands early or late.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

W, H, FPS = 1080, 1920, 30
IMAGE_SECONDS = 2.5  # how long a still image in clips/ is held
WORDS_PER_CAPTION = 3
RED = "&H003B3BFF&"    # ASS colors are &HBBGGRR&
TEAL = "&H00E6E61E&"
WHITE = "&H00FFFFFF&"


def run(cmd):
    print("+", " ".join(cmd[:6]), "...", file=sys.stderr)
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        check=True, capture_output=True, text=True).stdout.strip()
    return float(out)


def has_audio(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return bool(out)


def parse_script(text):
    """Return list of (display_word, color) tuples."""
    words = []
    for raw in text.split():
        color = WHITE
        if raw.startswith("!"):
            color, raw = RED, raw[1:]
        elif raw.startswith("+"):
            color, raw = TEAL, raw[1:]
        if raw:
            words.append((raw.upper(), color))
    return words


def speech_intervals(vo_path, min_silence=0.18, noise_db=-35):
    """Return [(start, end), ...] where the voiceover is actually speaking."""
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", vo_path, "-af",
         f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    total = duration(vo_path)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    speech, t = [], 0.0
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s - t > 0.05:
            speech.append((t, s))
        t = e
    if total - t > 0.05:
        speech.append((t, total))
    return speech or [(0.0, total)]


def map_to_speech(frac, speech):
    """Map a 0..1 fraction of the script onto real speaking time (skipping pauses)."""
    talk = sum(e - s for s, e in speech)
    target = frac * talk
    for s, e in speech:
        if target <= e - s:
            return s + target
        target -= e - s
    return speech[-1][1]


def chunk_captions_speech(words, speech):
    """Like chunk_captions, but timed to where the voice is actually talking."""
    caps = chunk_captions(words, 1.0)  # fractions of the script
    return [(map_to_speech(a, speech), map_to_speech(b, speech), g) for a, b, g in caps]


def norm_word(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def captions_from_word_times(words, word_times):
    """Use the script's exact words, timed by a transcript's word timestamps.
    word_times: [[start, end, text], ...] from speech-to-text."""
    import difflib
    a = [norm_word(w) for w, _ in words]
    b = [norm_word(t[2]) for t in word_times]
    times = [None] * len(words)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            for k in range(i2 - i1):
                j = min(j1 + int(k * (j2 - j1) / max(1, i2 - i1)), j2 - 1)
                if j >= j1:
                    times[i1 + k] = (word_times[j][0], word_times[j][1])
    # fill gaps by interpolation
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(times)):
        if times[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            if prev is not None and nxt is not None:
                times[i] = (times[prev][1], times[nxt][0])
            elif prev is not None:
                times[i] = (times[prev][1], times[prev][1] + 0.3)
            else:
                times[i] = (0.0, times[nxt][0] if nxt is not None else 0.3)
    caps, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if len(cur) >= WORDS_PER_CAPTION or re.search(r"[.!?,:]$", w[0]):
            caps.append(cur)
            cur = []
    if cur:
        caps.append(cur)
    out = []
    for n, idx in enumerate(caps):
        start = times[idx[0]][0]
        end = caps[n + 1] and times[caps[n + 1][0]][0] if n + 1 < len(caps) else times[idx[-1]][1] + 0.4
        out.append((start, max(end, start + 0.25), [words[i] for i in idx]))
    return out


def chunk_captions(words, total_seconds):
    """Group words into captions and spread them across the VO by character weight.
    Sentence-ending punctuation forces a caption break."""
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= WORDS_PER_CAPTION or re.search(r"[.!?]$", w[0]):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    weights = [sum(len(w) + 1 for w, _ in g) + (4 if re.search(r"[.!?]$", g[-1][0]) else 0)
               for g in groups]
    scale = total_seconds / sum(weights)
    t, out = 0.0, []
    for g, wt in zip(groups, weights):
        out.append((t, t + wt * scale, g))
        t += wt * scale
    return out


def ts_srt(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def ts_ass(s):
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def write_captions(caps, out_dir):
    with open(os.path.join(out_dir, "captions.srt"), "w") as f:
        for i, (a, b, g) in enumerate(caps, 1):
            f.write(f"{i}\n{ts_srt(a)} --> {ts_srt(b)}\n{' '.join(w for w, _ in g)}\n\n")

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for a, b, g in caps:
        text = " ".join(f"{{\\c{c}}}{w}" for w, c in g)
        # quick pop-in: start at 80% scale, grow to 100% over 120ms
        lines.append(f"Dialogue: 0,{ts_ass(a)},{ts_ass(b)},Cap,,0,0,0,,"
                     f"{{\\fscx80\\fscy80\\t(0,120,\\fscx100\\fscy100)}}{text}")
    path = os.path.join(out_dir, "captions.ass")
    with open(path, "w") as f:
        f.write(header + "\n".join(lines) + "\n")
    return path


def normalize(src, dst, seconds=None):
    """Scale/crop any clip to 1080x1920 30fps with a stereo audio track."""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},setsar=1,format=yuv420p")
    is_image = src.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    if is_image:
        # Still image (e.g. a close-up of a note): hold it with a slow push-in.
        seconds = seconds or IMAGE_SECONDS
        vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
              f"zoompan=z='1+0.0015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")
        cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", src]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src]
    if is_image or not has_audio(src):
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-ar", "48000", "-ac", "2"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    run(cmd + [dst])


# Punch-in framings cycled through within each clip: (zoom, vertical focus 0=top..1=bottom).
# Wide -> close on faces (upper third) -> medium. Faking cuts this way lets one 8s
# generation read like 3-4 shots.
PUNCH_FRAMES = [(1.0, 0.5), (1.4, 0.3), (1.18, 0.4)]


def punch_in(src, dst, every, tmp_prefix):
    """Split a normalized clip into `every`-second chunks with alternating crops."""
    total = duration(src)
    n = max(1, round(total / every))
    seg = total / n
    parts = []
    for i in range(n):
        z, fy = PUNCH_FRAMES[i % len(PUNCH_FRAMES)]
        cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
        x, y = (W - cw) // 2, int((H - ch) * fy)
        part = f"{tmp_prefix}_p{i:02}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{i * seg:.3f}", "-t", f"{seg:.3f}",
             "-i", src, "-vf", f"crop={cw}:{ch}:{x}:{y},scale={W}:{H},setsar=1,format=yuv420p",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-c:a", "aac", "-ar", "48000", "-ac", "2", part])
        parts.append(part)
    lst = f"{tmp_prefix}_parts.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", dst])


def drift(src, dst, idx, amount=0.07):
    """Gentle camera motion: slow zoom in or out (alternating per clip) with a slight pan."""
    n = max(1, int(duration(src) * FPS))
    if idx % 2 == 0:
        z = f"1+{amount}*on/{n}"
    else:
        z = f"1+{amount}-{amount}*on/{n}"
    sway = "+1" if idx % 3 else "-1"
    x = f"iw/2-(iw/zoom/2){sway}*iw*0.02*on/{n}"
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
         f"zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "copy", dst])


def build_reveal(main_video, real_video, seconds, dst):
    """White flash, then frozen last frame of ours beside the real clip."""
    half_w, half_h = W // 2, H // 2
    last = dst + ".last.png"
    run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", main_video,
         "-frames:v", "1", "-update", "1", last])
    label = ("drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf:"
             "text='{t}':fontsize=64:fontcolor=white:borderw=4:bordercolor=black:"
             "x=(w-text_w)/2:y=h-140")
    fc = (
        f"[0:v]scale={half_w}:{half_h}:force_original_aspect_ratio=increase,crop={half_w}:{half_h},"
        f"{label.format(t='ANIMATED')}[a];"
        f"[1:v]scale={half_w}:{half_h}:force_original_aspect_ratio=increase,crop={half_w}:{half_h},"
        f"fps={FPS},{label.format(t='REAL')}[b];"
        f"[a][b]hstack=2,pad={W}:{H}:0:(oh-ih)/2:color=black,fps={FPS},setsar=1,format=yuv420p,"
        f"fade=t=in:st=0:d=0.35:color=white[v]"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{seconds}", "-i", last,
           "-t", f"{seconds}", "-i", real_video]
    if has_audio(real_video):
        cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "1:a"]
    else:
        cmd += ["-f", "lavfi", "-t", f"{seconds}", "-i", "anullsrc=r=48000:cl=stereo",
                "-filter_complex", fc, "-map", "[v]", "-map", "2:a"]
    run(cmd + ["-t", f"{seconds}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
               "-c:a", "aac", "-ar", "48000", "-ac", "2", dst])
    os.remove(last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--reveal", help="real viral clip to show side by side at the end")
    ap.add_argument("--reveal-seconds", type=float, default=3.0)
    ap.add_argument("--watermark", default="HEARTWARMING HOLLY")
    ap.add_argument("--clip-volume", type=float, default=0.15,
                    help="volume of the clips' own sound under the VO (0 = mute)")
    ap.add_argument("--punch", type=float, default=0,
                    help="fake a cut every N seconds inside each clip by switching "
                         "between wide/close/medium crops (try 2). 0 = off")
    ap.add_argument("--keep-all", action="store_true",
                    help="keep every clip even past the end of the VO (e.g. real-photo endings)")
    ap.add_argument("--drift", action="store_true",
                    help="gentle slow zoom in/out and slight pan on every clip")
    ap.add_argument("--logo", help="channel logo image to fade in over the final shot")
    ap.add_argument("--logo-seconds", type=float, default=2.8)
    a = ap.parse_args()

    proj = a.project
    clips = sorted(glob.glob(os.path.join(proj, "clips", "*")))
    vos = glob.glob(os.path.join(proj, "vo.*"))
    script_path = os.path.join(proj, "script.txt")
    if not clips or not vos or not os.path.exists(script_path):
        sys.exit("project needs clips/, vo.<ext>, and script.txt")
    vo = vos[0]
    out = os.path.join(proj, "out")
    tmp = os.path.join(out, "tmp")
    os.makedirs(tmp, exist_ok=True)

    vo_len = duration(vo)
    story_len = vo_len + 0.4  # small breath after the last word

    # 1. Normalize clips, then concatenate and trim to the VO length.
    norm = []
    for i, c in enumerate(clips):
        d = os.path.join(tmp, f"n{i:02}.mp4")
        normalize(c, d)
        if a.drift and not c.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            dd = os.path.join(tmp, f"dr{i:02}.mp4")
            drift(d, dd, i)
            d = dd
        if a.punch and not c.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            pd = os.path.join(tmp, f"pn{i:02}.mp4")
            punch_in(d, pd, a.punch, os.path.join(tmp, f"c{i:02}"))
            d = pd
        norm.append(d)
    total_clip = sum(duration(n) for n in norm)
    if total_clip < story_len:
        print(f"warning: clips are {total_clip:.1f}s but VO needs {story_len:.1f}s; "
              "the video will end early", file=sys.stderr)
    if a.keep_all:
        story_len = max(story_len, total_clip)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(n)}'\n" for n in norm)
    story = os.path.join(tmp, "story.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-t", f"{story_len:.3f}", "-c", "copy", story])

    # 2. Captions.
    with open(script_path) as f:
        words = parse_script(f.read())
    wt_path = os.path.join(proj, "words.json")
    if os.path.exists(wt_path):
        import json
        with open(wt_path) as f:
            caps = captions_from_word_times(words, json.load(f))
    else:
        caps = chunk_captions_speech(words, speech_intervals(vo))
    ass = write_captions(caps, out)

    # 3. Story with VO mixed over clip audio, captions, and watermark.
    wm = ("drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf:"
          f"text='{a.watermark}':fontsize=40:fontcolor=white@0.75:borderw=2:"
          "bordercolor=black@0.5:x=(w-text_w)/2:y=h-260")
    ass_esc = os.path.abspath(ass).replace(":", r"\:")
    story_final = os.path.join(tmp, "story_final.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", story, "-i", vo, "-filter_complex",
         f"[0:v]ass='{ass_esc}',{wm}[v];"
         f"[0:a]volume={a.clip_volume}[bg];[1:a]aresample=48000,apad[vo];"
         f"[bg][vo]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", story_final])

    final = os.path.join(out, "final.mp4")
    if a.reveal:
        reveal = os.path.join(tmp, "reveal.mp4")
        build_reveal(story_final, a.reveal, a.reveal_seconds, reveal)
        with open(lst, "w") as f:
            f.write(f"file '{os.path.abspath(story_final)}'\nfile '{os.path.abspath(reveal)}'\n")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", final])
    else:
        os.replace(story_final, final)

    if a.logo:
        # Fade the channel logo in over the last few seconds, lower third,
        # so it sits over the final shot instead of on a separate end card.
        start = max(0.0, duration(final) - a.logo_seconds)
        branded = os.path.join(tmp, "branded.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-i", final, "-loop", "1", "-framerate", str(FPS),
             "-i", a.logo, "-filter_complex",
             f"[1:v]scale={int(W * 1.2)}:-1,format=rgba,"
             f"fade=t=in:st={start:.2f}:d=0.4:alpha=1[lg];"
             f"[0:v][lg]overlay=(W-w)/2:{int(H * 0.56)}:enable='gte(t,{start:.2f})':shortest=1[v]",
             "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", branded])
        os.replace(branded, final)

    print(f"Done: {final} ({duration(final):.1f}s)")


if __name__ == "__main__":
    main()
