"""Parse an episode script (.md) into cues and narration lines.

Script conventions (see 02-script-doorbell-camera.md):
  <!-- episode: notice=001 slug=doorbell -->      once, near the top
  ### RULE 1: DON'T WATCH IT TWICE (0:18–1:20)    scene header
  **[VISUAL]** description                          starts a new cue
  <!-- shot: doorcam fig=walkaway ts="03:12" -->  scene template for that cue;
                                                    several shot lines = one per narration line
  Narration line / with pauses //                   one caption each
"""
import re, shlex, json, sys
from pathlib import Path

WPS = 2.35  # narration speed in words per second (about 140 wpm)

def parse_kv(s):
    parts = shlex.split(s)
    return parts[0], dict(p.split("=", 1) for p in parts[1:])

def clean_caption(line):
    t = line.replace("//", " ").replace(" /", " ").rstrip("/ ")
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()

def estimate(line):
    long_ = line.count("//")
    short = line.count("/") - 2 * long_
    words = len(re.findall(r"[A-Za-z0-9']+", clean_caption(line)))
    return round(words / WPS + 0.5 * short + 1.0 * long_ + 0.35, 2)

def parse(path):
    src = Path(path).read_text()
    meta = {}
    m = re.search(r"<!--\s*episode:(.*?)-->", src)
    if m:
        meta = parse_kv("x " + m.group(1).strip())[1]
    m = re.search(r'^# Script: "(.+?)"', src, re.M)
    meta["title"] = m.group(1) if m else Path(path).stem
    body = src.split("## Full script", 1)[1].split("\n## ", 1)[0]
    scenes, cue = [], None
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s == "---" or s.startswith(">"):
            continue
        if s.startswith("### "):
            h = s[4:]
            mm = re.match(r"(.*?)\s*\((\d+:\d\d).(\d+:\d\d)\)$", h)
            name = mm.group(1) if mm else h
            rn = re.match(r"RULE (\d)", name)
            scenes.append({"name": name, "start": mm.group(2) if mm else "", "rule": int(rn.group(1)) if rn else 0, "cues": []})
            cue = None
            continue
        if not scenes:
            continue
        if s.startswith("**[VISUAL]**"):
            cue = {"visual": s[12:].strip(), "shots": [], "lines": []}
            scenes[-1]["cues"].append(cue)
            continue
        m = re.match(r"<!--\s*shot:(.*?)-->", s)
        if m and cue is not None:
            cue["shots"].append(parse_kv(m.group(1).strip()))
            continue
        if s.startswith("<!--"):
            continue
        if cue is None:
            cue = {"visual": "", "shots": [], "lines": []}
            scenes[-1]["cues"].append(cue)
        cue["lines"].append({"raw": s, "caption": clean_caption(s), "est": estimate(s)})
    return {"meta": meta, "scenes": scenes}

if __name__ == "__main__":
    ep = parse(sys.argv[1])
    n_cues = sum(len(s["cues"]) for s in ep["scenes"])
    n_lines = sum(len(c["lines"]) for s in ep["scenes"] for c in s["cues"])
    total = sum(l["est"] for s in ep["scenes"] for c in s["cues"] for l in c["lines"])
    untagged = [c["visual"][:60] for s in ep["scenes"] for c in s["cues"] if not c["shots"]]
    print(json.dumps(ep["meta"]), f"\n{len(ep['scenes'])} scenes, {n_cues} cues, {n_lines} lines, est {int(total//60)}:{int(total%60):02d}")
    for u in untagged:
        print("  untagged:", u)
