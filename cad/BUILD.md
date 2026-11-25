# Year Cassette: build guide

A hand-cranked box that replays one year of thermal-printer paper. One 48 mm square per day, about 19.6 m of paper, rolled up inside a 23 × 8.5 × 9 cm box. Fully mechanical: no electronics, no screws, no glue.

> **Status: prototype v1.** The parts are modelled, checked for collisions and checked that every gear pair meshes, but nobody has printed one yet. Expect to tune one or two fits after the first print. The parameters below are there for exactly that.

## What you need

- A printer with a bed of at least 245 × 90 mm. The tray is 234 mm long. Bambu Lab A1, P1S, X1C and H2D all work; the A1 mini does not.
- About 250 g of PLA.
- The paper: a roll of 58 mm thermal paper printed with one square per day (see "Making the paper roll" below).
- Optional: a 124 × 64 mm piece of thin clear plastic for the window, held with a bit of tape.

## Printed parts

| File | Print | Size (mm) | Notes |
|---|---|---|---|
| `tray.stl` | 1 | 234 × 84 × 82 | The box. Prints open side up. |
| `deck.stl` | 1 | 229 × 79 × 66 | Plate the spools stand on, with the guide posts and brake tongues printed in. |
| `lid.stl` | 1 | 234 × 84 × 6 | Already flipped for printing (top face on the bed). |
| `spool_drive.stl` | **2** | 64 × 64 × 23 | 30-tooth gear plus a hex shaft that drives a spool. |
| `spool.stl` | **2** | 48 × 48 × 63 | Lifts off the hex shaft, so you can swap the year's roll. |
| `spool_cap.stl` | **2** | 48 × 48 × 3 | Top flange. Presses onto the spool's peg. |
| `sun_gear_shaft.stl` | 1 | 34 × 34 × 93 | 15-tooth gear on a tall D-shaft. The crank goes on top. |
| `swing_arm.stl` | 1 | 16 × 48 × 9 | Grips the sun shaft and carries the idler on a snap pin. |
| `idler_gear.stl` | 1 | 44 × 44 × 6 | 20-tooth idler. |
| `crank.stl` | 1 | 54 × 18 × 22 | Press-fits onto the D-shaft. |

All files are already in print orientation, and **none of them need supports**.

**Plates on a 256 mm bed:** (1) tray, (2) deck + lid, (3) everything else.

**Print settings:** PLA, 0.2 mm layers, 3 walls, 15% gyroid infill, no supports.
- **Sun gear shaft:** use 4 walls and a brim. It's tall and thin, and it carries all the torque.
- **Gears:** use 0.16 mm layers if you want smoother meshing (optional).
- **Deck and lid:** a brim helps if your room is cold and the long corners lift.

## How it works

1. The **crank** turns the **sun gear** (centre of the box, 20 mm behind the paper).
2. The **swing arm** grips the sun shaft lightly, so it swings whichever way the sun turns, carrying the **idler gear** with it.
3. **Clockwise:** the idler swings left and meshes with the left spool's gear. The left spool winds paper on and the days go by (play).
4. **Anticlockwise:** the idler swings across (about a third of a turn) and meshes with the right spool's gear, which winds the paper back (rewind).
5. The spool that isn't driven is pulled by the paper. A springy tongue in the deck rubs its bottom flange lightly, so the paper stays taut.

The spools are deliberately never geared to each other: as one roll grows from 15 to 41 mm across, the other shrinks, so their speeds keep changing. Cassette decks solve it the same way.

## Assembly

1. **Tray:** check the three floor pins are clean. Trim any stringing so the gears turn freely.
2. **Spool drives:** drop both onto the left and right floor pins, gear down.
3. **Sun gear:** drop it onto the middle pin (the one nearer the back), gear down.
4. **Idler:** push the idler onto the swing arm's snap pin until it clicks past the barb.
5. **Swing arm:** slide the arm over the sun shaft, idler side down, until it rests on top of the sun gear and the idler sits level with the other gears. It should turn on the shaft with light resistance. Check: turn the sun shaft by hand. The arm should swing until the idler meshes with a spool gear, and then that spool should turn.
6. **Deck:** lower it onto the four corner posts, threading the two hex shafts and the sun shaft through their holes.
7. **Paper:** load the roll (see below).
8. **Spools:** put both spools on the hex shafts and press the caps onto their pegs.
9. **Lid:** press it on, threading the sun shaft through its hole.
10. **Crank:** press it onto the D-flat at the top of the shaft.

## Making the paper roll

- **Squares:** one per day, 48 × 48 mm (384 × 384 dots on a 58 mm, 203 dpi printer), with about 4 mm between days.
- **Rotate each picture 90° before printing.** The paper runs sideways through the window, so a picture printed upright would appear on its side.
- **Joining:** print a week (or a month) at a time and join the strips end to end with a narrow piece of tape on the back.
- **Which end goes where:** Jan 1 is the start of the roll; Dec 31 is the end.
- **Loading:**
  1. Tuck the **Dec 31 end** into the slot of the **right** spool and wind the whole year onto it, **printed side facing out**.
  2. Lead the **Jan 1 end** around the front of both guide posts, so the posts touch only the back of the paper.
  3. Tuck the Jan 1 end into the **left** spool's slot.
- **Paper type:** use long-life (top-coated) thermal paper if you want the year to last. Ordinary receipt paper fades within months, especially in sunlight.

## Tuning (all values in `year_cassette.py`, PARAMETERS section)

| Symptom | Change |
|---|---|
| The arm turns with the shaft and won't stop, so the idler grinds | Lower `arm_grip` (0.25 → 0.15) |
| The arm doesn't swing when you turn the crank | Raise `arm_grip` (0.25 → 0.35) |
| Gears bind or click | Raise `mesh_extra` (0.15 → 0.3) or `backlash` (0.2 → 0.3) |
| Paper goes slack | Raise `brake_bump_h` (1.2 → 1.5) |
| Too stiff to crank | Lower `brake_bump_h` (1.2 → 0.9) |
| Spool wobbles on its hex | Lower the `+ 0.3` clearance in `make_spool` |
| Crank or caps too tight or too loose | Change `press` (0.15) |

To regenerate the STL and STEP files and re-run the collision and mesh checks:

```
pip install cadquery          # Python 3.10-3.12
python year_cassette.py
```

It prints an overlap report: every gear pair should say `meshes`, and there should be no `CLASH`.
