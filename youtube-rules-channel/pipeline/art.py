"""Scene library: every frame is flat white line art on black with one yellow
danger light. Scenes are drawn on a 1920x1080 canvas; the caption band
(y > 880) is left empty for the renderer.

Each template is a function taking string params (from the shot tags in a
script) and returning SVG markup. Add new templates with @scene("name").
"""
import html, math

BG, INK, GRAY, DIM, ACC, REC = "#0B0B0C", "#F2F2F2", "#8E8E93", "#3A3A3E", "#FFC400", "#FF3B30"
GREEN = "#34C759"
FLOOR = 760

DEFS = f"""<defs>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="40"/></filter>
<radialGradient id="lensbg" cx="50%" cy="55%" r="60%"><stop offset="0" stop-color="#26262a"/><stop offset="1" stop-color="{BG}"/></radialGradient>
</defs>"""

SCENES = {}
def scene(name):
    def reg(fn):
        SCENES[name] = fn
        return fn
    return reg

def esc(t): return html.escape(str(t))
def on(p, k, default="0"): return str(p.get(k, default)) not in ("0", "", "no", "off", "false")

# ---------------------------------------------------------------- primitives

def text(x, y, t, size=40, fill=INK, weight=800, anchor="middle", font="Montserrat", ls=0, extra=""):
    fam = "JetBrains Mono, monospace" if font == "mono" else "Montserrat, Inter, sans-serif"
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{weight}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{esc(t)}</text>')

def glow(x, y, r=120, col=ACC, op=0.35):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}" opacity="{op}" filter="url(#soft)"/>'

def floor(y=FLOOR):
    return f'<line x1="0" y1="{y}" x2="1920" y2="{y}" stroke="{DIM}" stroke-width="5"/>'

def cross(x, y, s=1.0):
    d = 90 * s
    return (f'<g stroke="{ACC}" stroke-width="{22*s}" stroke-linecap="round" filter="url(#glow)">'
            f'<line x1="{x-d}" y1="{y-d}" x2="{x+d}" y2="{y+d}"/><line x1="{x+d}" y1="{y-d}" x2="{x-d}" y2="{y+d}"/></g>')

def fig(x, y, s=1.0, pose="stand", face=None, col=INK, op=1.0):
    """Stick figure standing on (x, y)."""
    w = 18 * s
    hy, neck, hip = y - 205 * s, y - 165 * s, y - 80 * s
    sh = neck + 15 * s
    L = lambda x1, y1, x2, y2: f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>'
    if pose == "walk":
        limbs = L(x, hip, x - 30*s, y) + L(x, hip, x + 35*s, y) + L(x, sh, x - 32*s, hip + 5*s) + L(x, sh, x + 34*s, hip)
    elif pose == "wave":
        limbs = L(x, hip, x - 25*s, y) + L(x, hip, x + 25*s, y) + L(x, sh, x - 30*s, hip + 10*s) + f'<path d="M{x} {sh} L{x+55*s} {sh-35*s} L{x+70*s} {sh-105*s}" fill="none"/>'
    elif pose == "kneel":
        hip = y - 55 * s; neck = hip - 85 * s; sh = neck + 15 * s; hy = neck - 40 * s
        limbs = L(x, hip, x + 45*s, hip) + L(x + 45*s, hip, x + 45*s, y) + L(x, hip, x - 20*s, y) + L(x, sh, x + 70*s, sh + 30*s)
    elif pose == "kick":
        limbs = L(x, hip, x - 25*s, y) + L(x, hip, x + 70*s, y - 40*s) + L(x, sh, x - 40*s, hip - 10*s) + L(x, sh, x + 30*s, hip)
    elif pose == "point":
        limbs = L(x, hip, x - 25*s, y) + L(x, hip, x + 25*s, y) + L(x, sh, x - 30*s, hip + 10*s) + L(x, sh, x + 90*s, sh + 10*s)
    elif pose == "sit":
        hip = y - 70 * s; neck = hip - 85 * s; sh = neck + 15 * s; hy = neck - 40 * s
        limbs = L(x, hip, x + 60*s, hip) + L(x + 60*s, hip, x + 60*s, y) + L(x, sh, x + 55*s, sh + 45*s)
    else:
        limbs = L(x, hip, x - 25*s, y) + L(x, hip, x + 25*s, y) + L(x, sh, x - 30*s, hip + 10*s) + L(x, sh, x + 30*s, hip + 10*s)
    body = L(x, neck, x, hip)
    out = (f'<g opacity="{op}" filter="url(#glow)"><g stroke="{col}" stroke-width="{w}" stroke-linecap="round" fill="none">{body}{limbs}</g>'
           f'<circle cx="{x}" cy="{hy}" r="{38*s}" fill="{col}"/>')
    if face == "eyes":
        out += f'<circle cx="{x-12*s}" cy="{hy-2*s}" r="{4.5*s}" fill="{BG}"/><circle cx="{x+12*s}" cy="{hy-2*s}" r="{4.5*s}" fill="{BG}"/>'
    elif face == "wide":
        out += f'<circle cx="{x-24*s}" cy="{hy-2*s}" r="{5*s}" fill="{BG}"/><circle cx="{x+24*s}" cy="{hy-2*s}" r="{5*s}" fill="{BG}"/>'
    elif face == "sleep":
        out += f'<line x1="{x-6*s}" y1="{hy}" x2="{x+14*s}" y2="{hy}" stroke="{BG}" stroke-width="{4*s}" stroke-linecap="round"/>'
    return out + "</g>"

def door(x, y, w=170, h=380, open_=0.0, under=False, knob_glow=False):
    out = ""
    if under:
        out += glow(x + w/2, y + h, 140, ACC, 0.45) + f'<rect x="{x+10}" y="{y+h-6}" width="{w-20}" height="6" fill="{ACC}"/>'
    out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}" stroke="{INK}" stroke-width="7"/>'
    if open_ > 0:
        ow = w * (1 - open_)
        out += f'<rect x="{x+3}" y="{y+3}" width="{w-6}" height="{h-6}" fill="#222226"/>'
        out += f'<path d="M{x} {y} L{x+ow} {y+25} L{x+ow} {y+h-25} L{x} {y+h}Z" fill="{BG}" stroke="{INK}" stroke-width="6"/>'
    else:
        out += f'<rect x="{x+25}" y="{y+30}" width="{w-50}" height="{h*0.35}" fill="none" stroke="{DIM}" stroke-width="4"/>'
        out += f'<rect x="{x+25}" y="{y+h*0.5}" width="{w-50}" height="{h*0.42}" fill="none" stroke="{DIM}" stroke-width="4"/>'
        kc = ACC if knob_glow else INK
        flt = 'filter="url(#glow)"' if knob_glow else ""
        out += f'<rect x="{x+w-55}" y="{y+h*0.5-8}" width="40" height="14" rx="7" fill="{kc}" {flt}/>'
    return out

def window(x, y, w=220, h=260, moon=True, lit=False, hand=False):
    fill = ACC if lit else "#141417"
    out = ""
    if lit: out += glow(x + w/2, y + h/2, 160, ACC, 0.35)
    out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" fill-opacity="{0.85 if lit else 1}" stroke="{GRAY}" stroke-width="6"/>'
    out += f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="{GRAY}" stroke-width="4"/>'
    if moon and not lit:
        out += f'<circle cx="{x+w*0.72}" cy="{y+70}" r="24" fill="{ACC}"/><circle cx="{x+w*0.72+12}" cy="{y+60}" r="22" fill="#141417"/>'
    if hand:
        out += f'<g transform="translate({x+w*0.3} {y+h*0.55})" fill="{INK}" filter="url(#glow)"><rect x="-14" y="0" width="28" height="60" rx="10"/><circle cx="0" cy="-6" r="22"/></g>'
    return out

def house(x, y, s=1.0, lit=False, win=True):
    w, h = 220 * s, 170 * s
    out = f'<path d="M{x} {y} L{x} {y-h} L{x+w/2} {y-h-95*s} L{x+w} {y-h} L{x+w} {y}Z" fill="{BG}" stroke="{INK if lit else GRAY}" stroke-width="{7*s}" stroke-linejoin="round"/>'
    if win:
        wx, wy = x + w/2 - 35*s, y - h + 35*s
        if lit:
            out += glow(wx + 35*s, wy + 30*s, 110*s, ACC, 0.5)
        out += f'<rect x="{wx}" y="{wy}" width="{70*s}" height="{60*s}" fill="{ACC if lit else "#141417"}" stroke="{INK if lit else GRAY}" stroke-width="{5*s}"/>'
    return out

def bed(x, y, person="sleep", hand_x=False):
    """Side-view bed; (x, y) is the floor point of the headboard."""
    out = f'<rect x="{x}" y="{y-230}" width="26" height="230" rx="10" fill="{INK}"/>'
    out += f'<rect x="{x+20}" y="{y-120}" width="620" height="22" fill="{INK}"/><rect x="{x+614}" y="{y-150}" width="26" height="150" rx="10" fill="{INK}"/>'
    if person == "sleep":
        out += f'<rect x="{x+110}" y="{y-190}" width="520" height="75" rx="30" fill="#8a8a90" stroke="{INK}" stroke-width="6"/>'
        out += f'<circle cx="{x+85}" cy="{y-175}" r="46" fill="{INK}" stroke="{BG}" stroke-width="5"/><line x1="{x+70}" y1="{y-178}" x2="{x+96}" y2="{y-178}" stroke="{BG}" stroke-width="5" stroke-linecap="round"/>'
    elif person == "awake":
        out += f'<rect x="{x+110}" y="{y-190}" width="520" height="75" rx="30" fill="#8a8a90" stroke="{INK}" stroke-width="6"/>'
        out += f'<circle cx="{x+85}" cy="{y-175}" r="46" fill="{INK}" stroke="{BG}" stroke-width="5"/><circle cx="{x+72}" cy="{y-180}" r="6" fill="{BG}"/><circle cx="{x+98}" cy="{y-180}" r="6" fill="{BG}"/>'
    elif person == "lump":
        out += f'<path d="M{x+30} {y-118} Q{x+40} {y-250} {x+200} {y-235} Q{x+420} {y-225} {x+610} {y-150} L{x+610} {y-118}Z" fill="#8a8a90" stroke="{INK}" stroke-width="6"/>'
    elif person == "climb":
        out += fig(x + 330, y - 120, 1.0, "sit", "eyes")
    else:
        out += f'<rect x="{x+40}" y="{y-150}" width="580" height="34" rx="14" fill="#5a5a60"/>'
    if hand_x:
        out += cross(x + 360, y - 260, 0.6)
    return out

