# Year Cassette: notes for Claude Code

A fully mechanical, hand-cranked box that replays a year of 58 mm thermal-printer paper. The live page is `index.html` (three.js, published on GitHub Pages). The printable design lives in `cad/`.

## Files
- `cad/year_cassette.py`: the parametric CadQuery model (single source of truth). All dimensions are in the PARAMETERS block at the top.
- `cad/BUILD.md`: what to print, print settings, assembly order, how to make and load the paper roll, and a tuning table.
- `cad/stl/`: print-ready STLs, already in print orientation, no supports. `spool_drive`, `spool` and `spool_cap` are printed twice each.
- `cad/step/`: the same parts as STEP files, plus `year_cassette_assembly.step` (the assembled box) for CAD programs.
- `cad/previews/`: multi-view renders of each part.
- `index.html`: interactive 3D explainer. Its geometry constants mirror the CAD parameters; keep them in sync when the design changes.

## Working on the design
1. Use Python 3.10-3.12 and `pip install cadquery`. The `flowful-ai/cad-skill` Claude Code skill (github.com/flowful-ai/cad-skill) helps with previews and checks.
2. Change values in the PARAMETERS block, then run `python cad/year_cassette.py`.
3. Read the report. Every gear pair must say `meshes`, there must be no `CLASH`, and the script exits non-zero if something collides.
4. Rebuild the zip that `index.html` links to: `cad/year-cassette-stl.zip`, containing every file in `cad/stl/`.

## Key design rules (don't break them)
- Only one spool is ever driven. The swing idler picks the spool from the crank direction, and the other spool must stay free so the changing roll diameters can't jam or tear the paper.
- No part may need supports. Keep overhangs under 45° and flat faces on the bed.
- Everything must fit a 256 mm bed (Bambu A1/P1S) with 5 mm free on each side.
- The printed side of the paper must never rub anything. The guide posts touch only its back.
