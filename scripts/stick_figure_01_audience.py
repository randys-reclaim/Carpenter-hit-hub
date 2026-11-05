import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, S, FPS, DUR = 1080, 1920, 2, 30, 23.0
OUT = sys.argv[1]
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

def figure(d, x, feet, h, armL, armR, legL, legR, seed, alpha=1.0, bob=0):
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

# audience: x positions, which ones stay
AUD = [110, 230, 350, 470, 610, 730, 850, 970]
STAY = {3, 5}
LEAVE_START = {0: 4.3, 7: 4.6, 1: 5.2, 6: 5.6, 2: 6.3, 4: 6.9}
AUD_Y, AUD_H = 1730, 185

def frame(t):
    img = Image.new("RGBA", (W * S, H * S), BG + (255,))
    fi = int(t * FPS) // 3  # boiling-line seed (12fps wobble)

    stage_a = 1 - prog(t, 12.6, 14.2)
    spot_a = (1 - prog(t, 3.6, 5.0)) * 0.85 + 0.15 * (1 - prog(t, 8, 10))
    spot_a *= stage_a
    glow_a = prog(t, 15.5, 17.5)

    # spotlight cone
    if spot_a > 0:
        L = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(L)
        ld.polygon([(470 * S, 700 * S), (610 * S, 700 * S), (800 * S, 1330 * S), (280 * S, 1330 * S)],
                   fill=LIGHT + (int(150 * spot_a),))
        img.alpha_composite(L)
    # warm glow at the end
    if glow_a > 0:
        L = Image.new("RGBA", img.size, LIGHT + (0,))
        ld = ImageDraw.Draw(L)
        ld.ellipse([190 * S, 1380 * S, 890 * S, 1830 * S], fill=LIGHT + (int(170 * glow_a),))
        L = L.filter(ImageFilter.GaussianBlur(60 * S))
        img.alpha_composite(L)

    d = ImageDraw.Draw(img)
    # stage
    if stage_a > 0:
        c = tuple(int(lerp(BG[i], INK[i], stage_a)) for i in range(3))
        j = jit(fi * 7 + 1)
        d.line([((290 + j()) * S, (1330 + j()) * S), ((790 + j()) * S, (1330 + j()) * S)], fill=c, width=8 * S)
        d.line([((300 + j()) * S, 1330 * S), ((300 + j()) * S, 1420 * S)], fill=c, width=6 * S)
        d.line([((780 + j()) * S, 1330 * S), ((780 + j()) * S, 1420 * S)], fill=c, width=6 * S)
    # ground line
    j = jit(fi * 7 + 2)
    d.line([((60 + j()) * S, (AUD_Y + 4 + j()) * S), ((1020 + j()) * S, (AUD_Y + 4 + j()) * S)], fill=(200, 192, 180), width=4 * S)

    # main performer
    if t < 3.6:
        wv = math.sin(t * 7)
        pose = (2.25 + 0.25 * wv, 2.25 - 0.25 * wv, 0.22, 0.22, abs(math.sin(t * 7)) * 8)
    else:
        a = prog(t, 3.6, 4.4)
        pose = (lerp(2.25, 0.18, a), lerp(2.25, 0.18, a), 0.12, 0.12, 0)
    mx, mfeet, mh = 540, 1330, 300
    m = prog(t, 13.0, 15.0)
    if m > 0:
        mfeet = lerp(1330, AUD_Y, m) - math.sin(m * math.pi) * 90
        mh = lerp(300, 215, m)
    armL, armR = pose[0], pose[1]
    hug = prog(t, 16.0, 16.8)
    armL, armR = lerp(armL, 1.25, hug), lerp(armR, 1.25, hug)
    figure(d, mx, mfeet, mh, armL, armR, pose[2], pose[3], fi * 31 + 99, bob=pose[4])

    # audience
    for i, ax in enumerate(AUD):
        seed = fi * 31 + i
        if i in STAY:
            target = 375 if i == 3 else 705
            g = prog(t, 13.4, 15.6)
            x = lerp(ax, target, g)
            hh = lerp(AUD_H, 205, g)
            walking = 0 < g < 1
            if walking:
                aL, aR, lL, lR, b = walk_pose(t * 9 + i)
            elif t < 3.6:
                aL, aR, lL, lR, b = 2.3 + 0.2 * math.sin(t * 8 + i), 2.3 - 0.2 * math.sin(t * 8 + i), 0.15, 0.15, 0
            else:
                aL, aR, lL, lR, b = 0.2, 0.2, 0.12, 0.12, 0
            if hug > 0:
                if i == 3: aR = lerp(aR, 1.3, hug)
                else: aL = lerp(aL, 1.3, hug)
            figure(d, x, AUD_Y, hh, aL, aR, lL, lR, seed, bob=b)
        else:
            st = LEAVE_START[i]
            if t < st:
                if t < 3.6:
                    cl = math.sin(t * 9 + i * 1.7)
                    figure(d, ax, AUD_Y, AUD_H, 2.2 + 0.25 * cl, 2.2 - 0.25 * cl, 0.15, 0.15, seed,
                           bob=abs(cl) * 6)
                else:
                    figure(d, ax, AUD_Y, AUD_H, 0.2, 0.2, 0.12, 0.12, seed)
            else:
                dirn = -1 if ax < 540 else 1
                x = ax + dirn * (t - st) * 260
                if -150 < x < W + 150:
                    aL, aR, lL, lR, b = walk_pose((t - st) * 9)
                    figure(d, x, AUD_Y, AUD_H, aL, aR, lL, lR, seed, bob=b)

    # heart
    hp = prog(t, 16.6, 17.3)
    if hp > 0:
        sc = (1 + 0.15 * math.sin(clamp((t - 16.6) / 0.7) * math.pi)) * hp
        cx, cy, rr = 540, 1360 - 30 * hp, 34 * sc
        L = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(L)
        col = ACCENT + (int(255 * hp),)
        ld.ellipse([(cx - rr * 1.9) * S, (cy - rr) * S, (cx) * S, (cy + rr * 0.9) * S], fill=col)
        ld.ellipse([(cx) * S, (cy - rr) * S, (cx + rr * 1.9) * S, (cy + rr * 0.9) * S], fill=col)
        ld.polygon([((cx - rr * 1.85) * S, (cy + rr * 0.1) * S), ((cx + rr * 1.85) * S, (cy + rr * 0.1) * S),
                    (cx * S, (cy + rr * 2.1) * S)], fill=col)
        img.alpha_composite(L)

    # text
    text_block(img, [("You didn't lose friends.", 0.2), ("You lost your audience.", 2.0)], 0.2, 7.6, t, f_main, 330,
               colors=[INK, ACCENT])
    text_block(img, [("When you stopped", 7.8), ("performing, the people", 7.8), ("who liked the act", 9.3),
                     ("stopped showing up.", 9.3)], 7.8, 12.6, t, f_main, 290)
    text_block(img, [("The ones who stayed", 12.9), ("were watching you.", 12.9), ("Not the show.", 14.8)],
               12.9, 18.0, t, f_main, 320, colors=[INK, INK, ACCENT])
    text_block(img, [("Small circle.", 18.3), ("Real people.", 19.2)], 18.3, DUR + 1, t, f_big, 380,
               colors=[INK, ACCENT])

    return img.convert("RGB").resize((W, H), Image.LANCZOS)

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                       "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                       "-c:a", "aac", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for k in range(n):
    ff.stdin.write(frame(k / FPS).tobytes())
ff.stdin.close(); ff.wait()
print("done", OUT)