def nightstand(x, y, device="phone", label="", glow_on=False):
    out = f'<rect x="{x}" y="{y-150}" width="170" height="150" fill="{BG}" stroke="{INK}" stroke-width="7"/><line x1="{x}" y1="{y-90}" x2="{x+170}" y2="{y-90}" stroke="{INK}" stroke-width="5"/>'
    if glow_on: out += glow(x + 85, y - 175, 150, ACC, 0.45)
    if device == "phone":
        out += f'<rect x="{x+45}" y="{y-172}" width="80" height="20" rx="6" fill="{ACC if glow_on else INK}"/>'
    elif device == "clock":
        out += f'<rect x="{x+15}" y="{y-235}" width="140" height="80" rx="10" fill="{BG}" stroke="{INK}" stroke-width="6"/>'
        out += text(x + 85, y - 178, label or "6:12", 44, REC if label.startswith(("25", "3:")) else INK, 700, font="mono")
    return out

def notif(x, y, title, sub, w=560, s=1.0):
    h = 120 * s
    return (f'<g filter="url(#glow)"><rect x="{x}" y="{y}" width="{w*s}" height="{h}" rx="{26*s}" fill="{INK}"/></g>'
            f'<circle cx="{x+60*s}" cy="{y+h/2}" r="{30*s}" fill="{BG}"/><circle cx="{x+60*s}" cy="{y+h/2}" r="{11*s}" fill="{ACC}"/>'
            + text(x + 110*s, y + 52*s, title, 30*s, BG, 800, "start")
            + text(x + 110*s, y + 90*s, sub, 24*s, "#55555a", 700, "start"))

def phone(x, y, w=420, h=760, inner=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="54" fill="{BG}" stroke="{INK}" stroke-width="9"/>'
            f'<rect x="{x+w/2-50}" y="{y+22}" width="100" height="16" rx="8" fill="{DIM}"/>' + inner)

def pips(n, x=960, y=0):
    return ""  # pips live in the HUD

def tire(cx, cy, r=140, face=None, cap=None, op=1.0, squash=False, fill_glow=False):
    ry = r * (0.86 if squash else 1)
    out = ""
    if fill_glow: out += glow(cx, cy, r * 1.3, ACC, 0.3)
    out += f'<g opacity="{op}"><ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{ry}" fill="{BG}" stroke="{INK}" stroke-width="{r*0.24}"/>'
    out += f'<ellipse cx="{cx}" cy="{cy}" rx="{r*0.42}" ry="{ry*0.42}" fill="none" stroke="{GRAY}" stroke-width="7"/>'
    if face == "whine":
        out += f'<path d="M{cx-r*0.22} {cy-r*0.08} l{r*0.12} {r*0.06} M{cx+r*0.22} {cy-r*0.08} l{-r*0.12} {r*0.06}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
        out += f'<path d="M{cx-r*0.14} {cy+r*0.2} q{r*0.14} {-r*0.12} {r*0.28} 0" stroke="{INK}" stroke-width="7" fill="none" stroke-linecap="round"/>'
    elif face == "sulk":
        out += f'<path d="M{cx-r*0.22} {cy-r*0.04} h{r*0.14} M{cx+r*0.08} {cy-r*0.04} h{r*0.14} M{cx-r*0.12} {cy+r*0.18} h{r*0.24}" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
    elif face == "happy":
        out += f'<path d="M{cx-r*0.24} {cy-r*0.04} q{r*0.07} {-r*0.1} {r*0.14} 0 M{cx+r*0.1} {cy-r*0.04} q{r*0.07} {-r*0.1} {r*0.14} 0 M{cx-r*0.14} {cy+r*0.12} q{r*0.14} {r*0.14} {r*0.28} 0" stroke="{INK}" stroke-width="7" fill="none" stroke-linecap="round"/>'
    if cap:
        out += f'<rect x="{cx-12}" y="{cy-ry-r*0.32}" width="24" height="{r*0.22}" rx="6" fill="{GREEN if cap=="green" else INK}"/>'
    return out + "</g>"

def tpms(cx, cy, s=1.0, col=ACC, op=1.0):
    return (f'<g transform="translate({cx} {cy}) scale({s})" opacity="{op}" filter="url(#glow)" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M-52 -58 Q-80 -5 -58 48 L58 48 Q80 -5 52 -58"/><path d="M-46 66 v14 M-23 66 v14 M0 66 v14 M23 66 v14 M46 66 v14"/>'
            f'<line x1="0" y1="-30" x2="0" y2="8"/><circle cx="0" cy="28" r="3" fill="{col}"/></g>')

def car(x, y, s=1.0, frost=False, dash=False):
    """Side view car, (x, y) = ground under rear bumper."""
    k = lambda v: v * s
    out = (f'<path d="M{x} {y-k(60)} L{x} {y-k(150)} Q{x+k(10)} {y-k(170)} {x+k(120)} {y-k(175)} L{x+k(230)} {y-k(270)} L{x+k(520)} {y-k(270)} '
           f'L{x+k(640)} {y-k(175)} Q{x+k(780)} {y-k(170)} {x+k(790)} {y-k(130)} L{x+k(790)} {y-k(60)}Z" fill="{BG}" stroke="{INK}" stroke-width="{k(8)}" stroke-linejoin="round"/>'
           f'<path d="M{x+k(250)} {y-k(250)} L{x+k(370)} {y-k(250)} L{x+k(370)} {y-k(180)} L{x+k(150)} {y-k(180)}Z M{x+k(395)} {y-k(250)} L{x+k(505)} {y-k(250)} L{x+k(600)} {y-k(180)} L{x+k(395)} {y-k(180)}Z" fill="{"#2a2a30" if frost else "#141417"}" stroke="{GRAY}" stroke-width="{k(5)}"/>')
    if frost:
        out += f'<path d="M{x+k(260)} {y-k(240)} l{k(30)} {k(20)} M{x+k(420)} {y-k(235)} l{k(40)} {k(15)} M{x+k(480)} {y-k(200)} l{k(25)} {k(-15)}" stroke="{INK}" stroke-width="{k(3)}" opacity=".6"/>'
    if dash:
        out += glow(x + k(560), y - k(200), k(60), ACC, 0.6)
    out += tire(x + k(160), y - k(55), k(70)) + tire(x + k(630), y - k(55), k(70))
    return out

def wheel(cx, cy, r=240, tilt=0, hands=False):
    out = f'<g transform="rotate({tilt} {cx} {cy})"><circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="30"/>'
    out += f'<circle cx="{cx}" cy="{cy}" r="{r*0.28}" fill="{BG}" stroke="{INK}" stroke-width="14"/>'
    out += f'<path d="M{cx-r} {cy} L{cx-r*0.28} {cy} M{cx+r*0.28} {cy} L{cx+r} {cy} M{cx} {cy+r*0.28} L{cx} {cy+r}" stroke="{INK}" stroke-width="22"/>'
    if hands:
        out += f'<circle cx="{cx-r}" cy="{cy-20}" r="42" fill="{INK}" stroke="{BG}" stroke-width="6"/><circle cx="{cx+r}" cy="{cy-20}" r="42" fill="{INK}" stroke="{BG}" stroke-width="6"/>'
    return out + "</g>"

def airmachine(x, y, price="$2.00", timer="4:00", lit=True, crack=True, drop=False, off=False):
    out = ""
    if lit and not off:
        out += glow(x + 85, y - 470, 170, ACC, 0.25)
    out += f'<rect x="{x-140}" y="{y-520}" width="30" height="520" fill="{INK}"/><rect x="{x-190}" y="{y-530}" width="130" height="16" fill="{INK}"/>'
    if not off:
        out += f'<rect x="{x-180}" y="{y-514}" width="110" height="8" fill="{ACC}" filter="url(#glow)"/>'
    out += f'<rect x="{x}" y="{y-360}" width="190" height="360" rx="12" fill="{BG}" stroke="{INK}" stroke-width="7"/>'
    out += text(x + 95, y - 300, "AIR", 46, INK, 900)
    out += f'<rect x="{x+28}" y="{y-270}" width="134" height="56" rx="6" fill="#1c1c1f" stroke="{GRAY}" stroke-width="3"/>'
    out += text(x + 95, y - 230, timer if timer else price, 32, ACC if not off else GRAY, 500, font="mono")
    out += text(x + 95, y - 170, price if timer else "", 26, GRAY, 500, font="mono")
    out += f'<path d="M{x+190} {y-140} C{x+330} {y-140} {x+300} {y+10} {x+440} {y-30} S{x+540} {y-120} {x+600} {y-90}" fill="none" stroke="{INK}" stroke-width="13" stroke-linecap="round"/>'
    if crack:
        out += f'<path d="M{x+300} {y-80} l22 -8 M{x+312} {y-62} l24 -2" stroke="{GRAY}" stroke-width="4"/>'
        out += f'<path d="M{x+340} {y-100} q16 -18 0 -34 M{x+362} {y-104} q22 -24 0 -48" stroke="{GRAY}" stroke-width="4" fill="none"/>'
    if drop:
        out += f'<path d="M{x+604} {y-70} q-18 28 0 42 q18 -14 0 -42Z" fill="{ACC}" filter="url(#glow)"/>'
    return out

def calendar(cx, cy, top, big, s=1.0):
    return (f'<rect x="{cx-170*s}" y="{cy-180*s}" width="{340*s}" height="{360*s}" rx="{20*s}" fill="{BG}" stroke="{INK}" stroke-width="{8*s}"/>'
            f'<rect x="{cx-170*s}" y="{cy-180*s}" width="{340*s}" height="{90*s}" rx="{20*s}" fill="{INK}"/>'
            + text(cx, cy - 118*s, top, 40*s, BG, 900) + text(cx, cy + 90*s, big, 140*s, INK, 900))

