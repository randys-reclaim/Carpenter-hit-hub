"""Render the channel's brand kit into ../brand/ from channel.json.

  avatar-800.png          YouTube profile picture (also TikTok / Instagram)
  avatar-1080.png         high-res profile picture
  youtube-banner.png      2560x1440, text inside the 1546x423 safe area
  watermark-150.png       YouTube video watermark
  highlight-*.png         Instagram story highlight covers (1080x1920)
  tiktok-ig-cover.png     1080x1920 pinned-post / profile cover
"""
import html, json, subprocess
from pathlib import Path
import art

HERE = Path(__file__).parent
OUT = HERE.parent / "brand"
CH = json.loads((HERE / "channel.json").read_text())

def mascot(cx, cy, s, body=art.BG, visor=art.ACC, badge=art.INK):
    """Faceless clerk: round head with a visor slit, shoulders, lanyard and ID badge."""
    k = lambda v: v * s
    return (f'<circle cx="{cx}" cy="{cy-k(150)}" r="{k(120)}" fill="{body}"/>'
            f'<rect x="{cx-k(78)}" y="{cy-k(160)}" width="{k(156)}" height="{k(22)}" rx="{k(11)}" fill="{visor}"/>'
            f'<path d="M{cx-k(210)} {cy+k(230)} Q{cx-k(210)} {cy+k(10)} {cx} {cy+k(10)} Q{cx+k(210)} {cy+k(10)} {cx+k(210)} {cy+k(230)}Z" fill="{body}"/>'
            f'<path d="M{cx-k(55)} {cy+k(12)} L{cx} {cy+k(120)} L{cx+k(55)} {cy+k(12)}" stroke="{visor}" stroke-width="{k(9)}" fill="none"/>'
            f'<rect x="{cx-k(38)}" y="{cy+k(115)}" width="{k(76)}" height="{k(96)}" rx="{k(8)}" fill="{badge}"/>'
            f'<rect x="{cx-k(24)}" y="{cy+k(138)}" width="{k(48)}" height="{k(10)}" fill="{body}"/><rect x="{cx-k(24)}" y="{cy+k(158)}" width="{k(32)}" height="{k(8)}" fill="{body}"/>')

def svg(w, h, body, bg=art.BG):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="display:block">{art.DEFS}'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>')

def avatar(size):
    c = size / 2
    return svg(size, size, mascot(c, c + size * 0.06, size / 800 * 1.25), bg=art.ACC)

def banner():
    W, H = 2560, 1440
    body = ""
    # a whole street across the full TV width; only the middle survives on phones
    s = 0.62
    step = 220 * s + 26
    n = int(W / step) + 2
    x0 = (W - n * step) / 2
    lit = n // 2
    for i in range(n):
        body += art.house(x0 + i * step, 760, s, lit=(i == lit))
    lx = x0 + lit * step + 220 * s / 2
    body += art.text(lx, 545, "YOURS", 30, art.ACC, 500, font="mono", ls=8) + f'<path d="M{lx} 562 L{lx} 590 M{lx-12} 578 L{lx} 592 L{lx+12} 578" stroke="{art.ACC}" stroke-width="5" fill="none"/>'
    body += f'<line x1="0" y1="760" x2="{W}" y2="760" stroke="{art.DIM}" stroke-width="4"/>'
    body += art.text(W / 2, 865, CH["name"].upper(), 92, art.INK, 900, ls=10)
    body += art.text(W / 2, 918, CH["tagline"].upper(), 28, art.GRAY, 500, font="mono", ls=6)
    return svg(W, H, body)

def watermark():
    return svg(150, 150, mascot(75, 84, 0.24), bg=art.ACC)

def highlight(label, icon):
    body = f'<circle cx="540" cy="960" r="300" fill="#141417" stroke="{art.ACC}" stroke-width="10"/>' + icon
    body += art.text(540, 1380, label, 64, art.INK, 900, ls=8)
    return svg(1080, 1920, body)

def cover():
    body = mascot(540, 820, 1.4, body=art.INK, visor=art.BG, badge=art.ACC)
    body += art.text(540, 1260, CH["name"].upper(), 66, art.INK, 900, ls=4)
    body += art.text(540, 1330, "NOTICES FOR THINGS", 34, art.GRAY, 500, font="mono", ls=5)
    body += art.text(540, 1380, "YOUR HOUSE WON'T TELL YOU.", 34, art.GRAY, 500, font="mono", ls=5)
    body += art.text(540, 1560, "NEW NOTICE EVERY WEEK", 36, art.ACC, 800, ls=6)
    return svg(1080, 1920, body)

def run():
    OUT.mkdir(exist_ok=True)
    rule_icon = art.text(540, 1035, "7", 240, art.ACC, 900)
    notice_icon = art.house(410, 1090, 1.2, lit=True)
    new_icon = art.notif(330, 900, "New notice", CH["handle"], 560, 0.75)
    jobs = [
        ("avatar-800.png", avatar(800), 800, 800),
        ("avatar-1080.png", avatar(1080), 1080, 1080),
        ("youtube-banner.png", banner(), 2560, 1440),
        ("watermark-150.png", watermark(), 150, 150),
        ("highlight-rules.png", highlight("RULES", rule_icon), 1080, 1920),
        ("highlight-notices.png", highlight("NOTICES", notice_icon), 1080, 1920),
        ("highlight-new.png", highlight("NEW", new_icon), 1080, 1920),
        ("tiktok-ig-cover.png", cover(), 1080, 1920),
    ]
    jp = OUT / "jobs.json"
    jp.write_text(json.dumps([{"html": h, "out": str(OUT / n), "w": w, "h": hh} for n, h, w, hh in jobs]))
    for n, *_ in jobs:
        (OUT / n).unlink(missing_ok=True)
    subprocess.run(["node", str(HERE / "render.js"), str(jp)], check=True)
    jp.unlink()

if __name__ == "__main__":
    run()
