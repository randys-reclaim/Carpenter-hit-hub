"""Fast vertical cut (9:16, under 3 minutes) from an episode's narration.

  python shorts.py ../episodes/004-tire-light ../cuts/004-tire-light.txt

The cut file lists which narration lines to use, in order, one per line:

  1 shock          line 1, with a hard punch-zoom and shake
  10 rule          rule title: white flash and punch-in
  12               a normal line: quick punch-in
  ALERT Duluth, MN start an "emergency notice" interruption (card + tone)
  25 alert         lines read under the LIVE emergency overlay
  END              end the interruption (glitch back to the notice)

The voice is cut from <episode>/narration.mp3 using the line timings written
by time_narration.py, so it is the same recording as the long video.
Output: <episode>/fast-9x16.mp4
"""
import html, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
W, H, FPS = 1080, 1920, 30
GAP = 0.08          # silence between lines (seconds)
CARD = 1.3          # "we interrupt" card length
RED, ACC, INK, BG = "#FF3B30", "#FFC400", "#FFFFFF", "#0B0B0C"

def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)

def render(jobs):
    """jobs: [(html, out_png, transparent)]"""
    js = HERE / "render_alpha.js"
    p = Path(tempfile.mktemp(suffix=".json"))
    p.write_text(json.dumps([{"html": h, "out": str(o), "w": W, "h": H, "alpha": a} for h, o, a in jobs]))
    subprocess.run(["node", str(js), str(p)], check=True)
    p.unlink()

def alert_overlay(city):
    c = html.escape(city.upper())
    return (f'<div style="position:relative;width:{W}px;height:{H}px">'
            f'<div style="position:absolute;inset:0;border:14px solid {RED};box-shadow:inset 0 0 160px rgba(255,59,48,.45)"></div>'
            f'<div style="position:absolute;left:0;right:0;top:250px;height:110px;background:{RED};display:flex;align-items:center;justify-content:center;gap:22px;'
            f'font:900 54px Montserrat,sans-serif;letter-spacing:.08em;color:{INK}">'
            f'<span style="display:inline-block;width:30px;height:30px;border-radius:50%;background:{INK}"></span>LIVE · EMERGENCY NOTICE</div>'
            f'<div style="position:absolute;left:0;right:0;top:360px;height:70px;background:{BG};display:flex;align-items:center;justify-content:center;'
            f'font:500 34px JetBrains Mono,monospace;letter-spacing:.2em;color:{ACC}">INCIDENT REPORTED · {c}</div></div>')

def alert_card(city):
    c = html.escape(city.upper())
    return (f'<div style="position:relative;width:{W}px;height:{H}px;background:{BG};overflow:hidden">'
            f'<div style="position:absolute;inset:0;background:repeating-linear-gradient(-45deg,{RED} 0 60px,{BG} 60px 120px);opacity:.22"></div>'
            f'<div style="position:absolute;left:60px;right:60px;top:640px;text-align:center;font:900 240px/1 Montserrat,sans-serif;color:{RED}">⚠</div>'
            f'<div style="position:absolute;left:60px;right:60px;top:930px;text-align:center;font:900 92px/1.1 Montserrat,sans-serif;color:{INK};letter-spacing:.02em">WE INTERRUPT<br>THIS NOTICE</div>'
            f'<div style="position:absolute;left:0;right:0;top:1200px;height:100px;background:{RED};display:flex;align-items:center;justify-content:center;'
            f'font:900 48px Montserrat,sans-serif;letter-spacing:.1em;color:{INK}">THIS JUST HAPPENED</div>'
            f'<div style="position:absolute;left:0;right:0;top:1330px;text-align:center;font:500 40px JetBrains Mono,monospace;letter-spacing:.24em;color:{ACC}">{c}</div></div>')

def motion(kind, d):
    """ffmpeg filter for one still: punch-in, shake, flash. n = frame number."""
    N = max(1, round(d * FPS))
    if kind == "shock":
        z = f"if(lt(n,6),1.16-0.10*n/6,1.06+0.02*(n-6)/{N})"
        sx, sy = "26*sin(n*2.3)*exp(-n/7)", "20*cos(n*2.9)*exp(-n/7)"
    elif kind == "alert":
        z = f"1.04+0.03*n/{N}"
        sx, sy = "6*sin(n*1.7)", "5*cos(n*2.1)"
    elif kind == "rule":
        z = f"if(lt(n,5),1.10-0.08*n/5,1.02+0.02*(n-5)/{N})"
        sx, sy = "10*sin(n*2.5)*exp(-n/5)", "0"
    else:
        z = f"if(lt(n,4),1.06-0.04*n/4,1.02+0.025*(n-4)/{N})"
        sx, sy = "0", "0"
    vf = (f"scale=w='trunc({W}*({z})/2)*2':h='trunc({H}*({z})/2)*2':eval=frame:flags=lanczos,"
          f"crop={W}:{H}:x='(iw-{W})/2+{sx}':y='(ih-{H})/2+{sy}'")
    if kind == "rule":
        vf += ",fade=t=in:st=0:d=0.15:color=white"
    if kind == "shock":
        vf += ",fade=t=in:st=0:d=0.08:color=white"
    return vf