def mappin(cx, cy, s=1.0):
    return (f'<g filter="url(#glow)"><path d="M{cx} {cy} C{cx-60*s} {cy-80*s} {cx-70*s} {cy-120*s} {cx-70*s} {cy-150*s} A{70*s} {70*s} 0 1 1 {cx+70*s} {cy-150*s} '
            f'C{cx+70*s} {cy-120*s} {cx+60*s} {cy-80*s} {cx} {cy}Z" fill="{ACC}"/></g><circle cx="{cx}" cy="{cy-150*s}" r="{26*s}" fill="{BG}"/>')

def grid():
    lines = "".join(f'<line x1="{x}" y1="60" x2="{x}" y2="860" />' for x in range(160, 1920, 200))
    lines += "".join(f'<line x1="0" y1="{y}" x2="1920" y2="{y}" />' for y in range(140, 860, 180))
    return f'<g stroke="#1d1d21" stroke-width="3">{lines}</g>'

def lens(cx=960, cy=450, r=400, inner="", ts="03:12:04 AM", rec=True):
    clip = f"lens{cx}{cy}"
    out = f'<defs><clipPath id="{clip}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>'
    out += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#lensbg)" stroke="{GRAY}" stroke-width="7"/>'
    out += f'<g clip-path="url(#{clip})">{inner}</g>'
    if rec: out += f'<circle cx="{cx+r*0.55}" cy="{cy-r*0.68}" r="12" fill="{REC}"/>' + text(cx + r*0.55 + 22, cy - r*0.68 + 10, "REC", 28, INK, 500, "start", "mono")
    if ts: out += text(cx, cy + r*0.86, ts, 30, GRAY, 500, font="mono")
    return out

ICONS = {}
def icon(name):
    def reg(fn):
        ICONS[name] = fn
        return fn
    return reg

@icon("playx")
def _(cx, cy): return f'<circle cx="{cx}" cy="{cy}" r="150" fill="none" stroke="{INK}" stroke-width="14"/><path d="M{cx-45} {cy-75} L{cx+80} {cy} L{cx-45} {cy+75}Z" fill="{INK}"/>' + cross(cx + 120, cy - 120, 0.55)
@icon("porchlight")
def _(cx, cy): return glow(cx, cy, 120, ACC, 0.15) + f'<rect x="{cx-50}" y="{cy-140}" width="100" height="40" fill="{INK}"/><path d="M{cx-70} {cy-100} L{cx+70} {cy-100} L{cx+50} {cy+80} L{cx-50} {cy+80}Z" fill="#2a2a30" stroke="{INK}" stroke-width="10"/>' + cross(cx + 120, cy - 120, 0.55)
@icon("wave")
def _(cx, cy): return f'<g fill="{INK}" filter="url(#glow)"><rect x="{cx-55}" y="{cy-20}" width="110" height="160" rx="30"/>' + "".join(f'<rect x="{cx-55+i*29}" y="{cy-120+abs(i-1.5)*14}" width="24" height="120" rx="12"/>' for i in range(4)) + f'<rect x="{cx+45}" y="{cy}" width="70" height="26" rx="13" transform="rotate(-40 {cx+45} {cy})"/></g>' + cross(cx + 130, cy - 130, 0.55)
@icon("boot")
def _(cx, cy): return f'<path d="M{cx-80} {cy-150} L{cx+10} {cy-150} L{cx+10} {cy+20} L{cx+130} {cy+50} L{cx+130} {cy+110} L{cx-80} {cy+110}Z" fill="{INK}"/>' + tire(cx + 260, cy + 30, 110) + text(cx + 180, cy - 110, "!", 90, ACC, 900)
@icon("hose")
def _(cx, cy): return f'<path d="M{cx-260} {cy-60} C{cx-100} {cy-60} {cx-120} {cy+90} {cx+40} {cy+60} S{cx+200} {cy-60} {cx+260} {cy-20}" fill="none" stroke="{INK}" stroke-width="22" stroke-linecap="round"/><path d="M{cx-60} {cy+30} l30 -10 M{cx-44} {cy+54} l32 -4" stroke="{ACC}" stroke-width="6"/><path d="M{cx} {cy-10} q22 -24 0 -48 M{cx+28} {cy-16} q30 -34 0 -68" stroke="{GRAY}" stroke-width="6" fill="none"/>'
@icon("steer")
def _(cx, cy): return wheel(cx, cy, 170, 18)
@icon("kettle")
def _(cx, cy): return glow(cx, cy, 160, ACC, 0.4) + f'<path d="M{cx-110} {cy+110} L{cx-90} {cy-40} Q{cx} {cy-110} {cx+90} {cy-40} L{cx+110} {cy+110}Z" fill="{BG}" stroke="{INK}" stroke-width="12"/><path d="M{cx+100} {cy-10} L{cx+180} {cy-70}" stroke="{INK}" stroke-width="14" stroke-linecap="round"/><path d="M{cx+190} {cy-110} q20 -30 0 -60 M{cx+225} {cy-120} q20 -30 0 -60" stroke="{ACC}" stroke-width="8" fill="none"/>'
@icon("carseat")
def _(cx, cy): return f'<path d="M{cx-60} {cy+120} L{cx+160} {cy+120} L{cx+160} {cy+70} L{cx-30} {cy+70} L{cx-110} {cy-170} L{cx-170} {cy-160} L{cx-90} {cy+90}Z" fill="{BG}" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/><path d="M{cx+40} {cy-60} l-90 0 m0 0 l30 -24 m-30 24 l30 24" stroke="{ACC}" stroke-width="10" fill="none" stroke-linecap="round"/>'
@icon("steps")
def _(cx, cy): return f'<rect x="{cx-170}" y="{cy-170}" width="340" height="340" rx="80" fill="{BG}" stroke="{INK}" stroke-width="12"/>' + text(cx, cy + 25, "11,402", 74, INK, 900) + text(cx, cy + 90, "STEPS", 30, ACC, 800, ls=6)
@icon("speech")
def _(cx, cy): return f'<path d="M{cx-300} {cy-120} H{cx+300} V{cy+60} H{cx-120} L{cx-200} {cy+140} L{cx-190} {cy+60} H{cx-300}Z" fill="{INK}"/>' + text(cx, cy - 15, "You seemed different", 44, BG, 800) + text(cx, cy + 35, "on Tuesday.", 44, BG, 800)
@icon("bell")
def _(cx, cy): return glow(cx, cy - 40, 150, ACC, 0.2) + f'<path d="M{cx-150} {cy+60} Q{cx-150} {cy-110} {cx} {cy-110} Q{cx+150} {cy-110} {cx+150} {cy+60}Z" fill="{INK}"/><rect x="{cx-200}" y="{cy+60}" width="400" height="34" rx="8" fill="{INK}"/><rect x="{cx-14}" y="{cy-150}" width="28" height="40" rx="6" fill="{INK}"/><path d="M{cx-230} {cy-150} q-30 -20 -40 -60 M{cx+230} {cy-150} q30 -20 40 -60" stroke="{ACC}" stroke-width="8" fill="none" stroke-linecap="round"/>'
@icon("thermo")
def _(cx, cy): return f'<rect x="{cx-40}" y="{cy-230}" width="80" height="330" rx="40" fill="{BG}" stroke="{INK}" stroke-width="10"/><circle cx="{cx}" cy="{cy+140}" r="75" fill="{INK}"/><rect x="{cx-16}" y="{cy-40}" width="32" height="160" fill="{INK}"/>'
@icon("cupholder")
def _(cx, cy): return f'<path d="M{cx-90} {cy-120} L{cx-70} {cy+120} L{cx+70} {cy+120} L{cx+90} {cy-120}Z" fill="{BG}" stroke="{INK}" stroke-width="12"/><path d="M{cx-80} {cy-20} q40 -30 80 0 t80 0" stroke="{ACC}" stroke-width="10" fill="none"/>'
@icon("home")
def _(cx, cy): return house(cx - 150, cy + 150, 1.4, lit=False) + f'<path d="M{cx-500} {cy+180} C{cx-300} {cy+180} {cx-260} {cy+240} {cx-160} {cy+200}" stroke="{ACC}" stroke-width="8" stroke-dasharray="2 18" stroke-linecap="round" fill="none"/>'

# ---------------------------------------------------------------- scenes

@scene("rule")
def rule(p):
    n, t = p.get("n", "1"), p.get("text", "")
    out = text(1060, 470, "RULE", 190, INK, 900, "end")
    out += f'<rect x="1100" y="300" width="200" height="200" rx="16" fill="{INK}"/>' + text(1200, 470, n, 170, BG, 900)
    if t:
        out += text(960, 600, t.upper(), 64, INK, 800, ls=3) + f'<rect x="{960-min(len(t)*22,620)}" y="630" width="{min(len(t)*44,1240)}" height="6" fill="{ACC}"/>'
    if on(p, "glitch"):
        out = f'<g transform="translate(-10 0)" opacity=".55"><g style="mix-blend-mode:screen">{out.replace(INK, "#ff4040")}</g></g><g transform="translate(10 0)" opacity=".55">{out.replace(INK, "#40c0ff")}</g>' + out
    return out

@scene("title")
def title(p):
    """Big command card (used for cold-open title beats)."""
    l1, l2 = p.get("l1", ""), p.get("l2", "")
    return text(960, 430, l1.upper(), 130, INK, 900) + text(960, 600, l2.upper(), 150, ACC, 900)

@scene("icons")
def icons(p):
    names = p.get("items", "playx").split(",")
    n = len(names)
    xs = [960] if n == 1 else [960 + (i - (n - 1) / 2) * 560 for i in range(n)]
    sc = 1.7 if n == 1 else 1.25
    out = "".join(f'<g transform="translate({x} 440) scale({sc}) translate({-x} -440)">' + ICONS[nm.strip()](x, 440) + "</g>" for nm, x in zip(names, xs))
    if p.get("label"): out += text(960, 790, p["label"].upper(), 54, GRAY, 800, ls=4)
    return out

