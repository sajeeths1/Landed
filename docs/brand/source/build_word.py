import math, sys, os, json

out_dir = sys.argv[1]

# ---------- optional cloud variant: run with a second argument "cloud" ----------
CLOUD = len(sys.argv) > 2 and sys.argv[2] == "cloud"
SUF = "-cloud" if CLOUD else ""
def cloud_shape(cx, cy, k):
    return (f'<g transform="translate({cx} {cy}) scale({k})"><rect x="-51" y="4" width="104" height="21" rx="10.5"/>'
            '<circle cx="-34" cy="8" r="17"/><circle cx="-10" cy="-9" r="25"/><circle cx="20" cy="-3" r="20"/><circle cx="40" cy="9" r="13"/></g>')
def clouds_html(items):
    if not CLOUD: return ""
    return "".join(f'<g class="cloud" style="animation-delay:{d}s, {d + 1}s">{cloud_shape(cx, cy, k)}</g>' for cx, cy, k, d in items)
def clouds_static(items):
    if not CLOUD: return ""
    return "".join(f'<g fill="#D6EFF9">{cloud_shape(cx, cy, k)}</g>' for cx, cy, k, d in items)
CLOUD_CSS = """  .cloud {{ fill:var(--cloud); }}
  .play .cloud {{ animation:cloudin 1s ease-out both, drift 7s ease-in-out infinite alternate; }}
  @keyframes cloudin {{ from {{ opacity:0; translate:-22px 0; }} to {{ opacity:1; translate:0 0; }} }}
  @keyframes drift {{ from {{ transform:translateX(0); }} to {{ transform:translateX(8px); }} }}
""".replace("{{", "{").replace("}}", "}")
HERE = os.path.dirname(os.path.abspath(__file__))
LT = json.load(open(os.path.join(HERE, "letters.json")))
LETTERS = LT["letters"]; EM = LT["em"]
LSW = 0.045 * EM                         # letter boldness (outline width)

BLUE, SKY, PALE = "#007CAC", "#5CC6EA", "#BFEAF8"
LW = 20                                   # L boldness (outline width)
K_FOOT = 1.75                             # how much longer the foot is than the regular Marcellus L
XE = 239.0 + 75.06 * K_FOOT               # right end of the L's foot
XR = LETTERS[-1]["x1"]                    # right edge of the word
FOOT_TOP = 354.0

# the L: Marcellus capital with the smoothed top and a lengthened foot (same recipe as the L logo)
L_PATH = open(os.path.join(HERE, "lpath_word.txt")).read().strip()
_old = "V200.2Q194.7 186.2 194.4 175.9Q194.1 165.5 193.4 157.8Q192.8 150.2 191.9 145.2Q191 140.1 190 136.7V136H229.3V136.7Q228.3 140.1 227.4 145.2Q226.5 150.2 225.9 157.8Q225.4 165.5 224.9 175.9Q224.5 186.2 224.5 200.2Z"
assert _old in L_PATH
L_PATH = L_PATH.replace(_old, "V244C194.7 204 193.7 168 191.8 136H227.4C225.5 168 224.5 204 224.5 244Z")

# ---------- flight path: orbit round the stem, then a wave with one loop over the letters ----------
CX, CY, RX, RY = 209.6, 222.0, 92.0, 31.0
A = math.radians(-9); ca, sa = math.cos(A), math.sin(A)
def to_screen(x, y): return (CX + x * ca - y * sa, CY + x * sa + y * ca)
def local_pt(th):
    r = math.radians(th); return (RX * math.cos(r), RY * math.sin(r))
def tan_ccw(th):                       # direction of travel on the orbit (theta decreasing), on screen
    r = math.radians(th); x, y = RX * math.sin(r), -RY * math.cos(r)
    l = math.hypot(x, y); x, y = x / l, y / l
    return (x * ca - y * sa, x * sa + y * ca)
