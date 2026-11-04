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

Public-service-announcement hijack (freezes the video where it was cut):
  25 interrupt     play the first half of line 25, then freeze on that frame
  PSA              start the hijack over the frozen frame
  LIVECHECK lessac Are we live?     muffled off-mic voices over static
  BROADCAST joe Warning. A number of tire pressure sensors ...
                   the announcer, one sentence per line, centred under
                   diagonal WARNING bands that strobe over the frozen video
  CARLIST          about 1,000 "affected vehicles" fly up in three columns
  ENDPSA           bright white flash, then the rest of line 25 plays from
                   exactly where it stopped

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

def tts(text, voice, out, muffled=False):
    """Robotic emergency-broadcast voice: piper TTS, then a radio band-pass and a little grit.
    muffled=True: quieter, duller and roomy, like someone off-mic in the control room."""
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    model = VOICE_DIR / f"en_US-{voice}-medium.onnx"
    for suffix in ("", ".json"):
        f = Path(str(model) + suffix)
        if not f.exists():
            subprocess.run(["curl", "-sSL", "-o", str(f), VOICE_URL.format(n=voice) + suffix], check=True)
    raw = Path(str(out) + ".raw.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", str(model), "-f", str(raw)], input=text.encode(), check=True, capture_output=True)
    af = ("highpass=f=200,lowpass=f=1400,aecho=0.8:0.7:60|140:0.35|0.25,volume=0.9,aresample=44100" if muffled
          else "highpass=f=320,lowpass=f=3300,acrusher=bits=10:mix=0.25,volume=1.6,aresample=44100")
    ff("-i", str(raw), "-af", af, "-ac", "1", str(out))
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

FONT = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"

def cctv_overlay():
    """Corner brackets and labels of a security-camera feed (transparent PNG)."""
    b = f"position:absolute;width:90px;height:90px;border-color:{INK};border-style:solid;opacity:.85"
    return (f'<div style="position:relative;width:{W}px;height:{H}px">'
            f'<div style="{b};left:40px;top:170px;border-width:6px 0 0 6px"></div><div style="{b};right:40px;top:170px;border-width:6px 6px 0 0"></div>'
            f'<div style="{b};left:40px;bottom:200px;border-width:0 0 6px 6px"></div><div style="{b};right:40px;bottom:200px;border-width:0 6px 6px 0"></div>'
            f'<div style="position:absolute;left:150px;bottom:212px;font:500 34px JetBrains Mono,monospace;letter-spacing:.16em;color:{INK};opacity:.85">CAM 04 · YOUR HOUSE</div></div>')

def flash_card(text):
    return (f'<div style="position:relative;width:{W}px;height:{H}px;background:{BG}">'
            f'<div style="position:absolute;left:0;right:0;top:860px;text-align:center;font:900 150px/1.05 Montserrat,sans-serif;color:{INK}">{html.escape(text)}</div></div>')

