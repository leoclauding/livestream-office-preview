# Studio / Office

Interactive Hong Kong Chinese concept preview for a livestream commerce office. The page includes selectable rooms, proposed circulation, and Blender Cycles renders of the full floor and two studio setups.

## Local preview

Start `python3 -m http.server 8000` in this directory and visit its local URL. The site is static and uses relative URLs for GitHub Pages.

## Design source

`design/layout.json` contains the traced structural geometry and proposed partitions, labels, and circulation. The as-built reference photo is not distributed. Door locations, room scale and finishes are schematic and require verification.

Regenerate images with Blender 5.2 or compatible: `blender -b -P design/render.py -- studio-a studio-b axon`.