@scene("houses")
def houses(p):
    n, lit = int(p.get("n", 7)), int(p.get("lit", 7))
    s = 0.85
    w = 220 * s + 30
    x0 = 960 - n * w / 2 + 15
    return floor(700) + "".join(house(x0 + i * w, 700, s, lit=(i + 1 == lit)) for i in range(n))

@scene("doorcam")
def doorcam(p):
    figp = p.get("fig", "none")
    inner = f'<path d="M500 760 Q960 640 1420 760 L1420 900 L500 900Z" fill="#1d1d20"/><path d="M880 900 L910 640 L1010 640 L1040 900Z" fill="#2b2b2f"/>'
    if on(p, "door"):
        inner += door(640, 300, 170, 360, open_=0.6) + glow(725, 500, 120, ACC, 0.25)
    if on(p, "porchlight"):
        inner += glow(900, 260, 140, ACC, 0.2)
    if on(p, "moth"):
        inner += f'<g fill="{INK}" transform="translate(1120 330)"><ellipse rx="10" ry="18"/><ellipse cx="-20" cy="-6" rx="22" ry="12" transform="rotate(-30)"/><ellipse cx="20" cy="-6" rx="22" ry="12" transform="rotate(30)"/></g>'
    if on(p, "headlights"):
        inner += f'<path d="M560 520 L1360 380 L1360 640Z" fill="{ACC}" opacity=".12"/>'
    if on(p, "shimmer"):
        inner += f'<path d="M700 700 q30 -14 60 0 t60 0 t60 0 t60 0 M760 730 q30 -14 60 0 t60 0 t60 0" stroke="{GRAY}" stroke-width="4" fill="none" opacity=".6"/>'
    if on(p, "footprints"):
        inner += "".join(f'<ellipse cx="{940 + (24 if i%2 else -24)}" cy="{690 + i*45}" rx="14" ry="24" fill="{INK}" opacity="{0.9-i*0.12}"/>' for i in range(5))
    poses = {"stepout": (820, 720, 1.05, "walk", None), "walkaway": (960, 690, 0.8, "walk", None), "turn": (960, 690, 0.85, "stand", "wide"),
             "wave": (960, 700, 0.95, "wave", "wide"), "stand": (960, 710, 0.95, "stand", "eyes"), "walkin": (960, 760, 1.2, "walk", "eyes"),
             "stiff": (960, 700, 0.95, "stand", None)}
    if figp in poses:
        x, y, s, pose, face = poses[figp]
        inner += fig(x, y, s, pose, face)
    if figp == "porchwave":
        inner += window(1150, 260, 170, 160, moon=False, hand=True) + fig(860, 730, 0.95, "wave", "wide")
    out = lens(960, 450, int(p.get("r", 400)), inner, p.get("ts", "03:12:04 AM"))
    if p.get("notif"):
        t, s_ = p["notif"].split("|") if "|" in p["notif"] else (p["notif"], "Front Door")
        out += notif(1220, 120, t, s_, 560, 1.0)
    return out

@scene("bedroom")
def bedroom(p):
    out = floor()
    out += window(1500, 200, 230, 280, moon=True)
    person = p.get("person", "sleep")
    out += bed(260, FLOOR, person, hand_x=on(p, "x"))
    dev = p.get("device", "phone")
    out += nightstand(1000, FLOOR, dev, p.get("clock", ""), glow_on=on(p, "glow"))
    if p.get("notif"):
        t, s_ = p["notif"].split("|")
        out += notif(880, 330, t, s_, 560, 0.95)
    if on(p, "kettle"):
        out += glow(1650, 640, 160, ACC, 0.45) + f'<rect x="1560" y="{FLOOR-10}" width="180" height="10" fill="{INK}"/>' + text(1650, 600, "DOWNSTAIRS", 28, GRAY, 500, font="mono", ls=4)
    return out

@scene("phone")
def phone_scene(p):
    mode = p.get("screen", "notif")
    x, y = 750, 70
    inner = ""
    if mode == "clip":
        inner += lens(960, 400, 180, door(880, 300, 90, 190, open_=0.6) + fig(980, 520, 0.6, "walk"), "03:12 AM", rec=True)
        inner += f'<rect x="790" y="660" width="340" height="10" rx="5" fill="{DIM}"/><rect x="790" y="660" width="120" height="10" rx="5" fill="{ACC}"/>'
    elif mode == "replay":
        inner += lens(960, 400, 180, fig(960, 500, 0.6, "walk"), "03:12 AM", rec=False)
        inner += f'<circle cx="960" cy="700" r="50" fill="none" stroke="{INK}" stroke-width="8"/><path d="M945 675 L985 700 L945 725Z" fill="{INK}"/>' + cross(960, 700, 0.6)
        inner += f'<ellipse cx="1050" cy="770" rx="50" ry="80" fill="{INK}" transform="rotate(-25 1050 770)"/>'
    elif mode == "delete":
        inner += f'<rect x="780" y="330" width="360" height="300" rx="24" fill="#1c1c1f" stroke="{GRAY}" stroke-width="3"/>' + text(960, 405, "Delete this event?", 30, INK, 800) + text(960, 450, "Are you sure?", 26, GRAY, 700)
        inner += f'<rect x="800" y="530" width="150" height="70" rx="35" fill="{DIM}"/><rect x="970" y="530" width="150" height="70" rx="35" fill="none" stroke="{INK}" stroke-width="4"/>' + text(875, 575, "YES", 26, "#55555a", 800) + text(1045, 575, "CANCEL", 22, INK, 800)
    elif mode == "storage":
        inner += text(790, 170, "Cloud storage", 30, INK, 800, "start") + f'<rect x="790" y="200" width="340" height="24" rx="12" fill="{DIM}"/><rect x="790" y="200" width="333" height="24" rx="12" fill="{ACC}"/>' + text(1130, 260, "98%", 26, ACC, 500, "end", "mono")
        for r in range(4):
            for c in range(3):
                inner += f'<rect x="{790+c*116}" y="{300+r*110}" width="104" height="80" rx="8" fill="#1c1c1f"/>' + text(842 + c*116, 370 + r*110, "3:12", 18, GRAY, 500, font="mono")
                inner += fig(842 + c*116, 360 + r*110, 0.18, "walk")
    elif mode == "toggle":
        inner += text(790, 190, "Settings", 34, INK, 900, "start") + f'<rect x="780" y="240" width="360" height="100" rx="18" fill="#1c1c1f"/>' + text(800, 300, "Motion alerts", 28, INK, 800, "start")
        inner += f'<rect x="1040" y="265" width="84" height="48" rx="24" fill="{ACC}"/><circle cx="1100" cy="289" r="20" fill="{INK}"/><ellipse cx="1150" cy="420" rx="45" ry="90" fill="{INK}" transform="rotate(-25 1150 420)"/>'
    elif mode == "battery":
        pct = p.get("pct", "41")
        inner += f'<rect x="830" y="300" width="260" height="130" rx="20" fill="none" stroke="{INK}" stroke-width="10"/><rect x="1090" y="340" width="20" height="50" rx="6" fill="{INK}"/>'
        inner += f'<rect x="848" y="318" width="{int(224*int(pct)/100)}" height="94" rx="10" fill="{ACC}"/>' + text(960, 520, f"{pct}%", 80, INK, 900) + text(960, 580, "CHARGING", 26, GRAY, 500, font="mono", ls=4)
        inner += f'<path d="M960 830 L960 880" stroke="{INK}" stroke-width="12"/>'
        out = phone(x, y, 420, 760, inner) + f'<path d="M1180 400 C1400 380 1500 250 1700 220" stroke="{ACC}" stroke-width="6" stroke-dasharray="2 16" stroke-linecap="round" fill="none"/>' + window(1660, 140, 160, 200, moon=True)
        return out
    elif mode in ("shared", "shared2", "remove"):
        inner += text(790, 160, "SETTINGS ›", 22, GRAY, 800, "start") + text(790, 210, "Shared Users", 40, INK, 900, "start")
        rows = [("You", "Owner", False)] + ([("You", "Added 3 years ago", True)] if mode != "shared" else [])
        for i, (n_, s_, hl) in enumerate(rows):
            yy = 250 + i * 130
            inner += f'<rect x="780" y="{yy}" width="360" height="110" rx="18" fill="#1c1c1f" stroke="{ACC if hl else "#1c1c1f"}" stroke-width="4"/><circle cx="840" cy="{yy+55}" r="34" fill="{INK}"/>'
            inner += text(895, yy + 48, n_, 30, INK, 800, "start") + text(895, yy + 82, s_, 20, ACC if hl else GRAY, 700, "start")
        if mode == "shared":
            inner += f'<rect x="780" y="380" width="360" height="110" rx="18" fill="none" stroke="{DIM}" stroke-width="3" stroke-dasharray="10 10"/>' + text(960, 445, "?", 50, DIM, 900)
        if mode == "remove":
            inner += f'<rect x="790" y="680" width="340" height="80" rx="40" fill="none" stroke="{GRAY}" stroke-width="4"/>' + text(960, 732, "Remove user", 28, GRAY, 800) + cross(960, 720, 0.7)
    elif mode == "clips":
        inner += text(790, 170, "Events", 34, INK, 900, "start")
        for i in range(6):
            yy = 210 + i * 95
            old = i == 5
            inner += f'<rect x="780" y="{yy}" width="360" height="80" rx="12" fill="#1c1c1f" stroke="{ACC if old else "#1c1c1f"}" stroke-width="4"/>' + fig(830, yy + 70, 0.22, "walk")
            inner += text(880, yy + 35, "Motion · Front Door", 20, INK, 800, "start") + text(880, yy + 62, "3 years ago · 3:12 AM" if old else f"{i+1} days ago · 3:12 AM", 18, ACC if old else GRAY, 500, "start", "mono")
    elif mode == "feed":
        inner += lens(960, 420, 190, bed(800, 560, "sleep").replace('transform', 'data-t') if False else window(860, 320, 200, 200, moon=False) + f'<rect x="880" y="430" width="160" height="40" rx="14" fill="#8a8a90"/><circle cx="895" cy="430" r="22" fill="{INK}"/>', "LIVE", rec=True)
        inner += text(960, 690, "Viewing as: You (2)", 24, ACC, 700)
    elif mode == "notif":
        t, s_ = p.get("notif", "Motion detected|Front Door · 3:12 AM").split("|")
        inner += text(960, 260, p.get("time", "3:12"), 110, INK, 800) + notif(775, 360, t, s_, 560, 0.66)
    return phone(x, y, 420, 760, inner)