def cubic(p, m0, q, m1, n=70):
    c1 = (p[0] + m0[0] / 3, p[1] + m0[1] / 3); c2 = (q[0] - m1[0] / 3, q[1] - m1[1] / 3)
    for j in range(1, n + 1):
        t = j / n; u = 1 - t
        pts.append((u**3 * p[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * q[0],
                    u**3 * p[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * q[1]))
Y_TOP, Y_BOT = 128.0, 236.0            # the pass heading left, and the bottom of the turn
TURN_CX, TURN_RX = 176.0, 92.0         # the turn sweeps round the left of the L's stem
TURN_CY, TURN_RY = (Y_TOP + Y_BOT) / 2, (Y_BOT - Y_TOP) / 2
LAST = LETTERS[-1]
X_START = 372.0
pts = [(X_START, Y_TOP)]
for i in range(1, 61):                                  # heading left
    pts.append((X_START + (TURN_CX - X_START) * i / 60, Y_TOP))
ENTRY_N = len(pts)
for i in range(1, 121):                                 # half an ellipse: round the left of the L, back underneath
    th = math.radians(-90 - 180 * i / 120)
    pts.append((TURN_CX + TURN_RX * math.cos(th), TURN_CY + TURN_RY * math.sin(th)))
ORBIT_N = len(pts)
# gentle climb after the L, one round loop through the first d and the e, then a high arch over the last d,
# carrying on up and away to the right (the landing itself is a separate approach, below)
LOOP_BOTTOM_I = 6                      # index in `way` of the bottom of the loop
way = [pts[-1], (440, 224), (700, 196), (880, 166), (975, 186),
       (992, 246), (940, 296), (872, 278), (892, 236),
       (1010, 208), (1150, 176), (1290, 160), (LAST["x1"] + 26, 148), (LAST["x1"] + 36, 114), (LAST["x1"] - 6, 87)]   # level run across the e and in FRONT of the last d, then up and away on its right
FAR = way[-1]
tang = [(190, -6)]
for i in range(1, len(way) - 1):
    tang.append(((way[i + 1][0] - way[i - 1][0]) * 0.5, (way[i + 1][1] - way[i - 1][1]) * 0.5))
tang.append((-70, -14))
WAY_START = len(pts) - 1
for i in range(len(way) - 1):
    cubic(way[i], tang[i], way[i + 1], tang[i + 1], 60)
MID_I = WAY_START + LOOP_BOTTOM_I * 60          # the path is split here so the two passes of the loop never reveal each other
SHRINK_I = WAY_START + 12 * 60                  # from here on the plane is flying away, so it gets smaller

# ---- the plane's other two views (same flat style and colour), each drawn around its body centre ----
# landed, facing the viewer: body with windscreen cut-out, slim wings with upturned tips, two wheels, fin, tailplane
_FRONT = ["M-9 -2.2L-45 -4.4L-47.6 -10L-46 -3L-9 4H9L46 -3L47.6 -10L45 -4.4L9 -2.2Z",
          "M-1.2 -9L0 -32L1.2 -9Z",
          "M-19 -11.8L0 -8.8L19 -11.8L0 -6.2Z",
          "M-9 0a9 10 0 1 0 18 0a9 10 0 1 0 -18 0Z"
          "M-5.6 -4.6Q0 -6.9 5.6 -4.6Q6.5 -2.7 5 -1.5Q0 -2.8 -5 -1.5Q-6.5 -2.7 -5.6 -4.6Z",
          "M-19.3 7.8a4.6 4.6 0 1 0 9.2 0a4.6 4.6 0 1 0 -9.2 0Z", "M10.1 7.8a4.6 4.6 0 1 0 9.2 0a4.6 4.6 0 1 0 -9.2 0Z"]
# turning, seen three-quarters on with the nose toward the viewer's left: near wing long, far wing short, fin leaning back
_TURN = ["M-8 -3L-38 -1.2L-40.5 2L-9 7Z",
         "M8 -2.5L44 -7L46.5 -11L45.5 -4L10 8Z",
         "M2 -9L10.5 -31L13.5 -31L11 -8Z",
         "M9 -13.5L24 -16.5L25 -15L10 -9.8Z",
         "M-12 0a12 10.6 0 1 0 24 0a12 10.6 0 1 0 -24 0Z"
         "M-9.6 -4.2Q-4 -8.2 3 -6.3Q4.2 -3.6 2 -2.4Q-4 -4.3 -8.3 -1Q-10.2 -2.4 -9.6 -4.2Z",
         "M-24.4 8a4.6 4.6 0 1 0 9.2 0a4.6 4.6 0 1 0 -9.2 0Z", "M14 9.6a5 5 0 1 0 10 0a5 5 0 1 0 -10 0Z"]
def view(parts, attr):
    return "".join(f'<path {attr} fill-rule="evenodd" d="{d}"/>' for d in parts)
def front_body(attr): return view(_FRONT, attr)
FRONT_GLASS = ""
FRONT_K = 1.12                         # smaller, so both wheels sit on the flat top of the d
FRONT_BOTTOM = 12.4                    # wheels reach this far below the body centre
TOP_CX = LAST["x1"] - 18.8             # centre of the flat top of the d's tall stroke
FRONT_Y = LAST["top"] - LSW / 2 - FRONT_BOTTOM * FRONT_K
LAND = (TOP_CX, FRONT_Y)
FRONT_T = f"translate({LAND[0]:.1f} {FRONT_Y:.1f}) scale({FRONT_K})"

cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + math.dist(pts[i], pts[i - 1]))
LTOT = cum[-1]
ORBIT_LEN = cum[ORBIT_N - 1] - cum[ENTRY_N - 1]
FLIGHT = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts[::2] + [pts[-1]])
END = pts[-1]
ang = math.degrees(math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0]))
PLANE_T = f"translate({END[0]:.2f} {END[1]:.2f}) rotate({ang:.2f})"
nx_ = (LETTERS[0]['x1'] + LETTERS[1]['x1']) / 2
ex = (LETTERS[3]["x0"] + LETTERS[3]["x1"]) / 2

