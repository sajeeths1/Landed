# Landed logos

Two animated logos for Landed, built as plain HTML/SVG (no libraries). Open any `.html` file in a browser to watch it; click the logo to replay.

Live preview of both: https://claude.ai/artifact/2oru5vuspX5dQgToCJnfKB

## Files

| File | What it is |
|---|---|
| `landed-wordmark-logo.html` | Full-word logo, animated. The plane circles the L, loops over the word, then turns and lands facing you on the last d. |
| `landed-wordmark-logo.svg` | Full-word logo, static (final frame). Use this for the site header. |
| `landed-logo.html` | L mark, animated. The plane orbits the L; runway markings light up on its foot. |
| `landed-logo.svg` | L mark, static. Use this for a favicon or app icon. |
| `landed-wordmark.svg` | The word "Landed" alone, static, no plane. |
| `landed-logos-share.html` | Both animated logos on one page with Replay and a light/dark switch (the page behind the preview link). |
| `landed-wordmark-20-frames.png`, `landed-wordmark-frames/` | 20 still frames of an earlier version of the full-word animation. |
| `*-frames.png` | Contact sheets used to check the animations. |
| `landed-higgsfield-concept.png` | The original AI concept image the L mark started from. |

## Colours and type

- Deep blue `#007CAC`, light blue (plane, trail) `#5CC6EA`, pale blue (runway dashes) `#BFEAF8`
- Dark background versions: `#1FA3D6`, `#8EDDF7`
- Lettering: Marcellus (Google Fonts), thickened and redrawn as shapes, so no font needs to load

## Changing the logos

The `.html` and `.svg` files are generated; edit the scripts in `source/`, not the outputs. Needs Python 3 with `fonttools`.

From inside `source/`, with `OUT` set to the folder the outputs should go to:

    python build_word.py OUT        # full-word logo (.html + .svg)
    python build_logo.py OUT        # L mark (.html + .svg)
    python make_share.py OUT        # combined page, built from the two .html files above

`letters.py`, `glyph.py` and `wordmark.py` extract the letter shapes from `font/Marcellus.ttf` into the `.json` / `.txt` files the build scripts read; rerun them only to change letter size, spacing or the L's shape.
