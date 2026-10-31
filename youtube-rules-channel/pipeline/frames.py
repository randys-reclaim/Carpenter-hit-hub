"""Build every frame for an episode.

Outputs (under episodes/<notice>-<slug>/):
  frames/clean/   one 16:9 image per shot, no caption (for editing in CapCut)
  frames/16x9/    one 16:9 image per narration line, caption burned in
  frames/9x16/    one vertical image per narration line (Shorts, TikTok, Reels)
  timeline.json   line order, captions and estimated durations
"""
import html, json, re, subprocess, sys
from pathlib import Path
import art, episode

HERE = Path(__file__).parent
CH = json.loads((HERE / "channel.json").read_text())

OVERLAY = ('<div style="position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.6) 100%),'
           'repeating-linear-gradient(0deg,rgba(255,255,255,.022) 0 1px,transparent 1px 3px)"></div>')

def caption_html(t):
    t = html.escape(t)
    return re.sub(r"\*(.+?)\*", r'<span style="color:#FFC400">\1</span>', t)

def pips(rule):
    if not rule:
        return ""
    cells = "".join(f'<i style="display:block;width:22px;height:12px;border-radius:3px;border:2px solid {"#F2F2F2" if i <= rule else "#6d6d72"};background:{"#F2F2F2" if i <= rule else "transparent"}"></i>' for i in range(1, 8))
    return f'<div style="display:flex;gap:8px">{cells}</div>'

def hud(notice, tc, rule, w):
    if w < 1500:  # vertical: progress boxes get their own row under the header
        return (f'<div style="position:absolute;top:60px;left:56px;right:56px;display:flex;justify-content:space-between;'
                f'font:500 22px JetBrains Mono,monospace;letter-spacing:.18em;color:#6d6d72"><span>NOTICE {notice} // {html.escape(CH["short"])}</span><span>{tc[3:8]}</span></div>'
                f'<div style="position:absolute;top:120px;left:0;right:0;display:flex;justify-content:center">{pips(rule)}</div>')
    return (f'<div style="position:absolute;top:34px;left:56px;right:56px;display:flex;justify-content:space-between;align-items:center;'
            f'font:500 {18 if w > 1500 else 22}px JetBrains Mono,monospace;letter-spacing:.18em;color:#6d6d72">'
            f'<span>NOTICE {notice} // {html.escape(CH["short"])}</span>{pips(rule)}<span>{tc}</span></div>')

def frame16(svg, notice, tc, rule, cap):
    c = (f'<div style="position:absolute;left:160px;right:160px;bottom:74px;text-align:center;font:800 52px/1.25 Montserrat,sans-serif;'
         f'letter-spacing:.03em;text-transform:uppercase;color:#F2F2F2;text-wrap:balance">{caption_html(cap)}</div>') if cap else ""
    return f'<div style="position:relative;width:1920px;height:1080px;background:#0B0B0C;overflow:hidden">{svg}{hud(notice, tc, rule, 1920)}{c}{OVERLAY}</div>'

def frame9(svg, notice, tc, rule, cap):
    return (f'<div style="position:relative;width:1080px;height:1920px;background:#0B0B0C;overflow:hidden">'
            f'{hud(notice, tc, rule, 1080)}'
            f'<div style="position:absolute;left:0;top:430px;width:1080px;height:608px">{svg}</div>'
            f'<div style="position:absolute;left:70px;right:70px;top:1150px;text-align:center;font:800 66px/1.2 Montserrat,sans-serif;letter-spacing:.02em;'
            f'text-transform:uppercase;color:#F2F2F2;text-wrap:balance">{caption_html(cap)}</div>'
            f'<div style="position:absolute;left:0;right:0;bottom:120px;text-align:center;font:500 26px JetBrains Mono,monospace;letter-spacing:.2em;color:#6d6d72">{html.escape(CH["handle"].upper())}</div>'
            f'{OVERLAY}</div>')

def build(script_path, out_root):
    ep = episode.parse(script_path)
    notice = ep["meta"].get("notice", "000")
    out = Path(out_root) / f'{notice}-{ep["meta"].get("slug", "episode")}'
    for d in ("frames/clean", "frames/16x9", "frames/9x16"):
        (out / d).mkdir(parents=True, exist_ok=True)
    jobs, timeline, n_line, n_cue = [], [], 0, 0
    for sc in ep["scenes"]:
        tc = f'00:0{sc["start"]}:00' if sc["start"] else ""
        for cue in sc["cues"]:
            n_cue += 1
            shots = cue["shots"] or [("title", {"l1": "", "l2": ""})]
            svgs = [art.svg(name, params) for name, params in shots]
            for k, s in enumerate(svgs):
                p = out / f"frames/clean/{n_cue:03d}{chr(97+k)}.png"
                jobs.append({"html": frame16(s, notice, tc, sc["rule"], ""), "out": str(p), "w": 1920, "h": 1080})
            for i, line in enumerate(cue["lines"]):
                n_line += 1
                s = svgs[min(i, len(svgs) - 1)]
                p16, p9 = out / f"frames/16x9/{n_line:04d}.png", out / f"frames/9x16/{n_line:04d}.png"
                jobs.append({"html": frame16(s, notice, tc, sc["rule"], line["caption"]), "out": str(p16), "w": 1920, "h": 1080})
                jobs.append({"html": frame9(s, notice, tc, sc["rule"], line["caption"]), "out": str(p9), "w": 1080, "h": 1920})
                timeline.append({"line": n_line, "cue": n_cue, "scene": sc["name"], "text": line["caption"].replace("*", ""),
                                 "raw": line["raw"], "est": line["est"], "img": str(p16.relative_to(out)), "vimg": str(p9.relative_to(out))})
    end = art.svg("mascot", {"text": CH["signoff"]})
    jobs.append({"html": frame9(end, notice, "", 0, "Full notice on YouTube"), "out": str(out / "frames/9x16/end.png"), "w": 1080, "h": 1920})
    (out / "timeline.json").write_text(json.dumps({"meta": ep["meta"], "lines": timeline}, indent=1))
    jp = out / "render-jobs.json"
    jp.write_text(json.dumps(jobs))
    print(f"{out.name}: {n_cue} cues, {n_line} lines, {len(jobs)} images")
    subprocess.run(["node", str(HERE / "render.js"), str(jp)], check=True)
    jp.unlink()
    return out

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else HERE.parent / "episodes")