# ---------- trail ----------
GAP = 30.0
def _normal(i):
    a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    dl = math.hypot(dx, dy) or 1
    return -dy / dl, dx / dl
def strand(t0, t1, off, wmax, skew=1.0, lo=0.0, hi=1.0):
    left, right = [], []
    LR = LTOT - GAP
    for i, (p, s) in enumerate(zip(pts, cum)):
        u = s / LR
        if u < t0 or u < lo: continue
        if u > t1 or u > hi: break
        t = (u - t0) / (t1 - t0)
        w = wmax * (math.sin(math.pi * t ** skew) ** 0.8)
        o = off * math.sin(math.pi * t)
        nx, ny = _normal(i)
        cx_, cy_ = p[0] + nx * o, p[1] + ny * o
        left.append((cx_ + nx * w / 2, cy_ + ny * w / 2))
        right.append((cx_ - nx * w / 2, cy_ - ny * w / 2))
    if len(left) < 2: return ""
    poly = left[::2] + [left[-1]] + right[::-1][::2] + [right[0]]
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + "Z"
def at(u):
    target = u * (LTOT - GAP)
    for i, s in enumerate(cum):
        if s >= target: return pts[i]
    return pts[-1]
U_MID = cum[MID_I] / (LTOT - GAP)
SEGS = [(0.0, U_MID), (U_MID, 1.0)]
_STRANDS = [(0.035, 1.0, 0.0, 4.6, 1.3, 1.0), (0.06, 0.80, 9.0, 1.9, 1.0, .42), (0.18, 0.66, -8.5, 1.4, 1.0, .3),
            (0.46, 0.98, -6.5, 1.3, 1.0, .4), (0.30, 0.92, 14.0, 1.0, 1.0, .22), (0.62, 0.99, 4.0, 1.0, 1.0, .35)]
DOTS = [(at(0.024), 2.3, .75), (at(0.014), 1.7, .5), (at(0.005), 1.1, .32)]
def trail(attr, k):
    lo, hi = SEGS[k]
    out = []
    for t0, t1, off, w, skew, op in _STRANDS:
        d = strand(t0, t1, off, w, skew, lo, hi)
        if d: out.append(f'<path {attr} opacity="{op}" d="{d}"/>')
    if k == 0:
        out += [f'<circle {attr} opacity="{o}" cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r}"/>' for c, r, o in DOTS]
    return "".join(out)