def clip(img, d, kind, out, overlay=None):
    vf = motion(kind, d)
    if overlay:
        graph = f"[0:v]{vf}[b];[1:v]format=rgba[o];[b][o]overlay=0:0:enable='gt(mod(t,0.9),0.08)'"
        ff("-loop", "1", "-t", f"{d}", "-i", str(img), "-loop", "1", "-t", f"{d}", "-i", str(overlay),
           "-filter_complex", graph + ",format=yuv420p", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-tune", "animation", str(out))
    else:
        ff("-loop", "1", "-t", f"{d}", "-i", str(img), "-vf", vf + ",format=yuv420p", "-r", str(FPS),
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-tune", "animation", str(out))

def parse_cut(path):
    items = []
    for raw in Path(path).read_text().splitlines():
        s = raw.split("#")[0].strip()
        if not s:
            continue
        if s.startswith("ALERT"):
            items.append(("ALERT", s[5:].strip()))
        elif s == "END":
            items.append(("END", ""))
        else:
            p = s.split()
            items.append((int(p[0]), p[1] if len(p) > 1 else "line"))
    return items

def run(ep_dir, cut_path):
    ep = Path(ep_dir)
    tl = json.loads((ep / "timeline.json").read_text())
    by_no = {l["line"]: l for l in tl["lines"]}
    work = ep / "work-fast"
    work.mkdir(exist_ok=True)
    items = parse_cut(cut_path)

    # overlay and card images for each interruption
    jobs, cities = [], [v for k, v in items if k == "ALERT"]
    for i, c in enumerate(cities):
        jobs.append((alert_overlay(c), work / f"ov{i}.png", True))
        jobs.append((alert_card(c), work / f"card{i}.png", False))
    if jobs:
        render(jobs)

    segs, audio, a_idx, in_alert = [], [], -1, False
    narr = ep / tl["narration"]["file"]
    for k, (key, kind) in enumerate(items):
        if key == "ALERT":
            a_idx += 1
            in_alert = True
            p = work / f"s{k:03d}.mp4"
            clip(work / f"card{a_idx}.png", CARD, "shock", p)
            segs.append(p)
            audio.append(("tone", CARD))
            continue
        if key == "END":
            in_alert = False
            continue
        ln = by_no[key]
        a, b = max(0, ln["start"] - 0.04), ln["end"] + 0.10
        d = round(b - a + GAP, 3)
        p = work / f"s{k:03d}.mp4"
        clip(ep / ln["vimg"], d, "alert" if in_alert and kind == "line" else kind, p,
             overlay=work / f"ov{a_idx}.png" if in_alert else None)
        segs.append(p)
        audio.append(("voice", a, b, d))

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    video = work / "video.mp4"
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video))

    # soundtrack: voice pieces back to back; alert cards get two short beeps
    parts, inputs, n = [], [], 0
    for a in audio:
        if a[0] == "tone":
            d = a[1]
            parts.append(f"sine=f=1050:d=0.18,volume=0.35,apad=pad_dur=0.12[t{n}a];sine=f=1050:d=0.18,volume=0.35,apad=whole_dur={d-0.30:.3f}[t{n}b];[t{n}a][t{n}b]concat=n=2:v=0:a=1,aformat=sample_rates=44100:channel_layouts=mono[p{n}]")
        else:
            _, s, e, d = a
            inputs += ["-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(narr)]
            idx = len(inputs) // 6 - 1
            parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=mono,apad=whole_dur={d:.3f}[p{n}]")
        n += 1
    total = sum(x[1] if x[0] == "tone" else x[3] for x in audio)
    graph = ";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[v];"
    graph += f"anoisesrc=color=brown:amplitude=0.035:duration={total:.3f},lowpass=f=180,volume=0.6[tone];"
    graph += "[v][tone]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[out]"
    sound = work / "sound.m4a"
    ff(*inputs, "-filter_complex", graph, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(sound))

    out = ep / "fast-9x16.mp4"
    ff("-i", str(video), "-i", str(sound), "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(out))
    for p in work.iterdir():
        p.unlink()
    work.rmdir()
    print(f"{out.name}: {int(total//60)}:{int(total%60):02d}")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
