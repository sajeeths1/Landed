import math, sys, os

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
import json
WM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wordmark.json")))
WM_VB = " ".join(f"{v:.1f}" for v in WM["vb"])
WM_SW = 0.045 * WM["em"]
WM_H = WM["vb"][3] / WM["em"]          # svg height in em
def wordmark(fill):
    return (f'<svg viewBox="{WM_VB}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Landed">'
            f'<g {fill} stroke-width="{WM_SW:.1f}"><path transform="{WM["Ltf"]}" d="{WM["L"]}"/><path d="{WM["rest"]}"/></g></svg>')

# ---------- geometry (512 x 512 canvas) ----------
CX, CY = 228.0, 242.0          # orbit centre
RX, RY = 178.0, 64.0           # orbit radii
A = math.radians(-9)          # orbit tilt
ca, sa = math.cos(A), math.sin(A)

def to_screen(x, y):
    return (CX + x * ca - y * sa, CY + x * sa + y * ca)

TH0, TH1 = -38.0, -303.0       # plane travels theta 0 -> 1 (counter-clockwise on screen)
EXIT = 62.0                    # length of the straight departure after the arc

def local_pt(th):
    r = math.radians(th)
    return (RX * math.cos(r), RY * math.sin(r))

# sample the centre line: arc then tangent line
pts = []
N = 400
for i in range(N + 1):
    th = TH0 + (TH1 - TH0) * i / N
    pts.append(to_screen(*local_pt(th)))
r1 = math.radians(TH1)
tx, ty = RX * math.sin(r1), -RY * math.cos(r1)          # tangent for decreasing theta
tl = math.hypot(tx, ty); tx, ty = tx / tl, ty / tl
ex, ey = local_pt(TH1)
for i in range(1, 41):
    d = EXIT * i / 40
    pts.append(to_screen(ex + tx * d, ey + ty * d))

# cumulative length
cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + math.dist(pts[i], pts[i - 1]))
LTOT = cum[-1]

# trail: a few fine strands that fan apart and rejoin, plus dissolving dots at the tail
GAP = 30.0
def _normal(i):
    a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    dl = math.hypot(dx, dy) or 1
    return -dy / dl, dx / dl
def strand(t0, t1, off, wmax, skew=1.0):
    left, right = [], []
    LR = LTOT - GAP
    for i, (p, s) in enumerate(zip(pts, cum)):
        u = s / LR
        if u < t0: continue
        if u > t1: break
        t = (u - t0) / (t1 - t0)
        w = wmax * (math.sin(math.pi * t ** skew) ** 0.8)
        o = off * math.sin(math.pi * t)
        nx, ny = _normal(i)
        cx_, cy_ = p[0] + nx * o, p[1] + ny * o
        left.append((cx_ + nx * w / 2, cy_ + ny * w / 2))
        right.append((cx_ - nx * w / 2, cy_ - ny * w / 2))
    poly = left[::3] + [left[-1]] + right[::-1][::3] + [right[0]]
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + "Z"
def at(u):
    target = u * (LTOT - GAP)
    for i, s in enumerate(cum):
        if s >= target: return pts[i]
    return pts[-1]
RIBBON = strand(0.07, 1.0, 0.0, 7.5, 1.25)                       # main stroke, heavier toward the plane
WISPS = [(strand(0.16, 0.90, 9.0, 3.2), .55), (strand(0.30, 0.74, -8.0, 2.2), .38), (strand(0.52, 0.97, -5.0, 1.6), .5)]
DOTS = [(at(0.048), 2.5, .75), (at(0.028), 1.8, .5), (at(0.010), 1.2, .32)]
def extras(fill_attr):
    out = [f'<path {fill_attr} opacity="{o}" d="{d}"/>' for d, o in WISPS]
    out += [f'<circle {fill_attr} opacity="{o}" cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r}"/>' for c, r, o in DOTS]
    return "".join(out)
def star(cx, cy, r):
    return f"M{cx} {cy-r}Q{cx} {cy} {cx+r} {cy}Q{cx} {cy} {cx} {cy+r}Q{cx} {cy} {cx-r} {cy}Q{cx} {cy} {cx} {cy-r}Z"
RUNWAY = [(256, 363.2), (281, 362.4), (306, 361.2), (331, 359.6)]   # centre-line dashes on the foot
def runway(attr):
    return "".join(f'<rect {attr} x="{x-7}" y="{y-1.3}" width="14" height="2.6" rx="1.3" transform="rotate(-3 {x} {y})"/>' for x, y in RUNWAY)