RIBBON = strand(0.035, 1.0, 0.0, 4.6, 1.3)
def extras(attr): return ""
SEG_I = [(0, MID_I), (MID_I, len(pts) - 1)]
FLIGHT_SEG = ["M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts[a:b + 1:2] + [pts[b]]) for a, b in SEG_I]
def star(cx, cy, r):
    return f"M{cx} {cy-r}Q{cx} {cy} {cx+r} {cy}Q{cx} {cy} {cx} {cy+r}Q{cx} {cy} {cx-r} {cy}Q{cx} {cy} {cx} {cy-r}Z"
# cloud variant: one long, low cloud under the word, so "Landed" rests on it
BANK_CX, BANK_CY, BANK_W = (190 + XR) / 2 + 10, 432.0, 800.0
def bank_shape():
    w = BANK_W; n = 13
    out = [f'<rect x="{-w / 2 - 26:.1f}" y="0" width="{w + 52:.1f}" height="44" rx="22"/>']
    for i in range(n):
        t = i / (n - 1)
        r = 30 + 24 * math.sin(math.pi * t) + (7 if i % 2 else -3)      # bigger puffs toward the middle, alternating
        cy = 14 - (r - 30) * 0.55
        out.append(f'<circle cx="{-w / 2 + t * w:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>')
    return f'<g transform="translate({BANK_CX:.1f} {BANK_CY})">' + "".join(out) + "</g>"
def bank_html():
    return f'<g class="cloud" style="animation-delay:0.1s, 1.1s">{bank_shape()}</g>' if CLOUD else ""
def bank_static():
    return f'<g fill="#D6EFF9">{bank_shape()}</g>' if CLOUD else ""
STARS = []      # sparkles removed

# near side (drawn in front): below the orbit's long axis near the L, and everything right of the orbit
X1 = 330.0
def axis_y(cx, cy, x): return cy + (x - cx) * math.tan(A)
NEAR_SHAPES = (f'<polygon points="-500,{axis_y(CX, CY, -500):.1f} {X1},{axis_y(CX, CY, X1):.1f} {X1},700 -500,700"/>'
               f'<rect x="{X1}" y="-200" width="2400" height="900"/>')

PLANE = ("M21.5 0C20.6-1.8 15.5-2.9 8-2.9H-16.8C-19.7-2.9-21.4-1.4-22.3 0C-21.4 1.4-19.7 2.9-16.8 2.9H8C15.5 2.9 20.6 1.8 21.5 0Z"
         "M8.4-2.2-8.8-14.9h-4.5L-3.8-2.2ZM8.4 2.2-8.8 14.9h-4.5L-3.8 2.2Z"
         "M-13.9-2.2-20.2-7.5h-2.9L-18.5-2.2ZM-13.9 2.2-20.2 7.5h-2.9L-18.5 2.2Z")

# runway dashes along the foot
RUNWAY = []
x = 256.0
while x < XE - 14:
    RUNWAY.append((x, 363.2 - (x - 256) * 0.05)); x += 25
def dash(attr, x, y, extra=""):
    return f'<rect {attr} {extra} x="{x-7:.1f}" y="{y-1.3:.1f}" width="14" height="2.6" rx="1.3" transform="rotate(-3 {x:.1f} {y:.1f})"/>'
def rw_defs():
    return (f'<linearGradient id="rwg" gradientUnits="userSpaceOnUse" x1="248" y1="0" x2="{XE-6:.0f}" y2="0">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".34" stop-color="#fff"/>'
            '<stop offset=".66" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="rwFade" maskUnits="userSpaceOnUse" x="230" y="340" width="{XE-220:.0f}" height="44"><rect x="230" y="340" width="{XE-220:.0f}" height="44" fill="url(#rwg)"/></mask>')
LGRAD = '<linearGradient id="tg" gradientUnits="userSpaceOnUse" x1="0" y1="126" x2="0" y2="378">'
GRAD = '<linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="190" y1="130" x2="340" y2="385">'

VB = (58, 20, XR + 120 - 58, (492 if CLOUD else 404) - 20)
VBS = " ".join(f"{v:.0f}" for v in VB)

# ---------- timing ----------
T0, DUR = 0.05, 3.1
EASE = (.38, .1, .66, .8)          # gentle start, brisk finish (no long glide to a stop)
EASE_CSS = "cubic-bezier(" + ",".join(str(v) for v in EASE) + ")"
def bez(u, a, b): return 3 * (1 - u) ** 2 * u * a + 3 * (1 - u) * u * u * b + u ** 3
def _solve(target, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        if bez(m, a, b) < target: lo = m
        else: hi = m
    return lo
def progress(sec):                    # how far along the path the plane is, `sec` seconds after take-off
    x = min(1.0, max(0.0, sec / DUR))
    return bez(_solve(x, EASE[0], EASE[2]), EASE[1], EASE[3])
def time_at(frac):                    # when the plane is `frac` along the path
    return T0 + DUR * bez(_solve(frac, EASE[1], EASE[3]), EASE[0], EASE[2])
T_RW = 0.0   # set below, once the L's own timing is known       # runway starts lighting when the plane is ~55% round the stem
T_END = T0 + DUR

LAST = LETTERS[-1]
DGRAD = f'<linearGradient id="dg" gradientUnits="userSpaceOnUse" x1="{LAST["x0"]:.0f}" y1="120" x2="{LAST["x1"]:.0f}" y2="385">'
# ---------- static SVG ----------
letters_static = "".join(f'<path d="{l["d"]}"/>' for l in LETTERS[:-1])
static_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VBS}" role="img" aria-label="Landed">
  <defs>
    <clipPath id="near">{NEAR_SHAPES}</clipPath>
    {GRAD}<stop offset="0" stop-color="#0F97CB"/><stop offset=".45" stop-color="{BLUE}"/><stop offset="1" stop-color="#00668F"/></linearGradient>
    {DGRAD}<stop offset="0" stop-color="#0F97CB"/><stop offset=".45" stop-color="{BLUE}"/><stop offset="1" stop-color="#00668F"/></linearGradient>
    {LGRAD}<stop offset="0" stop-color="{BLUE}"/><stop offset=".62" stop-color="{BLUE}"/><stop offset="1" stop-color="#00709D"/></linearGradient>
    {rw_defs()}
    <mask id="backMask" maskUnits="userSpaceOnUse" x="0" y="0" width="1700" height="500">
      <rect width="1700" height="500" fill="#fff"/>
      <path d="{L_PATH}" fill="#000" stroke="#000" stroke-width="{LW+12}" stroke-linejoin="round"/>
    </mask>
    <mask id="lMask" maskUnits="userSpaceOnUse" x="0" y="0" width="1700" height="500">
      <rect width="1700" height="500" fill="#fff"/>
      <g clip-path="url(#near)"><path d="{RIBBON}" fill="#000" stroke="#000" stroke-width="5" stroke-linejoin="round"/></g>
    </mask>
  </defs>
  {bank_static()}
  <path d="{L_PATH}" fill="url(#lg)" stroke="url(#lg)" stroke-width="{LW}" stroke-linejoin="round"/>
  <g mask="url(#rwFade)" opacity=".6">{"".join(dash(f'fill="{PALE}"', x, y) for x, y in RUNWAY)}</g>
  <g fill="url(#tg)" stroke="url(#tg)" stroke-width="{LSW:.1f}">{letters_static}</g>
  <path d="{LAST["d"]}" fill="url(#tg)" stroke="url(#tg)" stroke-width="{LSW:.1f}"/>
  {"".join(f'<path d="{star(*st)}" fill="{SKY}" opacity=".85"/>' for st in STARS)}
  <g transform="{FRONT_T}">{front_body(f'fill="{SKY}"')}</g>
</svg>
'''
open(os.path.join(out_dir, f"landed-wordmark-logo{SUF}.svg"), "w", encoding="utf-8").write(static_svg)

# The trail is time-based: each layer shows the stretch of path the plane covered in its last few
# tenths of a second, so it shortens when the plane slows and is gone moments after it arrives.
TAIL = [0.3, 0.2, 0.09]      # seconds of trail per layer, longest = faintest
STEPS = 80
def reveal_kf(i, lag, k):
    a, b = SEG_I[k]; s_lo, s_hi = cum[a], cum[b]
    total = DUR + lag
    def pct(sec): return 100 * min(1.0, max(0.0, (progress(sec) * LTOT - s_lo) / (s_hi - s_lo)))
    frames = []
    for j in range(STEPS + 1):
        sec = total * j / STEPS
        head = pct(sec); tail = pct(sec - lag)
        frames.append(f"{100 * j / STEPS:.2f}% {{ stroke-dasharray:{head - tail:.2f} 400; stroke-dashoffset:{-tail:.2f}; }}")
    return f"@keyframes trail{i}s{k} {{ " + " ".join(frames) + " }"
REVEAL_CSS = "\n  ".join(f".play .r{i}s{k} {{ animation:trail{i}s{k} {DUR + lag:.2f}s linear {T0}s both; }}" for k in range(2) for i, lag in enumerate(TAIL))
REVEAL_KF = "\n  ".join(reveal_kf(i, lag, k) for k in range(2) for i, lag in enumerate(TAIL))
REV_MASKS = "".join(
    f'<mask id="rev{k}" maskUnits="userSpaceOnUse" x="0" y="0" width="1700" height="500">'
    + "".join(f'<path class="reveal r{i}s{k}" pathLength="100" stroke-opacity="{op}" d="{FLIGHT_SEG[k]}"/>' for i, op in enumerate([".3", ".45", "1"]))
    + "</mask>" for k in range(2))

# the flying plane shrinks as it heads away
FAR_K = 0.5
def _smooth(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def fly_scale(sec):
    s_now = progress(sec) * LTOT
    return 1 - (1 - FAR_K) * _smooth((s_now - cum[SHRINK_I]) / (LTOT - cum[SHRINK_I]))
PSCALE_KF = "@keyframes pscale { " + " ".join(f"{100 * j / STEPS:.2f}% {{ transform:scale({fly_scale(DUR * j / STEPS):.3f}); }}" for j in range(STEPS + 1)) + " }"

# the turn and approach: carries on right a touch, swings round, and comes down and toward the viewer onto the d
T_TURN = T_END - 0.16                  # starts as the flying plane fades
AP = 0.8                              # seconds from the turn to touchdown
K0 = 0.26                              # size of the turning plane when far away, relative to its landed size
A0, A1, A2, A3 = FAR, (FAR[0] - 20, FAR[1] - 3), (LAND[0] - 8, LAND[1] - 22), LAND   # keeps climbing, swings back over the top, comes down onto the d
def appr(u):
    v = 1 - u
    x = v**3 * A0[0] + 3 * v * v * u * A1[0] + 3 * v * u * u * A2[0] + u**3 * A3[0]
    y = v**3 * A0[1] + 3 * v * v * u * A1[1] + 3 * v * u * u * A2[1] + u**3 * A3[1]
    return x, y
ASTEPS = 50
def _ease(x): return x * x * (3 - 2 * x)
APPR_KF = "@keyframes appr { " + " ".join(
    "{:.1f}% {{ transform:translate({:.1f}px, {:.1f}px) scale({:.3f}); }}".format(
        100 * j / ASTEPS, *appr(_ease(j / ASTEPS)), K0 + (1 - K0) * _ease(j / ASTEPS) ** 1.5) for j in range(ASTEPS + 1)) + " }"
T_FIN = T_TURN + AP
def _cross_front():
    for i in range(ORBIT_N, len(pts)):                # on the run heading right: just past the L's stem
        if pts[i][0] >= 246: return i
    return ORBIT_N
T_L = time_at(cum[_cross_front()] / LTOT)
# each of the letters after the L appears as the plane reaches it
def reach_time(xc):
    for i in range(ORBIT_N, len(pts)):
        if pts[i][0] >= xc: return time_at(cum[i] / LTOT)
    return T_END
def _mid(l): return (l["x0"] + l["x1"]) / 2
LT_DELAY = [reach_time((l["x0"] + l["x1"]) / 2) for l in LETTERS[:-1]] + [reach_time(LETTERS[-1]["x0"] - 40)]   # each letter starts as the plane passes over it; the last d is there to land on
T_RW = T_L + 0.4
# ---------- animated HTML ----------
letters_html = "".join(f'<path class="lt" style="animation-delay:{LT_DELAY[i]:.2f}s" d="{l["d"]}"/>' for i, l in enumerate(LETTERS[:-1])) + f'<path class="lt" style="animation-delay:{LT_DELAY[4]:.2f}s" d="{LAST["d"]}"/>'
runway_html = "".join(dash('class="rw"', x, y, f'style="animation-delay:{T_RW + i * 0.05:.2f}s"') for i, (x, y) in enumerate(RUNWAY))
star_delays = [time_at(0.12), time_at(0.45), time_at(0.8), T_END + 0.1]
stars_html = "".join(f'<path class="star" style="animation-delay:{d:.2f}s, {T_END + 0.6 + i * 0.7:.2f}s" d="{star(*st)}"/>' for i, (st, d) in enumerate(zip(STARS, star_delays)))

html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Landed wordmark logo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&display=swap" rel="stylesheet">
<style>
  :root {{ --bg:#ffffff; --blue:{BLUE}; --sky:{SKY}; --blue-hi:#0F97CB; --blue-lo:#00668F; --blue-lo2:#00709D; --wisp:{PALE}; --cloud:#D6EFF9; --ink:#06364A; --muted:#6b8794; --line:#dcebf1; }}
  :root[data-theme="dark"] {{ --bg:#062431; --blue:#1FA3D6; --sky:#8EDDF7; --blue-hi:#3FB6E6; --blue-lo:#168CC0; --blue-lo2:#1A93C6; --wisp:#E2F7FE; --cloud:#134B63; --ink:#EFFAFE; --muted:#8FB4C2; --line:#124357; }}
  * {{ box-sizing:border-box; }}
  html,body {{ height:100%; margin:0; }}
  body {{ background:var(--bg); color:var(--ink); font-family:"Marcellus",Georgia,serif;
         display:flex; flex-direction:column; align-items:center; justify-content:center; gap:4px; padding:16px;
         transition:background .4s ease; }}
  .stage {{ width:min(94vw,1100px); cursor:pointer; }}
  svg {{ display:block; width:100%; height:auto; overflow:visible; }}
  .tag  {{ font-size:clamp(13px,2.6vmin,20px); color:var(--muted); letter-spacing:.22em; text-transform:lowercase; }}
  .bar  {{ position:fixed; bottom:16px; display:flex; gap:8px; }}
  button {{ font:inherit; font-size:13px; padding:8px 14px; border-radius:999px; border:1px solid var(--line);
           background:transparent; color:var(--muted); cursor:pointer; }}
  button:hover {{ color:var(--ink); border-color:var(--muted); }}

  .halo {{ fill:none; stroke:var(--bg); stroke-linejoin:round; transition:stroke .4s ease; }}
  .lhalo {{ stroke-width:{LW+12}; }} .halo.thin {{ stroke-width:5; }}
  .g0 {{ stop-color:var(--blue-hi); }} .g1 {{ stop-color:var(--blue); }} .g2 {{ stop-color:var(--blue-lo); }} .g3 {{ stop-color:var(--blue-lo2); }}
  .l    {{ fill:url(#lg); stroke:url(#lg); stroke-width:{LW}; stroke-linejoin:round; }}
    .lt   {{ fill:url(#tg); stroke:url(#tg); stroke-width:{LSW:.1f}; }}
  .rw   {{ fill:var(--wisp); }}
  .sheen {{ fill:#fff; opacity:0; }}
  .sky  {{ fill:var(--sky); }}
  .star {{ fill:var(--sky); transform-box:fill-box; transform-origin:center; opacity:.85; }}
  .reveal {{ fill:none; stroke:#fff; stroke-width:40; stroke-dasharray:0 300; stroke-dashoffset:0; }}
  .plane  {{ offset-path:path("{FLIGHT}"); offset-rotate:auto; offset-distance:100%; opacity:0; }}
  .appr {{ transform:translate({LAND[0]:.1f}px, {LAND[1]:.1f}px); }}
  .vturn {{ opacity:0; }}
  .front .glass {{ fill:var(--blue); }}

{CLOUD_CSS}  /* ---- motion ---- */
  .play .lpath  {{ animation:appear .45s ease-in-out {T_L:.2f}s both; }}
  .play .lt     {{ animation:appear .45s ease-in-out both; }}
  @keyframes appear {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
  {REVEAL_CSS}
  .play .plane  {{ animation:fly {DUR}s {EASE_CSS} {T0}s both; }}
  .play .pshape {{ animation:pscale {DUR}s linear {T0}s both; }}
  .play .appr   {{ animation:appr {AP}s linear {T_TURN:.2f}s both; }}
  .play .vturn  {{ animation:vturn {AP}s linear {T_TURN:.2f}s both; }}
  .play .vfront {{ animation:vfront {AP}s linear {T_TURN:.2f}s both; }}
  .play .rw     {{ animation:lamp .35s ease-out both; }}
  .play .star   {{ animation:pop .6s cubic-bezier(.3,1.6,.5,1) both, twinkle 3.2s ease-in-out infinite; }}
  .play .sheen  {{ animation:sheen 1.5s cubic-bezier(.4,0,.2,1) {T_FIN + 0.1:.2f}s both; }}
  .play .mark   {{ animation:settle .7s cubic-bezier(.3,1.5,.5,1) {T_FIN - 0.05:.2f}s both; transform-origin:{VB[0] + VB[2] / 2:.0f}px 300px; }}
  .play ~ .tag  {{ animation:rise .7s cubic-bezier(.2,.9,.2,1) {T_END - 0.1:.2f}s both; }}
  @keyframes lrise {{ 0% {{ clip-path:inset(100% -20px 0px -20px); opacity:0; }} 2% {{ opacity:1; }} 100% {{ clip-path:inset(-20px); opacity:1; }} }}
  {REVEAL_KF}
  @keyframes fly   {{ 0% {{ offset-distance:0%; opacity:0; }} 6% {{ opacity:1; }} 94% {{ opacity:1; }} 100% {{ offset-distance:100%; opacity:0; }} }}
  {PSCALE_KF}
  {APPR_KF}
  @keyframes vturn  {{ 0% {{ opacity:0; filter:blur(1.2px); }} 16% {{ opacity:1; filter:blur(0); }} 46% {{ opacity:1; filter:blur(0); }} 70% {{ opacity:0; filter:blur(1.4px); }} 100% {{ opacity:0; }} }}
  @keyframes vfront {{ 0% {{ opacity:0; }} 44% {{ opacity:0; filter:blur(1.4px); }} 70% {{ opacity:1; filter:blur(0); }} 100% {{ opacity:1; filter:blur(0); }} }}
  
  @keyframes lamp  {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
  @keyframes pop   {{ from {{ transform:scale(0) rotate(-45deg); opacity:0; }} to {{ transform:scale(1) rotate(0); opacity:.85; }} }}
  @keyframes twinkle {{ 0%,100% {{ transform:scale(1); opacity:.85; }} 50% {{ transform:scale(.55); opacity:.4; }} }}
  @keyframes sheen {{ 0% {{ translate:0 0; opacity:0; }} 15% {{ opacity:.13; }} 85% {{ opacity:.13; }} 100% {{ translate:440px 0; opacity:0; }} }}
  @keyframes settle{{ 0% {{ transform:scale(1); }} 40% {{ transform:scale(1.02); }} 100% {{ transform:scale(1); }} }}
  @keyframes rise  {{ from {{ opacity:0; transform:translateY(14px); }} to {{ opacity:1; transform:none; }} }}
</style>
</head>
<body>
  <div class="stage play" id="stage" title="Click to replay">
    <svg viewBox="{VBS}" role="img" aria-label="Landed: a plane circles the L and flies across the word to the last d">
      <defs>
        <clipPath id="near">{NEAR_SHAPES}</clipPath>
        {GRAD}<stop offset="0" class="g0"/><stop offset=".45" class="g1"/><stop offset="1" class="g2"/></linearGradient>
        {DGRAD}<stop offset="0" class="g0"/><stop offset=".45" class="g1"/><stop offset="1" class="g2"/></linearGradient>
        {LGRAD}<stop offset="0" class="g1"/><stop offset=".62" class="g1"/><stop offset="1" class="g3"/></linearGradient>
        {rw_defs()}
        <clipPath id="lClip"><path d="{L_PATH}" stroke-width="{LW}" stroke="#000" stroke-linejoin="round"/></clipPath>
        <linearGradient id="wg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <mask id="wipeMask" maskUnits="userSpaceOnUse" x="-200" y="0" width="2600" height="500">
          <g class="wipe"><rect x="-3000" y="0" width="2881" height="500" fill="#fff"/><rect x="-120" y="0" width="120" height="500" fill="url(#wg)"/></g>
        </mask>
        {REV_MASKS}<mask id="revx"></mask>
      </defs>
      <g class="mark">
        <!-- far side of the orbit: behind the L's stem -->

        {bank_html()}
        <!-- the L with its runway foot, and the rest of the word -->
        <path class="l lpath" d="{L_PATH}"/>
        <g mask="url(#rwFade)" opacity=".6">{runway_html}</g>
        <g clip-path="url(#lClip)"><rect class="sheen" x="120" y="100" width="46" height="320" transform="skewX(-20)"/></g>
        <g>{letters_html}</g>

        <!-- near side of the orbit and the flight across the word: in front -->
        <g>
          <g mask="url(#rev0)">{trail('class="sky"', 0)}</g>
          <g mask="url(#rev1)">{trail('class="sky"', 1)}</g>
          <g class="plane"><path class="pshape sky" d="{PLANE}"/></g>
        </g>
        <g class="appr"><g class="vturn" transform="scale({FRONT_K})">{view(_TURN, 'class="sky"')}</g><g class="vfront" transform="scale({FRONT_K})">{view(_FRONT, 'class="sky"')}</g></g>
        {stars_html}
      </g>
    </svg>
  </div>
  <div class="bar">
    <button id="replay">Replay</button>
    <button id="theme">Dark / light</button>
  </div>
<script>
  const stage = document.getElementById('stage');
  function replay() {{ stage.classList.remove('play'); void stage.offsetWidth; stage.classList.add('play'); }}
  stage.addEventListener('click', replay);
  document.getElementById('replay').addEventListener('click', replay);
  document.getElementById('theme').addEventListener('click', () => {{
    const r = document.documentElement;
    r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark';
  }});
  // ?t=1.4 freezes the animation at that second (handy for grabbing stills); ?theme=dark starts dark
  const q = new URLSearchParams(location.search);
  if (q.get('theme') === 'dark') document.documentElement.dataset.theme = 'dark';
  if (q.has('t')) requestAnimationFrame(() => document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = parseFloat(q.get('t')) * 1000; }}));
</script>
</body>
</html>
'''
open(os.path.join(out_dir, f"landed-wordmark-logo{SUF}.html"), "w", encoding="utf-8").write(html)
print("ok", round(LTOT), round(ORBIT_LEN), round(T_RW, 2), round(T_END, 2), PLANE_T, VBS)