def creep(video, total, work, notice, city):
    """They're watching: CCTV feed overlay (blinking REC, ticking 3 AM clock, viewer count)
    and three-frame subliminal flashes every 20-30 seconds."""
    import art, frames
    render([(cctv_overlay(), work / "cctv.png", True), (flash_card("I SEE YOU"), work / "f_see.png", False),
            (flash_card("DON'T TURN AROUND"), work / "f_turn.png", False),
            (frames.frame9(art.svg("face", {}), notice, "", 0, ""), work / "f_face.png", False)])
    flashes, t, cycle = [], 19.3, ["f_face", "f_see", "f_face", "f_turn"]
    while t < total - 4:
        flashes.append((t, cycle[len(flashes) % len(cycle)]))
        t += 26.7 if len(flashes) % 2 else 21.9
    inputs = ["-i", str(video), "-loop", "1", "-i", str(work / "cctv.png")]
    names = sorted({n for _, n in flashes})
    for n in names:
        inputs += ["-loop", "1", "-i", str(work / f"{n}.png")]
    dt = f"fontfile={FONT}:fontcolor=white"
    clock = r"03\:%{eif\:12+trunc((4+t)/60)\:d\:2}\:%{eif\:mod(4+t\,60)\:d\:2} AM"
    g = f"[0:v][1:v]overlay=0:0:shortest=1[v0];"
    g += (f"[v0]drawtext={dt}:fontsize=40:x=150:y=190:text='● REC':fontcolor=0xFF3B30:enable='lt(mod(t,1),0.6)',"
          f"drawtext={dt}:fontsize=36:x=330:y=192:text='{clock}',"
          f"drawtext={dt}:fontsize=34:x=w-tw-150:y=192:text='1 WATCHING':enable='lt(t,{max(0, total-12):.2f})',"
          f"drawtext={dt}:fontsize=34:x=w-tw-150:y=192:text='2 WATCHING':fontcolor=0xFF3B30:enable='gte(t,{max(0, total-12):.2f})'[v1]")
    last = "v1"
    for i, (ft, n) in enumerate(flashes):
        idx = 2 + names.index(n)
        g += f";[{last}][{idx}:v]overlay=0:0:enable='between(t,{ft:.3f},{ft+0.1:.3f})'[f{i}]"
        last = f"f{i}"
    out = work / "creep.mp4"
    ff(*inputs, "-filter_complex", g, "-map", f"[{last}]", "-t", f"{total:.3f}", "-r", str(FPS), "-pix_fmt", "yuv420p",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-tune", "animation", str(out))
    return out

MAKES = {
    "FORD": ["F-150", "ESCAPE", "EXPLORER", "FOCUS", "FUSION", "MUSTANG", "RANGER", "EDGE", "EXPEDITION", "TAURUS"],
    "CHEVROLET": ["SILVERADO", "MALIBU", "EQUINOX", "TAHOE", "IMPALA", "CRUZE", "TRAVERSE", "COLORADO", "SUBURBAN"],
    "TOYOTA": ["CAMRY", "COROLLA", "RAV4", "TACOMA", "TUNDRA", "HIGHLANDER", "PRIUS", "SIENNA", "4RUNNER"],
    "HONDA": ["ACCORD", "CIVIC", "CR-V", "PILOT", "ODYSSEY", "FIT", "RIDGELINE", "HR-V"],
    "NISSAN": ["ALTIMA", "SENTRA", "ROGUE", "MAXIMA", "PATHFINDER", "FRONTIER", "TITAN", "MURANO"],
    "DODGE": ["RAM 1500", "CHARGER", "CHALLENGER", "DURANGO", "GRAND CARAVAN", "JOURNEY"],
    "JEEP": ["WRANGLER", "GRAND CHEROKEE", "CHEROKEE", "COMPASS", "LIBERTY", "GLADIATOR"],
    "GMC": ["SIERRA", "YUKON", "ACADIA", "TERRAIN", "CANYON", "SAVANA"],
    "HYUNDAI": ["ELANTRA", "SONATA", "TUCSON", "SANTA FE", "ACCENT", "PALISADE"],
    "KIA": ["OPTIMA", "SORENTO", "SOUL", "FORTE", "SPORTAGE", "TELLURIDE"],
    "SUBARU": ["OUTBACK", "FORESTER", "IMPREZA", "LEGACY", "CROSSTREK", "ASCENT"],
    "VOLKSWAGEN": ["JETTA", "PASSAT", "GOLF", "TIGUAN", "ATLAS", "BEETLE"],
    "BMW": ["3 SERIES", "5 SERIES", "X3", "X5", "X1", "7 SERIES"],
    "MAZDA": ["MAZDA3", "MAZDA6", "CX-5", "CX-9", "MX-5", "CX-30"],
    "BUICK": ["ENCLAVE", "LACROSSE", "ENCORE", "REGAL", "LUCERNE"],
    "CHRYSLER": ["300", "PACIFICA", "TOWN & COUNTRY", "SEBRING", "200"],
    "LEXUS": ["RX 350", "ES 350", "IS 250", "GX 460", "NX 300"],
    "TESLA": ["MODEL 3", "MODEL Y", "MODEL S", "MODEL X", "CYBERTRUCK"],
    "CADILLAC": ["ESCALADE", "CTS", "XT5", "SRX", "DTS"],
    "MERCURY": ["GRAND MARQUIS", "MOUNTAINEER", "MILAN", "SABLE"],
    "PONTIAC": ["GRAND PRIX", "G6", "VIBE", "AZTEK"],
    "SATURN": ["ION", "VUE", "AURA", "OUTLOOK"],
}

def car_list(n=1020):
    import random
    rnd = random.Random(2050)
    pool = [(m, x) for m, xs in MAKES.items() for x in xs]
    return [f"{rnd.randint(2000, 2050)} {m} {x}" for m, x in (rnd.choice(pool) for _ in range(n))]

def carlist_tall(rows):
    """Three columns of vehicles, one tall image that scrolls up."""
    cols = [rows[i::3] for i in range(3)]
    h = 160 + len(cols[0]) * 46 + 1920
    col = lambda c: "".join(f"<div>{html.escape(r)}</div>" for r in c)
    return (f'<div style="position:relative;width:{W}px;height:{h}px;background:{BG}">'
            f'<div style="position:absolute;left:30px;right:30px;top:1920px;display:grid;grid-template-columns:repeat(3,1fr);gap:18px;'
            f'font:500 25px/46px JetBrains Mono,monospace;color:{INK};white-space:nowrap;overflow:hidden">'
            + "".join(f"<div>{col(c)}</div>" for c in cols) + "</div></div>"), h

def list_header():
    return (f'<div style="position:relative;width:{W}px;height:{H}px">'
            f'<div style="position:absolute;left:0;right:0;top:0;height:440px;background:linear-gradient({BG} 78%,transparent)"></div>'
            f'<div style="position:absolute;left:0;right:0;top:260px;height:110px;background:{RED};display:flex;align-items:center;justify-content:center;'
            f'font:900 46px Montserrat,sans-serif;letter-spacing:.04em;color:{INK};white-space:nowrap">AFFECTED VEHICLES · 2000–2050</div></div>')

def diag_warning():
    band = lambda top: (f'<div style="position:absolute;left:-600px;width:2400px;top:{top}px;height:150px;background:{RED};transform:rotate(-24deg);'
                        f'display:flex;align-items:center;white-space:nowrap;overflow:hidden;font:900 96px Montserrat,sans-serif;letter-spacing:.08em;color:{BG}">'
                        + "⚠ WARNING " * 9 + "</div>")
    return f'<div style="position:relative;width:{W}px;height:{H}px;overflow:hidden">{band(420)}{band(1320)}</div>'

def psa_message(text):
    return (f'<div style="position:relative;width:{W}px;height:{H}px">'
            f'<div style="position:absolute;left:70px;right:70px;top:640px;background:rgba(11,11,12,.94);border:8px solid {RED};padding:46px 44px 54px;text-align:center">'
            f'<div style="font:900 34px Montserrat,sans-serif;letter-spacing:.16em;color:{RED};margin-bottom:26px">PUBLIC SERVICE ANNOUNCEMENT</div>'
            f'<div style="font:900 62px/1.18 Montserrat,sans-serif;color:{INK};text-transform:uppercase">{html.escape(text)}</div></div></div>')

def connecting():
    return (f'<div style="position:relative;width:{W}px;height:{H}px">'
            f'<div style="position:absolute;left:0;right:0;top:860px;text-align:center;font:900 76px Montserrat,sans-serif;letter-spacing:.12em;color:{INK}">STAND BY</div>'
            f'<div style="position:absolute;left:0;right:0;top:960px;text-align:center;font:500 34px JetBrains Mono,monospace;letter-spacing:.3em;color:{RED}">● LIVE FEED · CONNECTING</div></div>')

def enc():
    return ["-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "8M", "-bufsize", "16M", "-tune", "animation"]

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
        elif s in ("STATIC", "PSA", "CARLIST", "ENDPSA"):
            items.append((s, ""))
        elif s.startswith("LIVECHECK ") or s.startswith("BROADCAST "):
            tag, voice, text = s.split(" ", 2)
            items.append((tag, (voice, text)))
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
    if any(k == "PSA" for k, _ in items):
        jobs += [(diag_warning(), work / "psa_diag.png", True), (connecting(), work / "psa_conn.png", True),
                 (list_header(), work / "psa_head.png", True)]
        tall, tall_h = carlist_tall(car_list())
        for k, (key, val) in enumerate(items):
            if key in ("LIVECHECK", "BROADCAST"):
                voice, text = val
                wav = work / f"say{k:03d}.wav"
                said[k] = (wav, tts(text, voice, wav, muffled=key == "LIVECHECK"), False)
                if key == "BROADCAST":
                    jobs.append((psa_message(text), work / f"msg{k:03d}.png", True))
    if jobs:
        render(jobs)
    if any(k == "PSA" for k, _ in items):
        js = HERE / "render_alpha.js"
        jp = work / "tall.json"
        jp.write_text(json.dumps([{"html": tall, "out": str(work / "psa_list.png"), "w": W, "h": tall_h, "alpha": False}]))
        subprocess.run(["node", str(js), str(jp)], check=True)

    segs, audio, a_idx, in_alert = [], [], -1, False
    freeze, resume = None, None
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
        if key == "PSA":  # freeze on the last frame shown
            freeze = work / f"freeze{k:03d}.png"
            ff("-sseof", "-0.05", "-i", str(segs[-1]), "-frames:v", "1", "-update", "1", str(freeze))
            p = work / f"s{k:03d}.mp4"  # a hard jolt: the picture stutters and grains up
            ff("-loop", "1", "-t", "0.25", "-i", str(freeze), "-vf", motion("shock", 0.25) + "," + STATIC.format(W=W, H=H), *enc(), str(p))
            segs.append(p)
            audio.append(("static", 0.25))
            continue
        if key == "LIVECHECK":
            wav, dur, _ = said[k]
            d = dur + 0.25
            p = work / f"s{k:03d}.mp4"
            g = (f"[0:v]eq=brightness=-0.35:saturation=0.2,{HACK},noise=alls=25[b];[1:v]format=rgba[o];"
                 f"[b][o]overlay=0:0:enable='lt(mod(t,0.8),0.55)',format=yuv420p")
            ff("-loop", "1", "-t", f"{d}", "-i", str(freeze), "-loop", "1", "-t", f"{d}", "-i", str(work / "psa_conn.png"), "-filter_complex", g, *enc(), str(p))
            segs.append(p)
            audio.append(("say", wav, d))
            continue
        if key == "BROADCAST":
            wav, dur, _ = said[k]
            d = dur + 0.2
            p = work / f"s{k:03d}.mp4"
            g = (f"[0:v]eq=brightness=-0.45:saturation=0.15,{HACK}[b];[1:v]format=rgba[w];[2:v]format=rgba[m];"
                 f"[b][w]overlay=0:0:enable='lt(mod(t,0.5),0.32)'[bw];[bw][m]overlay=0:0,"
                 f"crop={W}:{H}:x='4*sin(n*1.9)':y='3*cos(n*2.3)',format=yuv420p")
            ff("-loop", "1", "-t", f"{d}", "-i", str(freeze), "-loop", "1", "-t", f"{d}", "-i", str(work / "psa_diag.png"),
               "-loop", "1", "-t", f"{d}", "-i", str(work / f"msg{k:03d}.png"), "-filter_complex", g, *enc(), str(p))
            segs.append(p)
            audio.append(("say", wav, d))
            continue
        if key == "CARLIST":
            d = 2.8
            p = work / f"s{k:03d}.mp4"
            g = (f"[0:v]crop={W}:{H}:0:'(ih-{H})*min(1,t/{d - 0.2})'[l];[1:v]format=rgba[h];"
                 f"[l][h]overlay=0:0,{HACK},format=yuv420p")
            ff("-loop", "1", "-t", f"{d}", "-i", str(work / "psa_list.png"), "-loop", "1", "-t", f"{d}", "-i", str(work / "psa_head.png"),
               "-filter_complex", g, *enc(), str(p))
            segs.append(p)
            audio.append(("ticks", d))
            continue
        if key == "ENDPSA":  # bright white flash, then the video resumes where it stopped
            p = work / f"s{k:03d}.mp4"
            ff("-f", "lavfi", "-i", f"color=c=white:s={W}x{H}:d=0.2:r={FPS}", *enc(), str(p))
            segs.append(p)
            audio.append(("bam", 0.2))
            if resume:
                ln, a, b = resume
                d = round(b - a + GAP, 3)
                p = work / f"s{k:03d}r.mp4"
                clip(ep / ln["vimg"], d, "line", p)
                segs.append(p)
                audio.append(("voice", a, b, d))
                resume = None
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
        if kind == "interrupt":
            mid = a + (b - a) * 0.5
            resume, b, kind = (ln, mid, b), mid, "line"
        d = round(b - a + (0 if (kind == "cut" or resume) else GAP), 3)
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
        elif a[0] == "ticks":  # data readout: fast high blips
            parts.append(f"sine=f=2400:d={a[1]:.3f},volume='0.12*lt(mod(t,0.045),0.012)':eval=frame,aformat=sample_rates=44100:channel_layouts=mono[p{n}]")
        elif a[0] == "bam":  # deep hit under the white flash
            parts.append(f"sine=f=48:d={a[1]:.3f},volume='1.2*exp(-t*9)':eval=frame,aformat=sample_rates=44100:channel_layouts=mono[p{n}]")
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
    total = sum(x[1] if x[0] in ("tone", "static", "silence", "ticks", "bam") else x[2] if x[0] == "say" else x[3] for x in audio)
    graph = ";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[v];"
    # low electrical drone: two close sine tones beat against each other, over brown-noise room tone
    graph += (f"anoisesrc=color=brown:amplitude=0.035:duration={total:.3f},lowpass=f=180,volume=0.6[rt];"
              f"sine=f=55:d={total:.3f},volume=0.05[d1];sine=f=58.5:d={total:.3f},volume=0.05[d2];"
              f"sine=f=120:d={total:.3f},volume=0.012,tremolo=f=0.3:d=0.8[hum];"
              f"[rt][d1][d2][hum]amix=inputs=4:normalize=0[tone];")
    graph += "[v][tone]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[out]"
    sound = work / "sound.m4a"
    ff(*inputs, "-filter_complex", graph, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(sound))

    video = creep(video, total, work, notice, cities[0] if cities else "")
    out = ep / "fast-9x16.mp4"
    ff("-i", str(video), "-i", str(sound), "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(out))
    for p in work.iterdir():
        p.unlink()
    work.rmdir()
    print(f"{out.name}: {int(total//60)}:{int(total%60):02d}")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