RW_DEFS = ('<linearGradient id="rwg" gradientUnits="userSpaceOnUse" x1="244" y1="0" x2="343" y2="0">'
           '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".38" stop-color="#fff"/>'
           '<stop offset=".62" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
           '<mask id="rwFade" maskUnits="userSpaceOnUse" x="230" y="340" width="130" height="40"><rect x="230" y="340" width="130" height="40" fill="url(#rwg)"/></mask>')
CLOUDS_BACK = [(104, 262, 1.15, 0.1), (392, 170, 0.55, 0.35)]   # (x, y, scale, delay)
STARS = [(96, 176, 9), (352, 138, 6), (438, 300, 4.5)]

# plane path as compact arc + line (used for offset-path and the reveal mask)
p0 = to_screen(*local_pt(TH0)); p1 = to_screen(ex, ey); p2 = pts[-1]
FLIGHT = (f"M{p0[0]:.2f} {p0[1]:.2f} A{RX:.0f} {RY:.0f} {math.degrees(A):.0f} 1 0 {p1[0]:.2f} {p1[1]:.2f} "
          f"L{p2[0]:.2f} {p2[1]:.2f}")

# final plane pose
ang = math.degrees(math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0]))
PLANE_T = f"translate({p2[0]:.2f} {p2[1]:.2f}) rotate({ang:.2f})"

# near half-plane (in front of the L)
u = (ca, sa); v = (-sa, ca)
c = (CX, CY)
hp = [(c[0] - 600 * u[0], c[1] - 600 * u[1]), (c[0] + 600 * u[0], c[1] + 600 * u[1]),
      (c[0] + 600 * u[0] + 600 * v[0], c[1] + 600 * u[1] + 600 * v[1]),
      (c[0] - 600 * u[0] + 600 * v[0], c[1] - 600 * u[1] + 600 * v[1])]
NEAR = " ".join(f"{x:.1f},{y:.1f}" for x, y in hp)

L_PATH = "M224.5 356.3Q246.3 356.3 270.6 354.7Q294.9 353 313.1 350.9Q334.2 348.6 351.6 345.5L344.5 372Q341.6 371.8 335.7 371.7Q329.8 371.5 322.5 371.3Q315.3 371.2 307.3 371.1Q299.3 371 292.2 370.9Q285.1 370.9 279.6 370.8Q274 370.7 271.6 370.7H190V370Q191 366.6 191.9 361.5Q192.8 356.5 193.4 348.9Q194.1 341.4 194.4 331Q194.7 320.6 194.7 306.7V244C194.7 204 193.7 168 191.8 136H227.4C225.5 168 224.5 204 224.5 244Z"
LW = 20
PLANE = ("M21.5 0C20.6-1.8 15.5-2.9 8-2.9H-16.8C-19.7-2.9-21.4-1.4-22.3 0C-21.4 1.4-19.7 2.9-16.8 2.9H8C15.5 2.9 20.6 1.8 21.5 0Z"
         "M8.4-2.2-8.8-14.9h-4.5L-3.8-2.2ZM8.4 2.2-8.8 14.9h-4.5L-3.8 2.2Z"
         "M-13.9-2.2-20.2-7.5h-2.9L-18.5-2.2ZM-13.9 2.2-20.2 7.5h-2.9L-18.5 2.2Z")

BLUE, SKY = "#007CAC", "#5CC6EA"
SKYFILL = f'fill="{SKY}"'
LIGHTFILL = 'fill="#BFEAF8"'

# ---------- static SVG (transparent background, real knock-outs) ----------
static_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Landed logo">
  <defs>
    <clipPath id="near"><polygon points="{NEAR}"/></clipPath>
    <linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="190" y1="130" x2="340" y2="385">
      <stop offset="0" stop-color="#22B4E6"/><stop offset=".45" stop-color="{BLUE}"/><stop offset="1" stop-color="#004E73"/>
    </linearGradient>
    {RW_DEFS}
    <mask id="backMask" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512">
      <rect width="512" height="512" fill="#fff"/>
      <path d="{L_PATH}" fill="#000" stroke="#000" stroke-width="{LW+12}" stroke-linejoin="round"/>
    </mask>
    <mask id="lMask" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512">
      <rect width="512" height="512" fill="#fff"/>
      <g clip-path="url(#near)"><path d="{RIBBON}" fill="#000" stroke="#000" stroke-width="5" stroke-linejoin="round"/></g>
    </mask>
  </defs>
  <g mask="url(#backMask)"><path d="{RIBBON}" fill="{SKY}"/>{extras(SKYFILL)}</g>
  {clouds_static(CLOUDS_BACK)}
  <path d="{L_PATH}" fill="url(#lg)" stroke="url(#lg)" stroke-width="{LW}" stroke-linejoin="round" mask="url(#lMask)"/>
  <g mask="url(#rwFade)" opacity=".6">{runway('fill="#BFEAF8"')}</g>
  <g clip-path="url(#near)"><path d="{RIBBON}" fill="{SKY}"/>{extras(LIGHTFILL)}</g>
  {"".join(f'<path d="{star(*st)}" fill="{SKY}" opacity=".85"/>' for st in STARS)}
  <path d="{PLANE}" fill="{SKY}" transform="{PLANE_T}"/>
