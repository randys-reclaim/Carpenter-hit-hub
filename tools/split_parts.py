#!/usr/bin/env python3
"""Cut a finished short into Part 1 (cliffhanger + call to action) and Part 2.

Usage:
  python3 tools/split_parts.py final.mp4 CUT_SECONDS out_dir
        [--cta "SHARE TO SEE THE REST"] [--cta2 "PART 2 ON MY PAGE"]

Part 1: the video up to CUT_SECONDS, then the last frame frozen for 3 seconds
        with the call-to-action text.
Part 2: a 1.5 second "PART 2" title over the first frame, then the rest of the video.
"""
import argparse
import os
import subprocess

FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"


def run(cmd):
    subprocess.run(cmd, check=True)


def esc(t):
    return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:")


def text(t, y, size, color="white"):
    return (f"drawtext=fontfile={FONT}:text='{esc(t)}':fontsize={size}:fontcolor={color}:"
            f"borderw=7:bordercolor=black:x=(w-text_w)/2:y={y}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("cut", type=float)
    ap.add_argument("out")
    ap.add_argument("--cta", default="SHARE TO SEE THE REST")
    ap.add_argument("--cta2", default="PART 2 ON MY PAGE")
    ap.add_argument("--clean", help="same video without burned captions (used for frozen frames)")
    ap.add_argument("--ass", help="captions.ass from assemble.py, re-burned over the frozen hold")
    ap.add_argument("--hold-from", type=float, default=None,
                    help="freeze the picture from this time until the cut while the audio keeps "
                         "playing (stops Part 1 from showing the twist)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-ar", "48000", "-ac", "2"]
    base = os.path.splitext(os.path.basename(a.video))[0]
    p1, p2 = os.path.join(a.out, f"{base}_PART1.mp4"), os.path.join(a.out, f"{base}_PART2.mp4")
    tmp = os.path.join(a.out, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    # Part 1: story up to the cut, then a frozen frame with the CTA.
    head = os.path.join(tmp, "head.mp4")
    clean = a.clean or a.video
    if a.hold_from is not None and a.hold_from < a.cut:
        hold = a.cut - a.hold_from
        pre = os.path.join(tmp, "pre.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-t", f"{a.hold_from}", *enc, pre])
        frame = os.path.join(tmp, "holdframe.png")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, a.hold_from - 0.04)}", "-i", clean,
             "-frames:v", "1", frame])
        caps = ""
        if a.ass:
            ass = os.path.abspath(a.ass).replace(":", r"\:")
            caps = f",setpts=PTS+{a.hold_from}/TB,ass='{ass}',setpts=PTS-STARTPTS"
        held = os.path.join(tmp, "held.mp4")
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", f"{hold}",
             "-i", frame, "-ss", f"{a.hold_from}", "-t", f"{hold}", "-i", a.video,
             "-vf", f"setsar=1{caps}", "-map", "0:v", "-map", "1:a", "-shortest", *enc, held])
        lst0 = os.path.join(tmp, "p0.txt")
        with open(lst0, "w") as f:
            f.write(f"file '{os.path.abspath(pre)}'\nfile '{os.path.abspath(held)}'\n")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst0, *enc, head])
        last = frame
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-t", f"{a.cut}", *enc, head])
        last = os.path.join(tmp, "last.png")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, a.cut - 0.05)}", "-i", clean,
             "-frames:v", "1", last])
    card = os.path.join(tmp, "card.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", "3", "-i", last,
         "-f", "lavfi", "-t", "3", "-i", "anullsrc=r=48000:cl=stereo", "-vf",
         "eq=brightness=-0.25," + text(a.cta, "h*0.40", 74, "0xFFD54A") + "," +
         text(a.cta2, "h*0.40+140", 70) + ",setsar=1", "-shortest", *enc, card])
    lst = os.path.join(tmp, "p1.txt")
    with open(lst, "w") as f:
        f.write(f"file '{os.path.abspath(head)}'\nfile '{os.path.abspath(card)}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, *enc,
         "-movflags", "+faststart", p1])

    # Part 2: "PART 2" title for 1.5s, then the rest of the story.
    tail = os.path.join(tmp, "tail.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a.cut}", "-i", a.video, *enc, tail])
    first = os.path.join(tmp, "first.png")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a.cut}", "-i", clean, "-frames:v", "1", first])
    title = os.path.join(tmp, "title.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-t", "1.5", "-i", first,
         "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=48000:cl=stereo", "-vf",
         "eq=brightness=-0.25," + text("PART 2", "h*0.42", 150, "0xFFD54A") + ",setsar=1",
         "-shortest", *enc, title])
    lst2 = os.path.join(tmp, "p2.txt")
    with open(lst2, "w") as f:
        f.write(f"file '{os.path.abspath(title)}'\nfile '{os.path.abspath(tail)}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst2, *enc,
         "-movflags", "+faststart", p2])
    print(f"Done: {p1}\n      {p2}")


if __name__ == "__main__":
    main()
