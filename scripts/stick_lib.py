import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, S, FPS, DUR = 1080, 1920, 2, 30, 23.0
BG = (244, 239, 230)
INK = (30, 30, 30)
ACCENT = (214, 120, 40)
LIGHT = (255, 226, 140)
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
f_main = ImageFont.truetype(FONT, 82 * S)
f_big = ImageFont.truetype(FONT, 104 * S)

def clamp(v, a=0, b=1): return max(a, min(b, v))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def prog(t, a, b): return ease((t - a) / (b - a))

def jit(seed):
    r = random.Random(seed)
    return lambda: r.uniform(-1.6, 1.6)

def figure(d, x, feet, h, armL, armR, legL, legR, seed, alpha=1.0, bob=0, face=False):
    if alpha <= 0: return
    j = jit(seed)
    col = tuple(int(lerp(BG[i], INK[i], alpha)) for i in range(3))
    w = max(2, int(h * 0.045)) * S
    r = h * 0.12
    feet -= bob
    hip = (x, feet - h * 0.45)
    neck = (x, feet - h + 2 * r)
    sh = (x, neck[1] + h * 0.06)
    P = lambda p: ((p[0] + j()) * S, (p[1] + j()) * S)
    hc = (x + j(), feet - h + r + j())
    d.ellipse([(hc[0] - r) * S, (hc[1] - r) * S, (hc[0] + r) * S, (hc[1] + r) * S], outline=col, width=w)
    d.line([P(neck), P(hip)], fill=col, width=w)
    if face:
        er = max(2.5, r * 0.11)
        for ex in (-0.35, 0.35):
            d.ellipse([(hc[0] + ex * r - er) * S, (hc[1] - 0.15 * r - er) * S, (hc[0] + ex * r + er) * S, (hc[1] - 0.15 * r + er) * S], fill=col)
        d.line([((hc[0] - 0.3 * r) * S, (hc[1] + 0.4 * r) * S), ((hc[0] + 0.3 * r) * S, (hc[1] + 0.4 * r) * S)], fill=col, width=max(2, w // 2))
    al, ll = h * 0.32, h * 0.45
    for ang, side in ((armL, -1), (armR, 1)):
        e = (sh[0] + side * math.sin(ang) * al * 0.5, sh[1] + math.cos(ang) * al * 0.5)
        hnd = (sh[0] + side * math.sin(ang * 1.08) * al, sh[1] + math.cos(ang * 1.08) * al)
        d.line([P(sh), P(e), P(hnd)], fill=col, width=w, joint="curve")
    for ang, side in ((legL, -1), (legR, 1)):
        k = (hip[0] + side * math.sin(ang) * ll * 0.5, hip[1] + math.cos(ang) * ll * 0.5)
        ft = (hip[0] + side * math.sin(ang) * ll, hip[1] + math.cos(ang) * ll)
        d.line([P(hip), P(k), P(ft)], fill=col, width=w, joint="curve")
    for q in (sh, hip):
        d.ellipse([(q[0] - w / S / 2) * S, (q[1] - w / S / 2) * S, (q[0] + w / S / 2) * S, (q[1] + w / S / 2) * S], fill=col)

def walk_pose(phase):
    s = math.sin(phase)
    return 0.3 - 0.35 * s, 0.3 + 0.35 * s, 0.12 + 0.38 * s, 0.12 - 0.38 * s, abs(math.cos(phase)) * 6

def text_block(img, lines, t0, t1, t, font, y, colors=None):
    a = prog(t, t0, t0 + 0.45) * (1 - prog(t, t1 - 0.4, t1))
    if a <= 0: return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    yy = (y + (1 - prog(t, t0, t0 + 0.45)) * 30) * S
    for i, (ln, start) in enumerate(lines):
        la = a * prog(t, start, start + 0.4)
        if la <= 0:
            yy += font.size * 1.18; continue
        c = (colors[i] if colors else INK) + (int(255 * la),)
        bw = d.textlength(ln, font=font)
        d.text(((W * S - bw) / 2, yy), ln, font=font, fill=c)
        yy += font.size * 1.18
    img.alpha_composite(layer)


def captions(img, t):
    text_block(img, [("You didn't lose friends.", 0.2), ("You lost your audience.", 2.0)], 0.2, 7.6, t, f_main, 330,
               colors=[INK, ACCENT])
    text_block(img, [("When you stopped", 7.8), ("performing, the people", 7.8), ("who liked the act", 9.3),
                     ("stopped showing up.", 9.3)], 7.8, 12.6, t, f_main, 290)
    text_block(img, [("The ones who stayed", 12.9), ("were watching you.", 12.9), ("Not the show.", 14.8)],
               12.9, 18.0, t, f_main, 320, colors=[INK, INK, ACCENT])
    text_block(img, [("Small circle.", 18.3), ("Real people.", 19.2)], 18.3, DUR + 1, t, f_big, 380,
               colors=[INK, ACCENT])

def glow(img, t, box=(190, 1380, 890, 1830)):
    a = prog(t, 15.5, 17.5)
    if a <= 0: return
    L = Image.new("RGBA", img.size, LIGHT + (0,))
    ImageDraw.Draw(L).ellipse([v * S for v in box], fill=LIGHT + (int(170 * a),))
    img.alpha_composite(L.filter(ImageFilter.GaussianBlur(60 * S)))

def heart(img, t, cx=540, cy0=1360):
    hp = prog(t, 16.6, 17.3)
    if hp <= 0: return
    sc = (1 + 0.15 * math.sin(clamp((t - 16.6) / 0.7) * math.pi)) * hp
    cy, rr = cy0 - 30 * hp, 34 * sc
    L = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(L)
    col = ACCENT + (int(255 * hp),)
    ld.ellipse([(cx - rr * 1.9) * S, (cy - rr) * S, cx * S, (cy + rr * 0.9) * S], fill=col)
    ld.ellipse([cx * S, (cy - rr) * S, (cx + rr * 1.9) * S, (cy + rr * 0.9) * S], fill=col)
    ld.polygon([((cx - rr * 1.85) * S, (cy + rr * 0.1) * S), ((cx + rr * 1.85) * S, (cy + rr * 0.1) * S),
                (cx * S, (cy + rr * 2.1) * S)], fill=col)
    img.alpha_composite(L)

def render(frame, out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                           "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                           "-c:a", "aac", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for k in range(int(DUR * FPS)):
        ff.stdin.write(frame(k / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    print("done", out)
