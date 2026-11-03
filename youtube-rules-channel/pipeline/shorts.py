"""Fast vertical cut (9:16, under 3 minutes) from an episode's narration.

  python shorts.py ../episodes/004-tire-light ../cuts/004-tire-light.txt

The cut file lists which narration lines to use, in order, one per line:

  1 shock          line 1, with a hard punch-zoom and shake
  10 rule          rule title: white flash and punch-in
  12               a normal line: quick punch-in
  ALERT Duluth, MN start an interruption: red WARNING strobe + alarm beeps
  25               lines inside an interruption play under the red LIVE overlay
  27 cut           cut the story off part-way through this line with a burst of
                   static, like the feed got hacked, and return to the notice
  END              end an interruption without the static cut
  SAY lessac Warning. We interrupt your regularly scheduled video.
                   inside an interruption: a robotic emergency voice reads the
                   text (piper TTS voices: lessac = woman, ryan = man). The
                   first SAY plays over the WARNING strobe; later ones over a
                   LIVE bulletin screen with the words as captions.
  STATIC           a short burst of static
  SAYCUT ryan ...  like SAY, but cut off part-way, then two glitches and back

The voice is cut from <episode>/narration.mp3 using the line timings written
by time_narration.py, so it is the same recording as the long video.
Output: <episode>/fast-9x16.mp4
"""
import html, json, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
W, H, FPS = 1080, 1920, 30
GAP = 0.08          # silence between lines (seconds)
CARD = 0.75         # red WARNING flash length
GLITCH = 0.35       # static burst when an interruption is cut off
RED, ACC, INK, BG = "#FF3B30", "#FFC400", "#FFFFFF", "#0B0B0C"

VOICE_DIR = Path.home() / ".cache" / "piper-voices"
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/{n}/medium/en_US-{n}-medium.onnx"

def tts(text, voice, out):
    """Robotic emergency-broadcast voice: piper TTS, then a radio band-pass and a little grit."""
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    model = VOICE_DIR / f"en_US-{voice}-medium.onnx"
    for suffix in ("", ".json"):
        f = Path(str(model) + suffix)
        if not f.exists():
            subprocess.run(["curl", "-sSL", "-o", str(f), VOICE_URL.format(n=voice) + suffix], check=True)
    raw = Path(str(out) + ".raw.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", str(model), "-f", str(raw)], input=text.encode(), check=True, capture_output=True)
    ff("-i", str(raw), "-af", "highpass=f=320,lowpass=f=3300,acrusher=bits=10:mix=0.25,volume=1.6,aresample=44100", "-ac", "1", str(out))
    raw.unlink()
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                capture_output=True, text=True).stdout)

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

def alert_card(city, inverse=False):
    """Full-screen WARNING flash. Two versions (red on black / black on red) alternate to strobe."""
    bg, fg = (RED, BG) if inverse else (BG, RED)
    c = html.escape(city.upper())
    return (f'<div style="position:relative;width:{W}px;height:{H}px;background:{bg};overflow:hidden">'
            f'<div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0 3px,transparent 3px 7px)"></div>'
            f'<div style="position:absolute;left:0;right:0;top:620px;text-align:center;font:900 300px/1 Montserrat,sans-serif;color:{fg}">⚠</div>'
            f'<div style="position:absolute;left:0;right:0;top:960px;text-align:center;font:900 165px/1 Montserrat,sans-serif;color:{fg};letter-spacing:.02em">WARNING</div>'
            f'<div style="position:absolute;left:0;right:0;top:1200px;text-align:center;font:500 44px JetBrains Mono,monospace;letter-spacing:.24em;color:{fg}">LIVE INCIDENT · {c}</div></div>')

def bulletin(text, city, notice):
    """LIVE bulletin screen: the case's map pin with the spoken words as the caption."""
    import art, frames
    return frames.frame9(art.svg("pin", {"city": city.split(",")[0]}), notice, "", 0, text)

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

HACK = "rgbashift=rh=-10:bh=10:gv=4,noise=alls=10"  # fixed grain (moving grain made files huge)
STATIC = ("noise=alls=90:allf=t+u,rgbashift=rh=-40:bh=40:rv=12:bv=-12,"
          "hue=s=0.4,eq=contrast=1.6:brightness=0.05,crop=iw:ih*0.92:0:'mod(n*97,ih*0.08)',scale={W}:{H}")

