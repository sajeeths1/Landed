"""Copy the Landed logos from docs/brand into public/brand for the website.

The animated .html logos are turned into self-contained animated .svg files:
same drawing, same CSS animation, no page script. A browser plays them in a
plain <img> tag, once, each time the image loads.

Run it again after the logos in docs/brand change. From the frontend folder:

    python scripts/make_brand_svgs.py
"""
import re
import shutil
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent
BRAND = FRONTEND.parent / "docs" / "brand"
OUT = FRONTEND / "public" / "brand"

# Page-only CSS rules (layout, buttons, captions, dark switch) that mean nothing inside the SVG.
PAGE_RULES = re.compile(
    r"^\s*(:root\[data-theme=\"dark\"\]|\*|html,\s*body|body|\.stage|\.word[^{]*|\.tag|\.bar|button[^{]*|\.wm|\.play ~ [^{]*)\s*\{[^}]*\}\s*$",
    re.M,
)

# People who ask their computer for less motion see the finished logo straight away.
REDUCED_MOTION = (
    "@media (prefers-reduced-motion: reduce) {"
    " .play * { animation-duration:1ms !important; animation-delay:0s !important;"
    " animation-iteration-count:1 !important; } }"
)


# Dark versions sit on the "night" blue used by the sidebar and landing page (Tailwind brand-950).
NIGHT = "#062431"


def animated_svg(html_file: Path, dark: bool = False) -> str:
    html = html_file.read_text(encoding="utf-8")
    css = html[html.index("<style>") + 7 : html.index("</style>")]
    if dark:
        # Use the logo's own dark-theme colours instead of the light ones.
        dark_vars = re.search(r':root\[data-theme="dark"\]\s*\{([^}]*)\}', css).group(1)
        css = re.sub(r":root\s*\{[^}]*\}", ":root {" + dark_vars.replace("--bg:#062431", "--bg:" + NIGHT) + "}", css, count=1)
    css = PAGE_RULES.sub("", css)
    css = css.replace(":root {", "svg {", 1)  # the colour variables live on the <svg> itself
    css = "\n".join(line for line in css.splitlines() if line.strip())
    start = html.index("<svg", html.index('id="stage"'))
    end = html.index("</svg>", start) + len("</svg>")
    svg = html[start:end]
    open_end = svg.index(">")
    head = svg[:open_end].replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" class="play" ', 1)
    return f"{head}>\n<style>\n{css}\n{REDUCED_MOTION}\n</style>{svg[open_end + 1:]}\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "landed-logo-animated.svg").write_text(animated_svg(BRAND / "landed-logo.html"), encoding="utf-8", newline="\n")
    (OUT / "landed-wordmark-animated.svg").write_text(animated_svg(BRAND / "landed-wordmark-logo.html"), encoding="utf-8", newline="\n")
    (OUT / "landed-wordmark-animated-dark.svg").write_text(animated_svg(BRAND / "landed-wordmark-logo.html", dark=True), encoding="utf-8", newline="\n")
    for name in ("landed-logo.svg", "landed-wordmark-logo.svg", "landed-wordmark.svg"):
        shutil.copyfile(BRAND / name, OUT / name)
    # Browser-tab icon: the L mark, cropped closer so it stays readable at 16 pixels.
    icon = (BRAND / "landed-logo.svg").read_text(encoding="utf-8").replace('viewBox="0 0 512 512"', 'viewBox="71 75 370 370"', 1)
    (FRONTEND / "app" / "icon.svg").write_text(icon, encoding="utf-8", newline="\n")
    (OUT / "landed-icon.svg").write_text(icon, encoding="utf-8", newline="\n")  # same crop, for small logos in the app
    print(f"Wrote 7 logo files to {OUT} and the tab icon to app/icon.svg")


if __name__ == "__main__":
    main()
