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
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src]
    if not has_audio(src):
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-ar", "48000", "-ac", "2"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    run(cmd + [dst])


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
        norm.append(d)
    total_clip = sum(duration(n) for n in norm)
    if total_clip < story_len:
        print(f"warning: clips are {total_clip:.1f}s but VO needs {story_len:.1f}s; "
              "the video will end early", file=sys.stderr)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(n)}'\n" for n in norm)
    story = os.path.join(tmp, "story.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-t", f"{story_len:.3f}", "-c", "copy", story])

    # 2. Captions.
    with open(script_path) as f:
        words = parse_script(f.read())
    caps = chunk_captions(words, vo_len)
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

    print(f"Done: {final} ({duration(final):.1f}s)")


if __name__ == "__main__":
    main()
