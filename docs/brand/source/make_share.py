import re, sys, os
W = sys.argv[1]

def grab(name):
    h = open(os.path.join(W, name), encoding="utf-8").read()
    css = re.search(r"<style>(.*?)</style>", h, re.S).group(1)
    body = re.search(r"<body>(.*?)<div class=\"bar\">", h, re.S).group(1)
    # page-level rules don't apply inside a shadow root; drop the ones that would be confusing to keep
    css = re.sub(r"\s*:root[^{]*\{[^}]*\}", "", css)
    css = re.sub(r"\s*html,body \{[^}]*\}", "", css)
    css = re.sub(r"\s*body \{[^}]*\}", "", css, flags=re.S)
    css = re.sub(r"\s*\.bar\s*\{[^}]*\}", "", css)
    css = re.sub(r"\s*button[^{]*\{[^}]*\}", "", css, flags=re.S)
    body = body.replace(' title="Click to replay"', "")
    return css, body

css_l, body_l = grab("landed-logo.html")
css_w, body_w = grab("landed-wordmark-logo.html")
host_css = ":host { display:flex; flex-direction:column; align-items:center; width:100%; }\n  .stage { cursor:default; }\n"

page = f'''<title>Landed Logos</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Marcellus&display=swap">
<style>
  /* layout: one quiet column; each logo sits alone on its own surface, with its controls underneath */
  :root {{
    --page:#F3F8FA; --fg:#06364A; --muted:#5C7A88; --line:#D5E4EA; --control:#FFFFFF;
    --surface-light:#FFFFFF; --surface-dark:#062431;
    --display:"Marcellus", Georgia, serif; --text:"Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --page:#041A24; --fg:#EAF6FB; --muted:#8FB4C2; --line:#16485C; --control:#0A2E3E; color-scheme:dark }} }}
  :root[data-theme="dark"] {{ --page:#041A24; --fg:#EAF6FB; --muted:#8FB4C2; --line:#16485C; --control:#0A2E3E; color-scheme:dark }}

  /* the logos' own colours, per surface (these stay fixed whatever the page theme is) */
  .surface, .surface[data-s="light"] {{ --bg:var(--surface-light); --blue:#007CAC; --sky:#5CC6EA; --blue-hi:#0F97CB; --blue-lo:#00668F; --blue-lo2:#00709D; --wisp:#BFEAF8; --cloud:#D6EFF9; }}
  .surface[data-s="dark"] {{ --bg:var(--surface-dark); --blue:#1FA3D6; --sky:#8EDDF7; --blue-hi:#3FB6E6; --blue-lo:#168CC0; --blue-lo2:#1A93C6; --wisp:#E2F7FE; --cloud:#134B63; }}
  .surface.mark, .surface.mark[data-s="light"] {{ --blue-hi:#22B4E6; --blue-lo:#004E73; }}
  .surface.mark[data-s="dark"] {{ --blue-hi:#5CCBF2; --blue-lo:#0B79A8; }}

  * {{ box-sizing:border-box; }}
  body {{ background:var(--page); color:var(--fg); font-family:var(--text); font-size:15px; line-height:1.5; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding-block:36px 56px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); display:flex; flex-direction:column; gap:36px; }}
  header {{ display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px; }}
  h1 {{ font-family:var(--display); font-weight:400; font-size:clamp(28px,5vw,40px); line-height:1.1; margin:0; text-wrap:balance; }}
  .lede {{ margin:6px 0 0; color:var(--muted); max-width:60ch; }}
  section {{ display:flex; flex-direction:column; gap:12px; min-width:0; }}
  .head {{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:8px 16px; }}
  h2 {{ font-family:var(--display); font-weight:400; font-size:22px; margin:0; }}
  .note {{ color:var(--muted); font-size:13.5px; margin:0; }}
  .surface {{ background:var(--bg); border:1px solid var(--line); border-radius:14px; padding:clamp(16px,4vw,40px); display:flex; justify-content:center; overflow:hidden; transition:background .35s ease; min-width:0; }}
  .surface.mark {{ padding-block:clamp(8px,2vw,20px) clamp(28px,5vw,48px); }}
  .surface > div {{ width:100%; display:flex; justify-content:center; min-width:0; }}
  .seg, .btn {{ font:inherit; font-size:13.5px; font-weight:500; color:var(--fg); background:var(--control); border:1px solid var(--line); border-radius:999px; }}
  .btn {{ padding:8px 18px; cursor:pointer; }}
  .btn:hover {{ border-color:var(--muted); }}
  .seg {{ display:inline-flex; padding:3px; gap:2px; }}
  .seg button {{ font:inherit; font-weight:500; color:var(--muted); background:transparent; border:0; border-radius:999px; padding:6px 14px; cursor:pointer; }}
  .seg button[aria-pressed="true"] {{ background:var(--fg); color:var(--page); }}
  .btn:focus-visible, .seg button:focus-visible {{ outline:2px solid #2AA8D8; outline-offset:2px; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }}
</style>

<div class="wrap">
  <header>
    <div>
      <h1>Landed logos</h1>
      <p class="lede">Two animated logos for Landed. Each one plays when the page opens. Use Replay to watch it again, and the switch to see both on a light or dark background.</p>
    </div>
    <div class="seg" role="group" aria-label="Background">
      <button type="button" id="bg-light" aria-pressed="true">Light</button>
      <button type="button" id="bg-dark" aria-pressed="false">Dark</button>
    </div>
  </header>

  <section>
    <div class="head"><h2>Wordmark</h2><p class="note">The plane sweeps round the L, climbs, loops, and lands facing you on top of the last d.</p></div>
    <div class="surface word" data-s="light"><div id="host-w"></div></div>
    <div class="controls"><button type="button" class="btn" id="replay-w">Replay</button></div>
  </section>

  <section>
    <div class="head"><h2>L mark</h2><p class="note">The plane orbits the L; runway markings light up along its foot.</p></div>
    <div class="surface mark" data-s="light"><div id="host-l"></div></div>
    <div class="controls"><button type="button" class="btn" id="replay-l">Replay</button></div>
  </section>
</div>

<template id="tpl-w"><style>
  {host_css}{css_w}</style>{body_w}</template>
<template id="tpl-l"><style>
  {host_css}{css_l}</style>{body_l}</template>

<script>
  // Each logo lives in its own shadow root so the two sets of styles, ids and keyframes can't collide.
  function mount(hostId, tplId, replayId) {{
    const host = document.getElementById(hostId);
    const root = host.attachShadow({{ mode: 'open' }});
    root.appendChild(document.getElementById(tplId).content.cloneNode(true));
    const stage = root.querySelector('.stage');
    document.getElementById(replayId).addEventListener('click', () => {{
      stage.classList.remove('play'); void stage.offsetWidth; stage.classList.add('play');
    }});
  }}
  mount('host-w', 'tpl-w', 'replay-w');
  mount('host-l', 'tpl-l', 'replay-l');

  const light = document.getElementById('bg-light'), dark = document.getElementById('bg-dark');
  function setBg(mode) {{
    document.querySelectorAll('.surface').forEach(s => s.dataset.s = mode);
    light.setAttribute('aria-pressed', mode === 'light'); dark.setAttribute('aria-pressed', mode === 'dark');
  }}
  light.addEventListener('click', () => setBg('light'));
  dark.addEventListener('click', () => setBg('dark'));
</script>
'''
out = os.path.join(W, "landed-logos-share.html")
open(out, "w", encoding="utf-8").write(page)
print("ok", len(page))