@scene("split")
def split(p):
    mode = p.get("mode", "walk")
    out = f'<line x1="960" y1="110" x2="960" y2="820" stroke="{DIM}" stroke-width="4"/>'
    lab = lambda x, t, c=GRAY: text(x, 840, t, 34, c, 800, ls=4)
    if mode == "walk":
        out += lens(500, 450, 300, fig(500, 640, 1.0, "stand"), "CLIP #1") + lens(1420, 450, 300, fig(1420, 640, 1.0, "walk", "eyes"), "CLIP #5")
    elif mode == "figs":
        out = fig(760, 720, 1.6, "stand") + fig(1160, 720, 1.6, "stand", op=float(p.get("fade", 0.25)))
        return out
    elif mode == "days":
        for cx, t in ((480, "MONDAY"), (1440, "MONDAY")):
            out += f'<rect x="{cx-260}" y="{FLOOR-200}" width="520" height="30" fill="{INK}"/><path d="M{cx-60} {FLOOR-280} h80 v80 h-80Z M{cx+20} {FLOOR-260} q30 0 30 20 t-30 20" stroke="{INK}" stroke-width="8" fill="none"/>'
            out += f'<rect x="{cx-90}" y="250" width="180" height="90" rx="10" fill="none" stroke="{INK}" stroke-width="6"/>' + text(cx, 312, "7:40", 50, INK, 700, font="mono") + lab(cx, t)
    elif mode == "life":
        out += bed(140, 700, "sleep") + ICONS["home"](520, 300).replace("1.4", "1") + lab(480, "YOU", INK)
        out += fig(1240, 700, 0.9, "walk") + f'<rect x="1420" y="520" width="300" height="180" rx="12" fill="none" stroke="{INK}" stroke-width="6"/>' + text(1570, 630, "9:00", 60, INK, 700, font="mono") + lab(1440, "IT", ACC)
    return out

@scene("pin")
def pin(p):
    out = grid() + mappin(560, 520, 1.6) + text(560, 640, p.get("city", "").upper(), 64, INK, 900, ls=6)
    ex = p.get("extra", "")
    if ex == "couch":
        out += f'<rect x="1100" y="560" width="520" height="140" rx="40" fill="#5a5a60" stroke="{INK}" stroke-width="6"/>' + fig(1300, 640, 1.0, "sit", "eyes") + glow(1370, 470, 60, ACC, 0.6)
    elif ex == "doorway":
        out += door(1150, 300, 200, 420, open_=0.7) + fig(1250, 720, 1.0, "stand", "eyes") + f'<g transform="translate(1560 700)"><rect x="-70" y="-60" width="130" height="50" rx="20" fill="{GRAY}"/><circle cx="-80" cy="-70" r="30" fill="{GRAY}"/><rect x="-60" y="-12" width="14" height="12" fill="{GRAY}"/><rect x="40" y="-12" width="14" height="12" fill="{GRAY}"/></g>' + text(1600, 600, "←", 50, ACC, 900)
    elif ex == "parka":
        out += tire(1500, 620, 120) + fig(1250, 720, 1.0, "kneel", "eyes") + f'<rect x="1360" y="580" width="50" height="16" rx="6" fill="{ACC}"/>'
    elif ex == "boxes":
        out += "".join(f'<rect x="{1150+i*150}" y="{600-(i%2)*120}" width="130" height="120" fill="none" stroke="{INK}" stroke-width="6"/>' for i in range(3)) + f'<path d="M1100 780 C1300 780 1450 700 1620 760" stroke="{ACC}" stroke-width="6" stroke-dasharray="2 16" stroke-linecap="round" fill="none"/>'
    elif ex == "calendar":
        out += calendar(1400, 440, "MONTH", p.get("big", "18"), 1.0) + tpms(1700, 300, 0.7, DIM)
    return out

@scene("peephole")
def peephole(p):
    inner = f'<path d="M460 760 Q960 640 1460 760 L1460 900 L460 900Z" fill="#1d1d20"/><rect x="760" y="640" width="400" height="60" rx="6" fill="#2a2a30" transform="rotate(6 960 670)"/>'
    inner += "".join(f'<ellipse cx="{940 + (26 if i%2 else -26)}" cy="{640 - i*50}" rx="14" ry="24" fill="{INK}" opacity="{0.8-i*0.12}"/>' for i in range(5)) if on(p, "prints") else ""
    inner += f'<rect x="1150" y="220" width="70" height="40" fill="{DIM}"/>'
    return f'<rect x="0" y="0" width="1920" height="900" fill="#050505"/>' + lens(960, 450, 360, inner, "", rec=False)

@scene("footprints")
def footprints(p):
    out = door(870, 180, 180, 360) + floor(560)
    out += "".join(f'<ellipse cx="{960 + (40 if i%2 else -40)}" cy="{620 + i*55}" rx="{18+i*2}" ry="{30+i*3}" fill="{INK}" opacity="{0.9-i*0.13}"/>' for i in range(5))
    out += text(1350, 780, "OUT", 44, INK, 800, ls=6) + text(1350, 840, "IN: 0", 44, ACC, 800, ls=6)
    return out

@scene("doorknob")
def doorknob(p):
    return (f'<rect x="560" y="80" width="800" height="760" fill="{BG}" stroke="{INK}" stroke-width="8"/>' + glow(1180, 470, 160, ACC, 0.45)
            + f'<rect x="1060" y="430" width="240" height="80" rx="40" fill="{ACC}" filter="url(#glow)"/><circle cx="1110" cy="470" r="50" fill="{ACC}"/>'
            + f'<g fill="{INK}"><rect x="1150" y="400" width="190" height="140" rx="60"/>' + "".join(f'<rect x="{1120}" y="{410+i*32}" width="80" height="26" rx="13"/>' for i in range(4)) + "</g>")

@scene("gray")
def gray_feed(p):
    return (f'<circle cx="960" cy="450" r="400" fill="#4a4a4f" stroke="{GRAY}" stroke-width="7"/>'
            + f'<path d="M560 450 h800" stroke="#5a5a60" stroke-width="3"/>' + text(960, 470, p.get("count", "0:60"), 120, INK, 500, font="mono")
            + text(960, 790, p.get("ts", "03:33:00 AM"), 30, GRAY, 500, font="mono"))

@scene("face")
def face(p):
    return (f'<circle cx="960" cy="450" r="400" fill="url(#lensbg)" stroke="{GRAY}" stroke-width="7"/>'
            + f'<circle cx="960" cy="460" r="260" fill="{INK}" filter="url(#glow)"/><circle cx="790" cy="440" r="22" fill="{BG}"/><circle cx="1130" cy="440" r="22" fill="{BG}"/>'
            + f'<path d="M820 330 h-80 M1100 330 h80" stroke="{ACC}" stroke-width="6" stroke-dasharray="6 10"/>')