def clip(img, d, kind, out, overlay=None):
    vf = motion("alert" if kind in ("alert", "cut") else kind, d)
    if kind == "static":
        vf = motion("shock", d) + "," + STATIC.format(W=W, H=H)
    elif kind in ("alert", "cut") or overlay:
        vf += "," + HACK
    if overlay:
        graph = f"[0:v]{vf}[b];[1:v]format=rgba[o];[b][o]overlay=0:0:enable='gt(mod(t,0.9),0.08)'"
        ff("-loop", "1", "-t", f"{d}", "-i", str(img), "-loop", "1", "-t", f"{d}", "-i", str(overlay),
           "-filter_complex", graph + ",format=yuv420p", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-tune", "animation", str(out))
    else:
        ff("-loop", "1", "-t", f"{d}", "-i", str(img), "-vf", vf + ",format=yuv420p", "-r", str(FPS),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-tune", "animation", str(out))

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
        elif s == "STATIC":
            items.append(("STATIC", ""))
        elif s.startswith("SAYCUT ") or s.startswith("SAY "):
            tag, voice, text = s.split(" ", 2)
            items.append((tag, (voice, text)))
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
        jobs.append((alert_card(c, inverse=True), work / f"cardx{i}.png", False))
    notice = tl["meta"].get("notice", "000")
    said, a_i, first = {}, -1, True
    for k, (key, val) in enumerate(items):
        if key == "ALERT":
            a_i, first = a_i + 1, True
        elif key in ("SAY", "SAYCUT"):
            voice, text = val
            wav = work / f"say{k:03d}.wav"
            said[k] = (wav, tts(text, voice, wav), first)
            if not first:
                shown = text
                if key == "SAYCUT":  # the voice is cut at 70%, so the caption stops there too
                    ws = text.split()
                    shown = " ".join(ws[:max(1, round(len(ws) * 0.7))]).rstrip(",.") + "—"
                jobs.append((bulletin(shown, cities[a_i], notice), work / f"bul{k:03d}.png", False))
            first = False
    if jobs:
        render(jobs)

    segs, audio, a_idx, in_alert = [], [], -1, False
    narr = ep / tl["narration"]["file"]
    for k, (key, kind) in enumerate(items):
        if key == "ALERT":
            a_idx += 1
            in_alert = True
            p = work / f"s{k:03d}.mp4"
            graph = (f"[0:v]{motion('shock', CARD)},{HACK}[a];[1:v]{motion('shock', CARD)}[b];"
                     f"[a][b]overlay=0:0:enable='lt(mod(t,0.18),0.09)',format=yuv420p")
            ff("-loop", "1", "-t", f"{CARD}", "-i", str(work / f"card{a_idx}.png"), "-loop", "1", "-t", f"{CARD}", "-i", str(work / f"cardx{a_idx}.png"),
               "-filter_complex", graph, "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-tune", "animation", str(p))
            segs.append(p)
            audio.append(("tone", CARD))
            continue
        if key == "END":
            in_alert = False
            continue
        if key == "STATIC":
            p = work / f"s{k:03d}.mp4"
            clip(work / f"card{a_idx}.png", GLITCH, "static", p)
            segs.append(p)
            audio.append(("static", GLITCH))
            continue
        if key in ("SAY", "SAYCUT"):
            wav, dur, on_card = said[k]
            keep = dur * 0.7 if key == "SAYCUT" else dur + 0.15
            p = work / f"s{k:03d}.mp4"
            if on_card:  # keep strobing the WARNING card while the warning is read
                graph = (f"[0:v]{motion('alert', keep)},{HACK}[a];[1:v]{motion('alert', keep)}[b];"
                         f"[a][b]overlay=0:0:enable='lt(mod(t,0.36),0.12)',format=yuv420p")
                ff("-loop", "1", "-t", f"{keep}", "-i", str(work / f"card{a_idx}.png"), "-loop", "1", "-t", f"{keep}", "-i", str(work / f"cardx{a_idx}.png"),
                   "-filter_complex", graph, "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-tune", "animation", str(p))
            else:
                clip(work / f"bul{k:03d}.png", keep, "alert", p, overlay=work / f"ov{a_idx}.png")
            segs.append(p)
            audio.append(("say", wav, keep))
            if key == "SAYCUT":  # two glitches, then back to the notice
                for g, gd in enumerate((0.22, 0.08, 0.26)):
                    p = work / f"s{k:03d}g{g}.mp4"
                    if g == 1:
                        ff("-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={gd}:r={FPS}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p))
                        audio.append(("silence", gd))
                    else:
                        clip(work / f"bul{k:03d}.png", gd, "static", p)
                        audio.append(("static", gd))
                    segs.append(p)
                in_alert = False
            continue
        ln = by_no[key]
        a, b = max(0, ln["start"] - 0.04), ln["end"] + 0.10
        if kind == "cut":
            b = a + (b - a) * 0.65
        d = round(b - a + (0 if kind == "cut" else GAP), 3)
        p = work / f"s{k:03d}.mp4"
        clip(ep / ln["vimg"], d, "alert" if in_alert and kind == "line" else kind, p,
             overlay=work / f"ov{a_idx}.png" if in_alert else None)
        segs.append(p)
        audio.append(("voice", a, b, d))
        if kind == "cut":
            p = work / f"s{k:03d}x.mp4"
            clip(ep / ln["vimg"], GLITCH, "static", p)
            segs.append(p)
            audio.append(("static", GLITCH))
            in_alert = False

    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    video = work / "video.mp4"
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video))

    # soundtrack: voice pieces back to back; alert cards get two short beeps
    parts, inputs, n = [], [], 0
    for a in audio:
        if a[0] == "tone":
            d = a[1]  # three fast alarm beeps
            parts.append(f"sine=f=1180:d={d:.3f},volume='0.4*lt(mod(t,0.25),0.12)':eval=frame,aformat=sample_rates=44100:channel_layouts=mono[p{n}]")
        elif a[0] == "say":
            _, wav, d = a
            inputs += ["-ss", "0", "-to", f"{d:.3f}", "-i", str(wav)]
            idx = len(inputs) // 6 - 1
            parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=mono,afade=t=out:st={max(0, d-0.03):.3f}:d=0.03,apad=whole_dur={d:.3f}[p{n}]")
        elif a[0] == "silence":
            parts.append(f"anullsrc=r=44100:cl=mono,atrim=0:{a[1]:.3f}[p{n}]")
        elif a[0] == "static":
            parts.append(f"anoisesrc=color=white:amplitude=0.5:duration={a[1]:.3f},highpass=f=900,volume=0.5,aformat=sample_rates=44100:channel_layouts=mono[p{n}]")
        else:
            _, s, e, d = a
            inputs += ["-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(narr)]
            idx = len(inputs) // 6 - 1
            parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=mono,apad=whole_dur={d:.3f}[p{n}]")
        n += 1
    total = sum(x[1] if x[0] in ("tone", "static", "silence") else x[2] if x[0] == "say" else x[3] for x in audio)
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