</svg>
'''
open(os.path.join(out_dir, f"landed-logo{SUF}.svg"), "w", encoding="utf-8").write(static_svg)

# ---------- animated HTML ----------
html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Landed logo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&display=swap" rel="stylesheet">
<style>
  :root {{ --bg:#ffffff; --blue:{BLUE}; --sky:{SKY}; --blue-hi:#22B4E6; --blue-lo:#004E73; --wisp:#BFEAF8; --cloud:#D6EFF9; --ink:#06364A; --muted:#6b8794; --line:#dcebf1; }}
  :root[data-theme="dark"] {{ --bg:#062431; --blue:#1FA3D6; --sky:#8EDDF7; --blue-hi:#5CCBF2; --blue-lo:#0B79A8; --wisp:#E2F7FE; --cloud:#134B63; --ink:#EFFAFE; --muted:#8FB4C2; --line:#124357; }}
  * {{ box-sizing:border-box; }}
  html,body {{ height:100%; margin:0; }}
  body {{ background:var(--bg); color:var(--ink); font-family:"Marcellus",Georgia,serif;
         display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; padding:16px;
         transition:background .4s ease; }}
  .stage {{ width:min(78vmin,520px); cursor:pointer; }}
  svg {{ display:block; width:100%; height:auto; overflow:visible; }}
  .word {{ font-family:"Marcellus",Georgia,serif; font-weight:400; -webkit-text-stroke:.045em var(--blue); font-size:clamp(34px,9vmin,64px); letter-spacing:.03em; color:var(--blue); margin-top:-11vmin; line-height:1; }}
  .word svg {{ display:block; margin:0 auto; height:{WM_H:.3f}em; width:auto; overflow:visible; }}
  .wm {{ fill:var(--blue); stroke:var(--blue); }}
  .tag  {{ font-size:clamp(12px,2.6vmin,17px); color:var(--muted); letter-spacing:.14em; text-transform:lowercase; margin-top:6px; }}
  .bar  {{ position:fixed; bottom:16px; display:flex; gap:8px; flex-wrap:wrap; justify-content:center; padding:0 12px; }}
  button[aria-pressed="true"] {{ color:var(--bg); background:var(--blue); border-color:var(--blue); }}
  button {{ font:inherit; font-size:13px; padding:8px 14px; border-radius:999px; border:1px solid var(--line);
           background:transparent; color:var(--muted); cursor:pointer; }}
  button:hover {{ color:var(--ink); border-color:var(--muted); }}

  .halo {{ fill:none; stroke:var(--bg); stroke-width:12; stroke-linejoin:round; transition:stroke .4s ease; }}
  .g0 {{ stop-color:var(--blue-hi); }} .g1 {{ stop-color:var(--blue); }} .g2 {{ stop-color:var(--blue-lo); }}
  .rw {{ fill:var(--wisp); }}
  .sheen {{ fill:#fff; opacity:0; }}
  .l    {{ fill:url(#lg); stroke:url(#lg); stroke-width:{LW}; stroke-linejoin:round; }}
  .lhalo {{ stroke-width:{LW+12}; }}
  .sky  {{ fill:var(--sky); }}
  .wisp {{ fill:var(--wisp); }}
  .halo.thin {{ stroke-width:5; }}
  .star {{ fill:var(--sky); transform-box:fill-box; transform-origin:center; opacity:.85; }}
  .reveal {{ fill:none; stroke:#fff; stroke-width:40; stroke-dasharray:100 100; stroke-dashoffset:0; }}
  .plane  {{ offset-path:path("{FLIGHT}"); offset-rotate:auto; offset-distance:100%; }}

{CLOUD_CSS}  /* ---- motion ---- */
  .play .lpath  {{ animation:lrise .85s cubic-bezier(.3,.85,.2,1) both; }}
  .play .reveal {{ animation:trail 2.3s cubic-bezier(.6,.02,.2,1) .55s both; }}
  .play .plane  {{ animation:fly 2.3s cubic-bezier(.6,.02,.2,1) .55s both; }}
  .play .star   {{ animation:pop .6s cubic-bezier(.3,1.6,.5,1) both, twinkle 3.2s ease-in-out 3.4s infinite; }}
  .play .s0 {{ animation-delay:1.55s, 3.4s; }} .play .s1 {{ animation-delay:1.0s, 4.3s; }} .play .s2 {{ animation-delay:2.7s, 5.1s; }}
  .play .rw     {{ animation:lamp .35s ease-out both; }}
  .play .rw:nth-of-type(1) {{ animation-delay:1.52s; }} .play .rw:nth-of-type(2) {{ animation-delay:1.55s; }} .play .rw:nth-of-type(3) {{ animation-delay:1.57s; }} .play .rw:nth-of-type(4) {{ animation-delay:1.60s; }}
  .play .sheen  {{ animation:sheen 1.1s cubic-bezier(.4,0,.2,1) 2.9s both; }}
  .play .mark   {{ animation:settle .7s cubic-bezier(.3,1.5,.5,1) 2.75s both; transform-origin:256px 300px; }}
  .play ~ .word {{ animation:rise .7s cubic-bezier(.2,.9,.2,1) 2.55s both; }}
  .play ~ .tag  {{ animation:rise .7s cubic-bezier(.2,.9,.2,1) 2.8s both; }}
  .stem {{ transform-origin:209px 376px; }}
  .foot {{ transform-origin:180px 353px; }}
  @keyframes lrise {{ from {{ clip-path:inset(100% -20px -20px -20px); }} to {{ clip-path:inset(-20px); }} }}
  @keyframes trail {{ from {{ stroke-dashoffset:100; }} to {{ stroke-dashoffset:0; }} }}
  @keyframes fly   {{ 0% {{ offset-distance:0%; opacity:0; }} 10% {{ opacity:1; }} 100% {{ offset-distance:100%; opacity:1; }} }}
  @keyframes pop   {{ from {{ transform:scale(0) rotate(-45deg); opacity:0; }} to {{ transform:scale(1) rotate(0); opacity:.85; }} }}
  @keyframes twinkle {{ 0%,100% {{ transform:scale(1); opacity:.85; }} 50% {{ transform:scale(.55); opacity:.4; }} }}
  @keyframes lamp  {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
  @keyframes sheen {{ 0% {{ translate:0 0; opacity:0; }} 15% {{ opacity:.13; }} 85% {{ opacity:.13; }} 100% {{ translate:520px 0; opacity:0; }} }}
  @keyframes settle{{ 0% {{ transform:scale(1); }} 40% {{ transform:scale(1.035); }} 100% {{ transform:scale(1); }} }}
  @keyframes rise  {{ from {{ opacity:0; transform:translateY(14px); }} to {{ opacity:1; transform:none; }} }}
</style>
</head>
<body>
  <div class="stage play" id="stage" title="Click to replay">
    <svg viewBox="0 0 512 512" role="img" aria-label="Landed logo: a capital L circled by a plane">
      <defs>
        <clipPath id="near"><polygon points="{NEAR}"/></clipPath>
        <linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="190" y1="130" x2="340" y2="385">
          <stop offset="0" class="g0"/><stop offset=".45" class="g1"/><stop offset="1" class="g2"/>
        </linearGradient>
        {RW_DEFS}
        <clipPath id="lClip"><path d="{L_PATH}" stroke-width="{LW}" stroke="#000" stroke-linejoin="round"/></clipPath>
        <clipPath id="stemClip"><rect x="180" y="132" width="58" height="244"/></clipPath>
        <mask id="rev" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512">
          <path class="reveal" pathLength="100" d="{FLIGHT}"/>
        </mask>
      </defs>
      <g class="mark">
        <!-- far side of the orbit: behind the letter -->
        <g mask="url(#rev)"><path class="sky" d="{RIBBON}"/>{extras('class="sky"')}</g>
        <path class="plane sky" d="{PLANE}"/>

        {clouds_html(CLOUDS_BACK)}
        <!-- the L -->
        <path class="halo lhalo" d="{L_PATH}"/>
        <path class="l lpath" d="{L_PATH}"/>
        <g mask="url(#rwFade)" opacity=".6">{runway('class="rw"')}</g>
        <g clip-path="url(#lClip)"><rect class="sheen" x="-70" y="100" width="46" height="320" transform="skewX(-20)"/></g>

        <!-- near side of the orbit: in front of the letter -->
        <g clip-path="url(#near)">
          <g mask="url(#rev)">
            <path class="halo thin" d="{RIBBON}"/>
            <path class="sky" d="{RIBBON}"/>{extras('class="wisp"')}
          </g>
          <path class="plane sky" d="{PLANE}"/>
        </g>
        {"".join(f'<path class="star s{i}" d="{star(*st)}"/>' for i, st in enumerate(STARS))}
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
open(os.path.join(out_dir, "landed-wordmark.svg"), "w", encoding="utf-8").write(wordmark(f'fill="{BLUE}" stroke="{BLUE}"'))
open(os.path.join(out_dir, f"landed-logo{SUF}.html"), "w", encoding="utf-8").write(html)
print("ok", round(LTOT, 1), PLANE_T)
