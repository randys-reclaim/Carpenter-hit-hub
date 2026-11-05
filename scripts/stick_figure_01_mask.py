"""Idea #1, way 2: "The Mask". Usage: python3 stick_figure_01_mask.py out.mp4"""
import math, sys
from stick_lib import *

GROUND = 1730
CROWD = [80, 190, 300, 395, 685, 780, 890, 1000]
STAY = {3, 4}
LEAVE = {0: 4.6, 7: 4.9, 1: 5.5, 6: 5.9, 2: 6.6, 5: 7.1}
CH = 185

def mask(d, cx, cy, r, alpha, seed):
    if alpha <= 0: return
    j = jit(seed)
    fill = tuple(int(lerp(BG[i], LIGHT[i], alpha)) for i in range(3))
    ink = tuple(int(lerp(BG[i], INK[i], alpha)) for i in range(3))
    w = 7 * S
    d.ellipse([(cx - r + j()) * S, (cy - r + j()) * S, (cx + r + j()) * S, (cy + r + j()) * S], fill=fill, outline=ink, width=w)
    for ex in (-0.38, 0.38):  # happy closed eyes
        d.arc([(cx + ex * r - 0.17 * r) * S, (cy - 0.35 * r) * S, (cx + ex * r + 0.17 * r) * S, (cy - 0.05 * r) * S],
              200, 340, fill=ink, width=w)
    d.arc([(cx - 0.55 * r) * S, (cy - 0.35 * r) * S, (cx + 0.55 * r) * S, (cy + 0.6 * r) * S], 20, 160, fill=ink, width=w)

def frame(t):
    img = Image.new("RGBA", (W * S, H * S), BG + (255,))
    fi = int(t * FPS) // 3
    glow(img, t)
    d = ImageDraw.Draw(img)
    j = jit(fi * 7 + 2)
    d.line([((60 + j()) * S, (GROUND + 4 + j()) * S), ((1020 + j()) * S, (GROUND + 4 + j()) * S)], fill=(200, 192, 180), width=4 * S)

    # wooden crate the main figure stands on
    ca = 1 - prog(t, 12.6, 13.4)
    if ca > 0:
        cc = tuple(int(lerp(BG[i], INK[i], ca)) for i in range(3))
        jj = jit(fi * 7 + 9)
        d.rectangle([(465 + jj()) * S, 1500 * S, (615 + jj()) * S, GROUND * S], outline=cc, width=7 * S)
        d.line([(465 * S, 1500 * S), (615 * S, GROUND * S)], fill=cc, width=5 * S)
        d.line([(615 * S, 1500 * S), (465 * S, GROUND * S)], fill=cc, width=5 * S)
    # main figure (center, slightly back, larger)
    m = prog(t, 13.0, 15.0)
    mfeet = lerp(1500, GROUND, m) - math.sin(m * math.pi) * 60
    mh = lerp(300, 215, m)
    if t < 3.6:
        wv = math.sin(t * 7)
        aL, aR, b = 2.25 + 0.25 * wv, 2.25 - 0.25 * wv, abs(wv) * 8
    else:
        a = prog(t, 3.6, 4.4)
        aL, aR, b = lerp(2.25, 0.18, a), lerp(2.25, 0.18, a), 0
    hug = prog(t, 16.0, 16.8)
    aL, aR = lerp(aL, 1.25, hug), lerp(aR, 1.25, hug)
    figure(d, 540, mfeet, mh, aL, aR, 0.12, 0.12, fi * 31 + 99, bob=b, face=True)

    # the mask: worn until 3.6, lifted off, drops to the ground, fades
    head_y = mfeet - b - mh + mh * 0.12
    r = 78
    if t < 3.9:
        mask(d, 540, head_y, r, 1, fi * 13)
    else:
        lift = prog(t, 3.9, 4.5)
        fall = prog(t, 4.5, 5.1)
        x = lerp(lerp(540, 690, lift), 590, fall)
        y = lerp(head_y, head_y - 90, lift)
        y = lerp(y, 1500 - 40, fall)  # lands on the riser floor
        mask(d, x, y, lerp(r, 60, fall), 1 - prog(t, 11.5, 13.0), fi * 13)

    # crowd
    for i, cx in enumerate(CROWD):
        seed = fi * 31 + i
        if i in STAY:
            target = 375 if i == 3 else 705
            g = prog(t, 13.4, 15.6)
            x, hh = lerp(cx, target, g), lerp(CH, 205, g)
            if 0 < g < 1:
                pa = walk_pose(t * 9 + i)
            elif t < 3.6:
                c = math.sin(t * 8 + i)
                pa = (2.2 + 0.25 * c, 2.2 - 0.25 * c, 0.15, 0.15, abs(c) * 6)
            else:
                pa = (0.2, 0.2, 0.12, 0.12, 0)
            aL2, aR2 = pa[0], pa[1]
            if i == 3: aR2 = lerp(aR2, 1.3, hug)
            else: aL2 = lerp(aL2, 1.3, hug)
            figure(d, x, GROUND, hh, aL2, aR2, pa[2], pa[3], seed, bob=pa[4])
        else:
            st = LEAVE[i]
            if t < st:
                if t < 3.6:
                    c = math.sin(t * 9 + i * 1.7)
                    figure(d, cx, GROUND, CH, 2.2 + 0.25 * c, 2.2 - 0.25 * c, 0.15, 0.15, seed, bob=abs(c) * 6)
                else:
                    figure(d, cx, GROUND, CH, 0.2, 0.2, 0.12, 0.12, seed)
            else:
                x = cx + (-1 if cx < 540 else 1) * (t - st) * 260
                if -150 < x < W + 150:
                    p = walk_pose((t - st) * 9)
                    figure(d, x, GROUND, CH, p[0], p[1], p[2], p[3], seed, bob=p[4])

    heart(img, t)
    captions(img, t)
    return img.convert("RGB").resize((W, H), Image.LANCZOS)

if __name__ == "__main__":
    render(frame, sys.argv[1])
