"""Idea #1, way 3: "The Table". Usage: python3 stick_figure_01_table.py out.mp4"""
import math, sys
from stick_lib import *

FEET = 1720          # seated figures' feet are hidden behind the tablecloth
TOP = 1620           # table top
SEATS = [130, 250, 370, 710, 830, 950]   # guests (main sits at 540)
LEAVE = {0: 4.5, 5: 4.9, 1: 5.5, 4: 5.9}
STAY = {2: 420, 3: 660}                  # seat index -> final x
GH = 260

def table(d, x0, x1, fi):
    j = jit(fi * 7 + 5)
    d.rectangle([x0 * S, TOP * S, x1 * S, 1760 * S], fill=BG)
    d.line([((x0 - 15 + j()) * S, (TOP + j()) * S), ((x1 + 15 + j()) * S, (TOP + j()) * S)], fill=INK, width=8 * S)
    d.line([((x0 + j()) * S, TOP * S), ((x0 + 10 + j()) * S, 1760 * S)], fill=INK, width=6 * S)
    d.line([((x1 + j()) * S, TOP * S), ((x1 - 10 + j()) * S, 1760 * S)], fill=INK, width=6 * S)

def cup(d, x, alpha):
    if alpha <= 0: return
    c = tuple(int(lerp(BG[i], INK[i], alpha)) for i in range(3))
    d.rectangle([(x - 14) * S, (TOP - 34) * S, (x + 14) * S, (TOP - 4) * S], outline=c, width=5 * S)

def frame(t):
    img = Image.new("RGBA", (W * S, H * S), BG + (255,))
    fi = int(t * FPS) // 3
    glow(img, t, box=(160, 1300, 920, 1820))
    d = ImageDraw.Draw(img)
    j = jit(fi * 7 + 2)
    d.line([((40 + j()) * S, (1762 + j()) * S), ((1040 + j()) * S, (1762 + j()) * S)], fill=(200, 192, 180), width=4 * S)

    hug = prog(t, 16.0, 16.8)
    # guests
    for i, sx in enumerate(SEATS):
        seed = fi * 31 + i
        if i in STAY:
            g = prog(t, 12.8, 14.8)
            x = lerp(sx, STAY[i], g)
            if t < 3.6:
                c = math.sin(t * 10 + i)
                pa = (1.9 + 0.3 * c, 1.9 - 0.3 * c, abs(c) * 7)
            else:
                pa = (0.6, 0.6, 0)
            aL, aR = pa[0], pa[1]
            if i == 2: aR = lerp(aR, 1.35, hug)
            else: aL = lerp(aL, 1.35, hug)
            figure(d, x, FEET, GH, aL, aR, 0.12, 0.12, seed, bob=pa[2])
        else:
            st = LEAVE[i]
            if t < st:
                if t < 3.6:
                    c = math.sin(t * 10 + i * 1.7)
                    figure(d, sx, FEET, GH, 1.9 + 0.3 * c, 1.9 - 0.3 * c, 0.12, 0.12, seed, bob=abs(c) * 7)
                else:
                    figure(d, sx, FEET, GH, 0.6, 0.6, 0.12, 0.12, seed)
            else:
                rise = prog(t, st, st + 0.4) * 25
                x = sx + (-1 if sx < 540 else 1) * max(0, t - st - 0.4) * 240
                if -150 < x < W + 150:
                    p = walk_pose(max(0, t - st - 0.4) * 9)
                    figure(d, x, FEET - rise, GH, p[0], p[1], p[2], p[3], seed, bob=p[4])

    # main figure at the middle seat: standing and telling a story, then sits
    if t < 3.6:
        wv = math.sin(t * 7)
        aL, aR, b, mh = 2.3 + 0.3 * wv, 1.0 - 0.4 * wv, abs(wv) * 8, 340
    else:
        a = prog(t, 3.6, 4.4)
        aL, aR, b, mh = lerp(2.3, 0.6, a), lerp(1.0, 0.6, a), 0, lerp(340, 265, a)
    aL, aR = lerp(aL, 1.35, hug), lerp(aR, 1.35, hug)
    figure(d, 540, FEET, mh, aL, aR, 0.12, 0.12, fi * 31 + 99, bob=b, face=True)

    # table shrinks after everyone else has gone
    g = prog(t, 12.6, 14.6)
    table(d, lerp(70, 320, g), lerp(1010, 760, g), fi)
    for i, sx in enumerate(SEATS):
        if i in STAY:
            cup(d, lerp(sx, STAY[i], prog(t, 12.8, 14.8)) + 35, 1)
        else:
            cup(d, sx + 35, 1 - prog(t, LEAVE[i] + 2.5, LEAVE[i] + 3.2))
    cup(d, 575, 1)

    heart(img, t, cy0=1300)
    captions(img, t)
    return img.convert("RGB").resize((W, H), Image.LANCZOS)

if __name__ == "__main__":
    render(frame, sys.argv[1])