@scene("keypad")
def keypad(p):
    lit = p.get("lit", "")
    out = f'<rect x="740" y="80" width="440" height="760" rx="30" fill="{BG}" stroke="{INK}" stroke-width="8"/>'
    keys = "123456789*0#"
    for i, k in enumerate(keys):
        cx, cy = 840 + (i % 3) * 120, 220 + (i // 3) * 160
        hit = k in lit
        if hit: out += glow(cx, cy, 70, ACC, 0.6)
        out += f'<circle cx="{cx}" cy="{cy}" r="52" fill="{ACC if hit else BG}" stroke="{ACC if hit else INK}" stroke-width="6"/>' + text(cx, cy + 18, k, 52, BG if hit else INK, 800)
    return out

@scene("kitchen")
def kitchen(p):
    out = floor() + f'<rect x="300" y="{FLOOR-260}" width="900" height="260" fill="{BG}" stroke="{INK}" stroke-width="7"/><line x1="300" y1="{FLOOR-230}" x2="1200" y2="{FLOOR-230}" stroke="{INK}" stroke-width="5"/>'
    out += "".join(f'<rect x="{330+i*220}" y="140" width="200" height="180" fill="none" stroke="{GRAY}" stroke-width="5"/>' for i in range(4))
    if on(p, "kettle"): out += ICONS["kettle"](800, FLOOR - 380).replace("translate", "translate")
    if on(p, "coffee"): out += fig(560, FLOOR, 1.0, "stand", "eyes") + f'<rect x="595" y="{FLOOR-130}" width="36" height="44" rx="6" fill="{INK}"/>'
    if on(p, "dashglow"): out += window(1400, 200, 300, 280, moon=False) + glow(1550, 420, 60, ACC, 0.8) + f'<rect x="1430" y="400" width="240" height="60" rx="20" fill="none" stroke="{GRAY}" stroke-width="4"/>'
    return out

@scene("mascot")
def mascot(p):
    out = (f'<circle cx="960" cy="300" r="105" fill="{INK}"/><rect x="895" y="292" width="130" height="14" rx="7" fill="{BG}"/>'
           f'<path d="M800 560 Q800 420 960 420 Q1120 420 1120 560 L1120 640 L800 640Z" fill="{INK}"/>'
           f'<path d="M920 420 L960 520 L1000 420" stroke="{BG}" stroke-width="6" fill="none"/>'
           f'<rect x="932" y="520" width="56" height="70" rx="6" fill="{ACC}"/><rect x="942" y="536" width="36" height="8" fill="{BG}"/><rect x="942" y="552" width="26" height="6" fill="{BG}"/>')
    if p.get("text"):
        out += text(960, 750, p["text"].upper(), 50, INK, 500, font="mono", ls=6) + f'<rect x="560" y="775" width="800" height="5" fill="{ACC}"/>'
    if p.get("sub"):
        out += text(960, 840, p["sub"].upper(), 34, ACC, 500, font="mono", ls=8)
    return out

@scene("endscreen")
def endscreen(p):
    out = "".join(f'<rect x="{x}" y="250" width="640" height="360" rx="16" fill="#141417" stroke="{DIM}" stroke-width="4" stroke-dasharray="14 10"/>' + text(x + 320, 445, "NEXT NOTICE", 34, DIM, 800, ls=4) for x in (180, 1100))
    return out + f'<circle cx="960" cy="760" r="80" fill="none" stroke="{ACC}" stroke-width="8"/>' + text(960, 772, "SUB", 34, ACC, 900)

# ---- tire episode

@scene("dash")
def dash(p):
    mode = p.get("light", "on")
    out = ""
    if on(p, "frost"):
        out += f'<path d="M0 0 L380 0 L180 200 L0 170Z M1920 0 L1540 0 L1740 210 L1920 170Z" fill="{INK}" opacity=".1"/><path d="M80 40 l60 30 M120 110 l40 -20 M1790 60 l-40 40 M1830 130 l-60 0" stroke="{INK}" stroke-width="4" opacity=".35"/>'
    out += f'<path d="M0 0 L1920 0 L1920 420 Q960 300 0 420Z" fill="#141417" opacity=".7"/>'
    out += f'<rect x="260" y="480" width="1400" height="320" rx="160" fill="#111114" stroke="{GRAY}" stroke-width="7"/>'
    out += f'<circle cx="580" cy="640" r="125" fill="none" stroke="{DIM}" stroke-width="8"/><circle cx="1340" cy="640" r="125" fill="none" stroke="{DIM}" stroke-width="8"/>'
    if mode == "on": out += glow(960, 640, 140, ACC, 0.35) + tpms(960, 630, 1.3)
    elif mode == "pulse": out += glow(960, 640, 220, ACC, 0.5) + tpms(960, 630, 1.6)
    elif mode == "flicker": out += tpms(960, 630, 1.3, ACC, 0.45)
    else: out += tpms(960, 630, 1.3, DIM)
    return out

@scene("route")
def route(p):
    bends = int(p.get("bends", 1))
    out = grid()
    hx, wx, y = 260, 1660, 600
    out += ICONS["home"](hx + 50, y - 150).split("<path d=\"M")[0] if False else house(hx - 110, y + 60, 1.0)
    out += f'<rect x="{wx-80}" y="{y-200}" width="160" height="260" fill="{BG}" stroke="{INK}" stroke-width="7"/>' + text(wx, y + 120, "WORK", 34, GRAY, 500, font="mono", ls=6) + text(hx, y + 120, "HOME", 34, GRAY, 500, font="mono", ls=6)
    stations = [(560, 260), (960, 200), (1340, 300)][:bends]
    d = f"M{hx+120} {y}"
    for sx, sy in stations:
        d += f" Q{sx-120} {y} {sx} {sy+60}"
        y2 = y
        d += f" Q{sx+120} {y2} {sx+200} {y2}"
    d += f" L{wx-90} {y}"
    out += f'<path d="{d}" fill="none" stroke="{ACC}" stroke-width="10" stroke-dasharray="2 18" stroke-linecap="round"/>'
    for sx, sy in stations:
        out += f'<rect x="{sx-50}" y="{sy-30}" width="100" height="70" rx="10" fill="{INK}"/>' + text(sx, sy + 18, "AIR", 30, BG, 900)
    return out

@scene("loop")
def loop(p):
    out = grid()
    out += f'<path d="M960 170 C1300 150 1520 280 1530 450 C1540 650 1340 790 1040 790 C740 795 420 740 380 520 C350 330 610 185 960 170Z" fill="none" stroke="{ACC}" stroke-width="10" stroke-dasharray="2 20" stroke-linecap="round"/>'
    for x, y in ((960, 170), (1530, 450), (1040, 790), (380, 520), (1310, 230), (560, 260), (1400, 700)):
        out += f'<rect x="{x-45}" y="{y-32}" width="90" height="64" rx="10" fill="{INK}"/>' + text(x, y + 12, "AIR", 26, BG, 900)
    out += house(880, 560, 0.8) + text(960, 610, "HOME", 30, GRAY, 500, font="mono", ls=6)
    return out

@scene("thermo")
def thermo(p):
    out = ICONS["thermo"](640, 470) + text(820, 300, p.get("from", "50°"), 70, GRAY, 800, "start") + text(820, 600, p.get("to", "20°"), 90, INK, 900, "start")
    out += f'<path d="M800 340 L800 530" stroke="{ACC}" stroke-width="8"/><path d="M785 520 L800 545 L815 520" fill="none" stroke="{ACC}" stroke-width="8"/>'
    out += tire(1380, 460, 180, squash=on(p, "squash")) + text(1380, 760, "-1 PSI / 10°F", 44, ACC, 800, font="mono")
    return out

@scene("car")
def car_scene(p):
    out = floor(780)
    if on(p, "sunrise"):
        out += f'<path d="M1490 780 A160 160 0 0 1 1810 780Z" fill="{ACC}" opacity=".18"/><path d="M1490 780 A160 160 0 0 1 1810 780" fill="none" stroke="{ACC}" stroke-width="6"/>'
    out += car(560 if not p.get("figure") else 600, 780, 1.0, frost=on(p, "frost"), dash=on(p, "dash"))
    f = p.get("figure", "")
    if f == "kick":
        out += fig(560, 780, 1.0, "kick", "eyes") + text(720, 610, "!", 90, ACC, 900) + text(1190, 610, "!", 90, ACC, 900)
    elif f == "kneel":
        out += fig(470, 780, 1.0, "kneel", "eyes") + f'<rect x="560" y="700" width="60" height="18" rx="6" fill="{ACC}"/>'
    if on(p, "happy"):
        out += glow(720, 725, 90, ACC, 0.4) + glow(1190, 725, 90, ACC, 0.4)
    return out

@scene("tires")
def tires(p):
    face_ = p.get("face", "whine")
    cap = p.get("cap", None)
    return "".join(tire(360 + i * 400, 450, 150, face=face_, cap=cap, squash=on(p, "squash"), fill_glow=on(p, "glow")) for i in range(4))

@scene("tire")
def tire_scene(p):
    mode = p.get("mode", "glow")
    out = ""
    if mode == "glow":
        out += tire(960, 450, 260, "happy", fill_glow=True)
    elif mode == "breath":
        out += tire(960, 450, 260, "sulk")
        out += "".join(f'<circle cx="{960+math.cos(a)*(330+(i%3)*40)}" cy="{450+math.sin(a)*(330+(i%3)*40)}" r="{9-(i%3)*2}" fill="{INK}" opacity=".7"/>' for i, a in enumerate([k*0.52 for k in range(12)]))
    elif mode == "water":
        out += f'<clipPath id="tc"><ellipse cx="960" cy="450" rx="200" ry="200"/></clipPath>' + tire(960, 450, 260)
        out += f'<path d="M700 600 q65 -30 130 0 t130 0 t130 0 t130 0 V720 H700Z" fill="{ACC}" opacity=".8" clip-path="url(#tc)"/>'
    elif mode == "rust":
        out += tire(1100, 470, 260) + "".join(f'<circle cx="{1100+math.cos(a)*108}" cy="{470+math.sin(a)*108}" r="14" fill="#a0522d"/>' for a in (0.5, 1.4, 2.6, 4.0, 5.2)) + fig(600, 760, 1.2, "point", "eyes")
    elif mode == "chuck":
        out += airmachine(300, 760, timer="1:48") + tire(1380, 600, 160)
    return out

@scene("jamb")
def jamb(p):
    psi = p.get("psi", "35")
    out = f'<rect x="300" y="200" width="560" height="400" rx="20" fill="{INK}"/>' + text(580, 300, "TIRE AND LOADING", 30, BG, 800) + text(580, 470, f"{psi} PSI", 120, BG, 900) + text(580, 540, "FRONT / REAR · COLD", 26, "#55555a", 700)
    out += f'<circle cx="1380" cy="440" r="260" fill="{BG}" stroke="{INK}" stroke-width="12"/>'
    for i in range(9):
        a = math.radians(150 + i * 30)
        out += f'<line x1="{1380+math.cos(a)*200}" y1="{440+math.sin(a)*200}" x2="{1380+math.cos(a)*235}" y2="{440+math.sin(a)*235}" stroke="{GRAY}" stroke-width="8"/>'
    a = math.radians(150 + 7 * 30)
    out += f'<line x1="1380" y1="440" x2="{1380+math.cos(a)*190}" y2="{440+math.sin(a)*190}" stroke="{ACC}" stroke-width="14" stroke-linecap="round" filter="url(#glow)"/><circle cx="1380" cy="440" r="24" fill="{INK}"/>'
    return out + text(1380, 620, psi, 60, ACC, 900)

@scene("calendar")
def calendar_scene(p):
    out = calendar(760, 450, p.get("top", "DAYS"), p.get("big", "30"))
    if p.get("light"):
        out += glow(1300, 450, 120, ACC, 0.4) + tpms(1300, 440, 1.6)
    return out

@scene("states")
def states(p):
    out = ""
    for i, (st, ab) in enumerate((("CALIFORNIA", "CA"), ("CONNECTICUT", "CT"))):
        cx = 620 + i * 680
        out += glow(cx, 430, 200, ACC, 0.25) + f'<rect x="{cx-280}" y="220" width="560" height="420" rx="24" fill="{BG}" stroke="{ACC}" stroke-width="8"/>'
        out += text(cx, 470, ab, 220, ACC, 900) + text(cx, 580, st, 44, INK, 800, ls=6)
    return out + text(960, 790, "FREE AIR WITH FUEL · STATE LAW", 40, GRAY, 500, font="mono", ls=4)

@scene("airmachine")
def airmachine_scene(p):
    out = floor(780) + airmachine(700, 780, p.get("price", "$2.00"), p.get("timer", "4:00"), lit=True, crack=True, drop=on(p, "drop"), off=on(p, "off"))
    if p.get("tire", "1") != "0":
        out += tire(1460, 680, 110)
    return out

@scene("compressor")
def compressor(p):
    out = f'<rect x="560" y="260" width="800" height="420" rx="210" fill="{BG}" stroke="{INK}" stroke-width="10"/>'
    out += f'<path d="M600 560 Q960 590 1320 560 L1320 600 Q960 690 600 600Z" fill="{ACC}" opacity=".85"/>'
    out += "".join(f'<path d="M{700+i*90} {350+(i%3)*40} q-10 16 0 24 q10 -8 0 -24Z" fill="{ACC}"/>' for i in range(7))
    out += f'<path d="M960 680 L960 760" stroke="{INK}" stroke-width="12"/><path d="M960 790 q-16 26 0 38 q16 -12 0 -38Z" fill="{ACC}" filter="url(#glow)"/>'
    return out

@scene("highway")
def highway(p):
    out = f'<path d="M560 860 L900 300 L1020 300 L1360 860Z" fill="#141417"/>' + "".join(f'<rect x="954" y="{330+i*110}" width="12" height="{40+i*12}" fill="{INK}"/>' for i in range(5))
    if p.get("sign"):
        out += f'<rect x="1440" y="300" width="18" height="400" fill="{GRAY}"/><rect x="1360" y="220" width="180" height="110" rx="10" fill="{INK}"/>' + text(1450, 295, p["sign"], 50, BG, 900)
    if on(p, "slosh"):
        out += ICONS["cupholder"](420, 470)
    if on(p, "light"):
        out += tpms(1600, 760, 0.8)
    return out

@scene("sign")
def sign(p):
    out = f'<rect x="460" y="200" width="1000" height="300" rx="20" fill="{BG}" stroke="{INK}" stroke-width="10"/>' + text(960, 330, p.get("l1", "NITROGEN"), 110, INK, 900) + text(960, 430, p.get("l2", "FILLED"), 70, GREEN, 900, ls=12)
    out += "".join(f'<rect x="{700+i*170}" y="600" width="50" height="90" rx="14" fill="{GREEN}"/>' for i in range(4))
    return out

@scene("wheel")
def wheel_scene(p):
    out = ""
    if on(p, "station"):
        out += f'<rect x="1500" y="120" width="260" height="140" rx="14" fill="{INK}"/>' + text(1630, 215, "AIR", 80, BG, 900) + glow(1630, 190, 200, ACC, 0.3)
    out += wheel(960, 520, 300, float(p.get("tilt", 14)), hands=on(p, "hands"))
    if on(p, "light"):
        out += tpms(1560, 760, 0.8)
    return out

# ---------------------------------------------------------------- render helpers

def svg(scene_name, params):
    fn = SCENES.get(scene_name)
    body = fn(params) if fn else text(960, 470, f"[{scene_name}]", 60, GRAY)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="100%" height="100%">{DEFS}{body}</svg>'

# ---- plus-one episode (furnace in July)

@scene("furnace")
def furnace_scene(p):
    """Furnace cutaway: cabinet, burners, igniter. lit=1 flames, igniter=1 glowing igniter, fan=1 blower lines."""
    out = floor()
    out += f'<rect x="760" y="140" width="400" height="{FLOOR-140}" rx="10" fill="{BG}" stroke="{INK}" stroke-width="8"/>'
    out += f'<rect x="800" y="180" width="320" height="230" fill="#141417" stroke="{GRAY}" stroke-width="5"/>'
    out += f'<rect x="800" y="450" width="320" height="260" fill="#141417" stroke="{GRAY}" stroke-width="5"/>'
    out += f'<rect x="900" y="60" width="120" height="80" fill="{BG}" stroke="{INK}" stroke-width="7"/>'  # flue
    if on(p, "igniter"):
        out += glow(860, 330, 70, ACC, 0.7) + f'<rect x="840" y="300" width="40" height="70" rx="8" fill="{ACC}" filter="url(#glow)"/>'
    if on(p, "lit"):
        out += glow(960, 330, 150, ACC, 0.35) + "".join(f'<path d="M{880+i*60} 390 q-22 -50 0 -100 q22 50 0 100Z" fill="{ACC}" filter="url(#glow)"/>' for i in range(4))
    if on(p, "fan"):
        out += f'<circle cx="960" cy="580" r="90" fill="none" stroke="{INK}" stroke-width="6"/>' + "".join(f'<path d="M960 580 L{960+80*math.cos(a)} {580+80*math.sin(a)}" stroke="{INK}" stroke-width="10"/>' for a in (0, 2.1, 4.2))
    if p.get("label"):
        out += text(1500, 300, p["label"].upper(), 44, GRAY, 500, font="mono", ls=4)
    if p.get("clock"):
        out += text(1500, 420, p["clock"], 90, INK, 500, font="mono")
    if p.get("temp"):
        out += text(420, 300, p["temp"], 120, ACC, 900) + text(420, 370, "OUTSIDE", 34, GRAY, 800, ls=6)
    return out

@scene("thermostat")
def thermostat_scene(p):
    """Wall thermostat close-up. mode=OFF, temp, wire=1 pulled wires, x=1 yellow cross."""
    out = f'<rect x="640" y="130" width="640" height="560" rx="60" fill="{BG}" stroke="{INK}" stroke-width="10"/>'
    out += f'<rect x="720" y="220" width="480" height="260" rx="20" fill="#141417" stroke="{GRAY}" stroke-width="5"/>'
    out += text(960, 400, p.get("temp", "72°"), 150, INK, 500, font="mono")
    out += text(960, 600, "MODE: " + p.get("mode", "OFF"), 52, ACC if p.get("mode", "OFF") == "OFF" else INK, 800, ls=6)
    if on(p, "wire"):
        out += f'<path d="M700 700 C640 780 560 760 520 830 M760 700 C740 800 680 800 660 860" stroke="{INK}" stroke-width="10" fill="none"/><path d="M700 700 C640 780 560 760 520 830" stroke="{REC}" stroke-width="4" fill="none"/>'
    if on(p, "x"):
        out += cross(1400, 200, 0.7)
    if p.get("months"):
        out += text(960, 820, p["months"].upper(), 40, GRAY, 500, font="mono", ls=6)
    return out

@scene("closet")
def closet_scene(p):
    """Closet with the only warm vent, folded blanket."""
    out = floor() + f'<rect x="660" y="120" width="600" height="{FLOOR-120}" fill="#141417" stroke="{INK}" stroke-width="8"/>'
    out += f'<line x1="680" y1="260" x2="1240" y2="260" stroke="{GRAY}" stroke-width="6"/>'
    out += glow(960, FLOOR - 40, 160, ACC, 0.45) + f'<rect x="880" y="{FLOOR-30}" width="160" height="22" fill="{ACC}" filter="url(#glow)"/>'
    out += "".join(f'<line x1="{896+i*26}" y1="{FLOOR-28}" x2="{896+i*26}" y2="{FLOOR-10}" stroke="{BG}" stroke-width="6"/>' for i in range(6))
    if on(p, "blanket"):
        out += "".join(f'<rect x="{800}" y="{FLOOR-120-i*28}" width="320" height="26" rx="10" fill="{INK if i%2 else GRAY}"/>' for i in range(3))
    if on(p, "cold"):
        out += text(420, 400, "COLD", 60, GRAY, 800, ls=8) + text(1500, 400, "COLD", 60, GRAY, 800, ls=8)
    return out

@scene("fridge")
def fridge_scene(p):
    """Fridge side view with the gap behind it. open=1 door open with light on floor, gap=1 dimension line,
    breath=1 hum lines, milk=1 milk carton at the back."""
    out = floor() + f'<rect x="1500" y="120" width="40" height="{FLOOR-120}" fill="{DIM}"/>'  # wall
    out += f'<rect x="1000" y="140" width="400" height="{FLOOR-140}" rx="16" fill="{BG}" stroke="{INK}" stroke-width="8"/><line x1="1000" y1="380" x2="1400" y2="380" stroke="{INK}" stroke-width="6"/>'
    if on(p, "gap"):
        out += f'<rect x="1410" y="140" width="80" height="{FLOOR-140}" fill="#050505"/>' + f'<circle cx="1440" cy="250" r="6" fill="{INK}"/><circle cx="1462" cy="250" r="6" fill="{INK}"/>'
        out += f'<path d="M1410 100 H1490 M1410 80 v40 M1490 80 v40" stroke="{ACC}" stroke-width="6"/>' + text(1450, 70, '4"', 54, ACC, 900)
    if on(p, "breath"):
        out += "".join(f'<path d="M{1420+i*20} {520-i*40} q30 -20 0 -40" stroke="{GRAY}" stroke-width="5" fill="none"/>' for i in range(3)) + text(1200, 830, "IN · OUT · IN · OUT", 40, GRAY, 500, font="mono", ls=6)
    if on(p, "open"):
        out += f'<path d="M1000 140 L760 220 L760 {FLOOR-40} L1000 {FLOOR}Z" fill="{BG}" stroke="{INK}" stroke-width="7"/>'
        out += f'<path d="M1010 200 L1390 200 L1700 {FLOOR} L700 {FLOOR}Z" fill="{ACC}" opacity=".18"/>' + glow(1200, 300, 120, ACC, 0.5)
    if on(p, "milk"):
        out += f'<path d="M1300 310 h60 v-70 l-30 -30 l-30 30Z" fill="{INK}"/>' + text(1180, 330, "BACK", 30, ACC, 800, font="mono", ls=4)
    if on(p, "defrost"):
        out += "".join(f'<ellipse cx="{1080+i*90}" cy="{430+(i%2)*30}" rx="8" ry="14" fill="{INK}"/>' for i in range(4)) + text(560, 300, "DEFROST", 50, GRAY, 500, font="mono", ls=6) + text(560, 370, "8–12 HRS", 50, ACC, 500, font="mono", ls=6)
    return out

@scene("duct")
def duct_scene(p):
    """Duct run through a house cross-section; at= kitchen|hall|bed shows the lump, stop=1 lump glowing over the bed."""
    out = f'<rect x="200" y="200" width="1520" height="90" rx="10" fill="#141417" stroke="{INK}" stroke-width="7"/>'
    rooms = (("KITCHEN", 420), ("HALLWAY", 960), ("BEDROOM", 1500))
    for nm, x in rooms:
        out += f'<rect x="{x-60}" y="290" width="120" height="40" fill="{BG}" stroke="{GRAY}" stroke-width="5"/>' + text(x, 420, nm, 40, GRAY, 800, ls=6)
        out += f'<line x1="{x+270}" y1="320" x2="{x+270}" y2="{FLOOR}" stroke="{DIM}" stroke-width="5"/>' if x < 1500 else ""
    out += floor()
    at = p.get("at", "")
    pos = {"kitchen": 420, "hall": 960, "bed": 1500}
    if at in pos:
        x = pos[at]
        out += glow(x, 245, 90, ACC, 0.5 if on(p, "stop") else 0.25) + f'<ellipse cx="{x}" cy="245" rx="70" ry="38" fill="{ACC if on(p, "stop") else INK}"/>'
        out += text(x, 160, "TICK", 40, ACC, 800, font="mono", ls=6)
    if on(p, "bed"):
        out += bed(1180, FLOOR, "sleep")
    if on(p, "pop"):
        out += "".join(text(x, 160, "POP", 44, INK, 900) for x in (520, 1100, 1600))
    return out

@scene("vent")
def vent_scene(p):
    """Register cover close-up with four screws. tight=1 screws glow, driver=1 screwdriver, warm=1 glow through slats."""
    out = f'<rect x="560" y="160" width="800" height="520" rx="12" fill="{BG}" stroke="{INK}" stroke-width="10"/>'
    if on(p, "warm"):
        out += glow(960, 420, 220, ACC, 0.35)
    out += "".join(f'<rect x="620" y="{210+i*44}" width="680" height="22" rx="6" fill="{GRAY}"/>' for i in range(10))
    for x, y in ((600, 200), (1320, 200), (600, 640), (1320, 640)):
        out += (glow(x, y, 40, ACC, 0.7) if on(p, "tight") else "") + f'<circle cx="{x}" cy="{y}" r="22" fill="{ACC if on(p, "tight") else INK}"/><line x1="{x-14}" y1="{y}" x2="{x+14}" y2="{y}" stroke="{BG}" stroke-width="6"/>'
    if on(p, "driver"):
        out += f'<path d="M1330 650 L1600 860" stroke="{INK}" stroke-width="14" stroke-linecap="round"/><rect x="1560" y="820" width="140" height="56" rx="22" fill="{INK}" transform="rotate(38 1630 848)"/>'
    if p.get("label"):
        out += text(960, 800, p["label"].upper(), 44, ACC, 800, font="mono", ls=6)
    return out

@scene("drip")
def drip_scene(p):
    """Air handler leaking condensate; prints=1 small wet footprints to the bedroom door, towel=1."""
    out = floor() + f'<rect x="200" y="200" width="300" height="{FLOOR-200}" rx="10" fill="{BG}" stroke="{INK}" stroke-width="8"/>' + text(350, 300, "AC", 60, GRAY, 900)
    out += f'<path d="M500 600 H620 V{FLOOR-10}" stroke="{INK}" stroke-width="12" fill="none"/>' + "".join(f'<ellipse cx="620" cy="{FLOOR-60+i*20}" rx="8" ry="12" fill="{INK}" opacity=".7"/>' for i in range(2))
    out += f'<path d="M560 {FLOOR+4} Q760 {FLOOR-20} 900 {FLOOR+4}" fill="{GRAY}" opacity=".5"/>'
    out += door(1500, FLOOR - 380, 170, 380)
    if on(p, "prints"):
        out += "".join(f'<ellipse cx="{760+i*130}" cy="{FLOOR+40+(18 if i%2 else -18)}" rx="{14+i*1.5}" ry="{24+i*2}" fill="{INK}" opacity=".85" transform="rotate(90 {760+i*130} {FLOOR+40})"/>' for i in range(6))
        out += text(1150, 920 - 50, "SMALLER THAN YOURS", 36, ACC, 800, font="mono", ls=4) if on(p, "small") else ""
    if on(p, "towel"):
        out += f'<rect x="980" y="{FLOOR-6}" width="260" height="22" rx="6" fill="{INK}"/>' + cross(1110, 520, 0.5)
    return out

@scene("waterheater")
def waterheater_scene(p):
    """Water heater tank; knocks=N shows N knock marks, sediment=1 gray grit at the bottom, bucket=1."""
    out = floor() + f'<rect x="780" y="120" width="360" height="{FLOOR-160}" rx="60" fill="{BG}" stroke="{INK}" stroke-width="8"/><rect x="900" y="{FLOOR-40}" width="120" height="40" fill="{INK}"/>'
    out += glow(960, FLOOR - 90, 120, ACC, 0.35) + f'<path d="M880 {FLOOR-70} q20 -40 40 0 q20 -40 40 0 q20 -40 40 0 q20 -40 40 0" stroke="{ACC}" stroke-width="8" fill="none"/>'
    if on(p, "sediment"):
        out += "".join(f'<circle cx="{820+(i*37)%300}" cy="{FLOOR-130-(i*13)%40}" r="{6+i%3*3}" fill="{GRAY}"/>' for i in range(16))
    k = int(p.get("knocks", 0))
    if k:
        out += "".join(text(1400, 260 + i * 140, "KNOCK", 64, INK, 900) for i in range(k)) + text(480, 340, "YOU LIVE", 44, GRAY, 800, ls=6) + text(480, 420, "ALONE", 70, ACC, 900, ls=6)
    if on(p, "bucket"):
        out += f'<path d="M1300 {FLOOR} L1280 {FLOOR-180} L1520 {FLOOR-180} L1500 {FLOOR}Z" fill="{BG}" stroke="{INK}" stroke-width="7"/><ellipse cx="1400" cy="{FLOOR-170}" rx="110" ry="18" fill="{GRAY}"/><path d="M1360 {FLOOR-172} q20 -24 40 0" stroke="{ACC}" stroke-width="6" fill="none"/>'
    return out

@scene("panel")
def panel_scene(p):
    """Breaker panel with handwritten labels. hot=1 HIS ROOM glows, flipped=1 everything goes dark."""
    labels = ["KITCHEN", "DRYER", "MASTER", "BATH", "AC", "HIS ROOM", "FRIDGE", "FURNACE"]
    dark = on(p, "flipped")
    out = f'<rect x="560" y="80" width="800" height="760" rx="16" fill="{BG}" stroke="{INK if not dark else DIM}" stroke-width="10"/>'
    for i, lb in enumerate(labels):
        col, row = i % 2, i // 2
        x, y = 640 + col * 360, 160 + row * 170
        hot = lb == "HIS ROOM"
        if hot and on(p, "hot"):
            out += glow(x + 140, y + 50, 110, ACC, 0.55)
        c = ACC if hot and (on(p, "hot") or dark) else (DIM if dark else INK)
        out += f'<rect x="{x}" y="{y}" width="120" height="90" rx="10" fill="{BG}" stroke="{c}" stroke-width="6"/><rect x="{x+35 if hot and dark else x+65}" y="{y+20}" width="20" height="50" rx="4" fill="{c}"/>'
        out += text(x + 140, y + 60, lb, 34, c, 600, "start", extra='font-style="italic"')
    if dark:
        out += text(960, 900 - 30, "SILENCE", 46, GRAY, 500, font="mono", ls=12)
    return out

@scene("form")
def form_scene(p):
    """Manual J load-calc form with BEDROOMS + 1 circled."""
    out = f'<rect x="560" y="80" width="800" height="760" fill="{INK}"/>' + text(960, 170, "MANUAL J · LOAD CALCULATION", 36, BG, 900, ls=3)
    rows = [("SQ FT", "1,850"), ("WINDOWS", "14"), ("INSULATION", "R-30"), ("BEDROOMS", "3"), ("OCCUPANTS", "BEDROOMS + 1")]
    for i, (k, v) in enumerate(rows):
        y = 280 + i * 110
        out += f'<line x1="620" y1="{y+20}" x2="1300" y2="{y+20}" stroke="{GRAY}" stroke-width="3"/>' + text(640, y, k, 40, BG, 800, "start", ls=3) + text(1280, y, v, 40, BG, 600, "end", font="mono")
    if on(p, "circle"):
        out += f'<ellipse cx="1150" cy="{280+4*110-14}" rx="190" ry="60" fill="none" stroke="{REC}" stroke-width="8"/>' + text(1450, 720, "+1", 140, REC, 900)
    return out

@scene("bill")
def bill_scene(p):
    """Two identical houses, your electric bill much higher."""
    out = floor(700) + house(380, 700, 1.4, lit=False) + house(1220, 700, 1.4, lit=True)
    out += text(530, 790, p.get("a", "$142"), 70, GRAY, 800, font="mono") + text(1370, 790, p.get("b", "$298"), 80, ACC, 900, font="mono")
    out += text(530, 860, "NEIGHBOR", 32, GRAY, 800, ls=6) + text(1370, 860, "YOU", 32, ACC, 800, ls=6)
    return out

@scene("shiver")
def shiver_scene(p):
    """Person in bed under three blankets, shaking."""
    out = floor() + bed(560, FLOOR, "sleep") + "".join(f'<rect x="{600}" y="{FLOOR-150-i*26}" width="560" height="24" rx="10" fill="{INK if i%2 else GRAY}"/>' for i in range(3))
    out += "".join(f'<path d="M{560+i*14} {FLOOR-260} l-8 -20 M{1180-i*14} {FLOOR-260} l8 -20" stroke="{ACC}" stroke-width="6"/>' for i in range(3))
    if p.get("label"):
        out += text(960, 860 - 40, p["label"].upper(), 44, ACC, 800, font="mono", ls=6)
    return out

@scene("hum")
def hum_scene(p):
    """Dark silent house, a figure sitting still and humming."""
    out = floor() + window(1400, 200, 230, 280, moon=True) + fig(900, FLOOR, 1.1, "sit", "eyes")
    out += "".join(f'<path d="M{1000+i*40} {500-i*10} q20 -20 0 -40" stroke="{ACC}" stroke-width="6" fill="none" opacity="{1-i*0.25}"/>' for i in range(4))
    out += text(960, 860 - 30, "HMMMMMMMMM", 44, GRAY, 500, font="mono", ls=10)
    return out
