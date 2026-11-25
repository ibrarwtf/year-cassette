"""Year Cassette: a hand-cranked, fully mechanical viewer for one year of 58 mm thermal-printer paper.

One centre crank drives a sun gear. A swing arm (friction-coupled to the sun shaft) carries an idler gear
that engages the LEFT spool gear when the crank turns clockwise (play) and the RIGHT spool gear when it
turns anticlockwise (rewind). The undriven spool is pulled by the paper against a light printed brake.

Coordinates (assembled): X = box length, Y = depth (+Y is the FRONT, where the window is), Z up, origin at the
centre of the floor's underside. Every part is exported in its PRINT orientation (flat face on the bed).

Run:  python year_cassette.py            -> writes stl/*.stl, step/*.step and checks the assembly for collisions
"""
import math, os, sys
import cadquery as cq

# ============================================================
# PARAMETERS (mm)
# ============================================================
# Paper
paper_w = 58.0           # thermal roll width
paper_clear = 0.6        # extra height between spool flanges

# Box
box_l, box_w = 234.0, 84.0
wall = 2.4
floor_t = 3.0
wall_top = 82.0          # top of the tray walls (lid sits here)
lid_t = 3.0
lid_lip_depth = 3.0
lid_lip_t = 1.6
corner_r = 4.0

# Layout
spool_x = 80.0           # spool axes at x = +-80, y = 0
sun_y = -20.0            # sun/crank axis at (0, -20): behind the paper
post_x, post_y = 64.0, 22.0   # guide posts (paper passes in front of them)
post_d = 6.0

# Gears (module 2, 20 deg pressure angle, chunky teeth that print well)
module = 2.0
z_sun, z_idler, z_spool = 15, 20, 30
gear_t = 6.0
backlash = 0.2           # tooth thinning at the pitch circle (total)
mesh_extra = 0.15        # added to the arm length so printed gears do not bind

# Vertical stack
collar_h = 0.8           # gears ride on small collars on the floor pins
gear_z0 = floor_t + collar_h          # 3.8
gear_z1 = gear_z0 + gear_t            # 9.8
arm_z0 = gear_z1 + 0.2                # swing arm sits just above the gears
arm_t = 2.0
deck_z0, deck_t = 14.0, 3.0           # deck plate the spools stand on
deck_z1 = deck_z0 + deck_t            # 17.0

# Shafts and fits
pin_d = 6.0              # floor pins
pin_clear = 0.5          # bore = pin + clearance
hex_af = 11.0            # spool drive shaft (hex, across flats)
hex_top = 27.0           # top of the drive shaft
spool_gap = 0.6          # spool bottom sits this far above the deck
sun_shaft_d = 10.0
sun_shaft_top = wall_top + lid_t + 12.0   # 97
d_flat = 1.2             # D-flat depth on the top of the sun shaft
hole_clear = 0.4         # shaft holes in deck/lid
arm_grip = 0.25          # swing-arm hub interference on the sun shaft (the friction)
idler_bore = 5.0
idler_pin_d = 4.6
press = 0.15             # press-fit allowance

# Spool
core_d = 15.0
flange_d = 48.0
flange_t = 1.6
peg_d = 10.0             # top peg the cap presses onto
paper_slot_w = 1.0       # slot in the core to tuck the paper end

# Brake (springy tongue in the deck pressing up on each spool's bottom flange)
brake_bump_h = 1.2
brake_tongue_t = 1.2

# Window (open at the top: the lid closes it, so no long bridge to print)
win_w = 54.0            # shows one 48 mm day at a time

# Finish (small touches: chamfered lid edge, debossed label, dot recess, chamfered crank knob)
label_text = "YEAR CASSETTE"
label_size = 4.5
label_depth = 0.4
label_x, label_y = -96.0, 30.0   # label starts near the front-left corner of the lid (text runs toward +x)
dot_d = 3.0
label_chamfer = 0.8

# Crank
crank_arm = 40.0
crank_hub_d = 18.0
crank_hub_h = 10.0
crank_bar_t = 5.0
handle_d, handle_h = 9.0, 22.0

# Derived
r_sun, r_idler, r_spool = module * z_sun / 2, module * z_idler / 2, module * z_spool / 2
arm_len = r_sun + r_idler + mesh_extra
spool_z0 = deck_z1 + spool_gap                  # 17.6
core_z0 = spool_z0 + flange_t                   # 19.2
core_z1 = core_z0 + paper_w + paper_clear       # 77.8
paper_mid = core_z0 + (paper_w + paper_clear) / 2
cap_collar_h = 1.6
peg_top = core_z1 + flange_t + cap_collar_h     # 81.0 (< wall_top: clears the lid)
inner_l, inner_w = box_l - 2 * wall, box_w - 2 * wall

TOL = dict(tolerance=0.01, angularTolerance=0.1)
HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# HELPERS
# ============================================================
def pol(r, a):
    return (r * math.cos(a), r * math.sin(a))

def gear_points(z, m=module, pa_deg=20.0, bl=backlash, n=10):
    """Involute spur gear outline (counter-clockwise)."""
    rp = m * z / 2; pa = math.radians(pa_deg); rb = rp * math.cos(pa); ra = rp + m; rf = rp - 1.25 * m
    inv = lambda a: math.tan(a) - a
    psi_p = (math.pi * m / 2 - bl) / (2 * rp)
    psi = lambda r: psi_p + inv(pa) - inv(math.acos(min(1.0, rb / r)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * k / n for k in range(n + 1)]
    pts = []
    for i in range(z):
        th = 2 * math.pi * i / z
        if rf < rb: pts.append(pol(rf, th - psi(rb)))
        pts += [pol(r, th - psi(r)) for r in rs]
        pts.append(pol(ra, th))
        pts += [pol(r, th + psi(r)) for r in reversed(rs)]
        if rf < rb: pts.append(pol(rf, th + psi(rb)))
    return pts

def gear(z, t=gear_t):
    return cq.Workplane("XY").polyline(gear_points(z)).close().extrude(t)

def cyl(d, h, x=0, y=0, z0=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)

def hexagon(af, h, x=0, y=0, z0=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).polygon(6, af / math.cos(math.radians(30))).extrude(h)

def d_shaft(d, h, flat, z0=0, x=0, y=0):
    c = cyl(d, h, x, y, z0)
    cut = cq.Workplane("XY").workplane(offset=z0).center(x + d / 2 - flat + d / 2, y).rect(d, d * 2).extrude(h)
    return c.cut(cut)

def rbox(l, w, h, r, z0=0, x=0, y=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).rect(l, w).extrude(h).edges("|Z").fillet(r)

# ============================================================
# PARTS (assembled position)
# ============================================================
def make_tray():
    outer = rbox(box_l, box_w, wall_top, corner_r)
    inner = rbox(inner_l, inner_w, wall_top, corner_r - wall + 0.01, z0=floor_t)
    t = outer.cut(inner)
    # window: open from the paper bottom up through the top of the front wall (the lid closes it)
    win_z0 = core_z0 - 1.5
    t = t.cut(cq.Workplane("XY").workplane(offset=win_z0).center(0, box_w / 2 - wall / 2).rect(win_w, wall * 3).extrude(wall_top))
    # floor pins with collars: spools and sun
    for x, y, h in [(-spool_x, 0, hex_top - 1.0), (spool_x, 0, hex_top - 1.0), (0, sun_y, gear_z0 + 5.2)]:
        t = t.union(cyl(pin_d + 4, collar_h, x, y, floor_t)).union(cyl(pin_d, h - floor_t, x, y, floor_t))
    # deck support posts in the four corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            t = t.union(rbox(8, 8, deck_z0 - floor_t, 1.0, floor_t, sx * (inner_l / 2 - 4), sy * (inner_w / 2 - 4)))
    return t

def make_deck():
    d = rbox(inner_l - 0.6, inner_w - 0.6, deck_t, corner_r - wall, deck_z0)
    for x in (-spool_x, spool_x):
        d = d.cut(cyl(hex_af / math.cos(math.radians(30)) + 0.9, deck_t + 2, x, 0, deck_z0 - 1))
    d = d.cut(cyl(sun_shaft_d + hole_clear * 2, deck_t + 2, 0, sun_y, deck_z0 - 1))
    # corner notches clear the support posts' fillets; finger holes to lift the deck out
    for sx in (-1, 1):
        d = d.cut(cyl(14, deck_t + 2, sx * 40, -24, deck_z0 - 1))
    # guide posts
    for sx in (-1, 1):
        d = d.union(cyl(post_d, core_z1 + 2 - deck_z1, sx * post_x, post_y, deck_z1))
    # brake tongues: U-slot leaves a tongue, thinned from below, with a bump under the spool flange
    for sx in (-1, 1):
        bx, by = sx * spool_x, -21.0
        tongue_l, tongue_w, slot = 18.0, 5.0, 1.2
        root_x = bx - sx * (tongue_l - 3)
        cx = (root_x + bx + sx * 3) / 2
        u = (cq.Workplane("XY").workplane(offset=deck_z0 - 1).center(cx, by).rect(tongue_l + slot, tongue_w + 2 * slot).extrude(deck_t + 2)
             .cut(cq.Workplane("XY").workplane(offset=deck_z0 - 1).center(cx - sx * slot / 2, by).rect(tongue_l, tongue_w).extrude(deck_t + 2)))
        d = d.cut(u)
        d = d.cut(cq.Workplane("XY").workplane(offset=deck_z0 - 0.01).center(cx - sx * slot / 2, by).rect(tongue_l - 2, tongue_w).extrude(deck_t - brake_tongue_t + 0.01))
        d = d.union(cyl(4.0, brake_bump_h, bx, by, deck_z1))
    return d

def make_lid():
    p = rbox(box_l, box_w, lid_t, corner_r, wall_top).faces(">Z").edges().chamfer(label_chamfer)
    # debossed label + a dot recess (fill it with paint or a dab of orange), reading from the front
    label = (cq.Workplane("XY").text(label_text, label_size, label_depth + 0.01, kind="bold", halign="left", valign="center")
             .rotate((0, 0, 0), (0, 0, 1), 180).translate((-label_x, label_y, wall_top + lid_t - label_depth)))
    p = p.cut(label).cut(cyl(dot_d, label_depth + 0.01, -label_x + 6, label_y, wall_top + lid_t - label_depth))
    lip_o = rbox(inner_l - 0.4, inner_w - 0.4, lid_lip_depth, corner_r - wall, wall_top - lid_lip_depth)
    lip_i = rbox(inner_l - 0.4 - 2 * lid_lip_t, inner_w - 0.4 - 2 * lid_lip_t, lid_lip_depth, 0.8, wall_top - lid_lip_depth)
    p = p.union(lip_o.cut(lip_i))
    # the lip must not hang into the window opening at the front
    p = p.cut(cq.Workplane("XY").workplane(offset=wall_top - lid_lip_depth - 0.1).center(0, inner_w / 2 - lid_lip_t).rect(win_w, lid_lip_t * 4).extrude(lid_lip_depth + 0.1))
    return p.cut(cyl(sun_shaft_d + hole_clear * 2, lid_t + 2, 0, sun_y, wall_top - 1))

def make_spool_drive(x):
    g = gear(z_spool).translate((x, 0, gear_z0))
    g = g.union(hexagon(hex_af, hex_top - gear_z1, x, 0, gear_z1))
    return g.cut(cyl(pin_d + pin_clear, hex_top + 5, x, 0, 0))

def make_spool(x):
    s = cyl(flange_d, flange_t, x, 0, spool_z0).union(cyl(core_d, core_z1 - core_z0, x, 0, core_z0))
    s = s.union(cyl(peg_d, peg_top - core_z1, x, 0, core_z1))
    s = s.cut(hexagon(hex_af + 0.3, hex_top - spool_z0, x, 0, spool_z0 - 0.01))     # sits on the drive shaft
    slot = cq.Workplane("XY").workplane(offset=core_z0 + 4).center(x + core_d / 4, 0).rect(core_d / 2 + 0.2, paper_slot_w).extrude(paper_w - 8)
    return s.cut(slot)

def make_cap(x):
    c = cyl(flange_d, flange_t, x, 0, core_z1).union(cyl(peg_d + 6, cap_collar_h, x, 0, core_z1 + flange_t))
    return c.cut(cyl(peg_d + press, 10, x, 0, core_z1 - 1))

def make_sun():
    g = gear(z_sun).translate((0, sun_y, gear_z0))
    g = g.union(cyl(sun_shaft_d, sun_shaft_top - gear_z1, 0, sun_y, gear_z1))
    flat_cut = cq.Workplane("XY").workplane(offset=wall_top + lid_t).center(sun_shaft_d / 2 - d_flat + sun_shaft_d / 2, sun_y).rect(sun_shaft_d, sun_shaft_d * 2).extrude(20)
    g = g.cut(flat_cut)
    return g.cut(cyl(pin_d + pin_clear, gear_z0 + 5.5 - floor_t, 0, sun_y, floor_t - 0.01))

def make_arm(angle_deg=90.0):
    """Swing arm at the given angle (deg, CCW from +X seen from above), assembled on the sun axis."""
    a = cq.Workplane("XY").workplane(offset=arm_z0).circle(8.0).extrude(arm_t)
    a = a.union(cq.Workplane("XY").workplane(offset=arm_z0).center(arm_len / 2, 0).rect(arm_len, 7.0).extrude(arm_t))
    a = a.union(cq.Workplane("XY").workplane(offset=arm_z0).center(arm_len, 0).circle(5.0).extrude(arm_t))
    a = a.cut(cq.Workplane("XY").workplane(offset=arm_z0 - 1).circle((sun_shaft_d - arm_grip) / 2).extrude(arm_t + 2))
    a = a.cut(cq.Workplane("XY").workplane(offset=arm_z0 - 1).center(-5, 0).rect(8, 1.0).extrude(arm_t + 2))   # split = spring grip
    # snap pin down through the idler
    pin_z0 = gear_z0 - 0.4
    pin = cq.Workplane("XY").workplane(offset=pin_z0).center(arm_len, 0).circle(idler_pin_d / 2).extrude(arm_z0 - pin_z0)
    barb = (cq.Workplane("XY").workplane(offset=pin_z0).center(arm_len, 0).circle(idler_bore / 2 + 0.35)
            .workplane(offset=0.8).circle(idler_pin_d / 2 - 0.2).loft())
    pin = pin.union(barb).cut(cq.Workplane("XY").workplane(offset=pin_z0 - 0.1).center(arm_len, 0).rect(1.2, 8).extrude(4.0))
    a = a.union(pin)
    return a.rotate((0, 0, 0), (0, 0, 1), angle_deg).translate((0, sun_y, 0))

def make_idler(angle_deg=90.0):
    g = gear(z_idler).cut(cyl(idler_bore, gear_t + 2, 0, 0, -1)).translate((arm_len, 0, gear_z0))
    return g.rotate((0, 0, 0), (0, 0, 1), angle_deg).translate((0, sun_y, 0))

def make_crank():
    hub_z0 = wall_top + lid_t + 0.5
    c = cq.Workplane("XY").workplane(offset=hub_z0).center(crank_arm / 2, 0).rect(crank_arm, 9.0).extrude(crank_bar_t)
    c = c.union(cyl(crank_hub_d, crank_hub_h, 0, 0, hub_z0)).union(cyl(handle_d, handle_h, crank_arm, 0, hub_z0).faces(">Z").edges().chamfer(1.0))
    hole = d_shaft(sun_shaft_d + press, crank_hub_h + 2, d_flat - press, hub_z0 - 1)
    return c.cut(hole).translate((0, sun_y, 0))

# ============================================================
# ENGAGEMENT GEOMETRY + ASSEMBLY CHECKS
# ============================================================
def engage_angles():
    """Arm angles (deg) where the idler meshes with the right / left spool gear, swinging via the front."""
    E = r_idler + r_spool + mesh_extra
    dx, dy = spool_x, -sun_y
    dd = math.hypot(dx, dy)
    a = (arm_len ** 2 - E ** 2 + dd ** 2) / (2 * dd); h = math.sqrt(arm_len ** 2 - a ** 2)
    ux, uy = dx / dd, dy / dd
    px, py = a * ux - h * uy, a * uy + h * ux
    right = math.degrees(math.atan2(py, px))
    return right, 180 - right

def vol(shape):
    try:
        return shape.val().Volume()
    except Exception:
        return 0.0

def clash(a, b):
    try:
        return vol(a.intersect(b))
    except Exception:
        return -1.0

PRINT_FLIP = {"lid", "swing_arm"}          # printed upside down

if __name__ == "__main__":
    right, left = engage_angles()
    print(f"idler engages right spool at {right:.1f} deg, left at {left:.1f} deg, swing {left - right:.1f} deg")

    parts = {
        "tray": make_tray(), "deck": make_deck(), "lid": make_lid(),
        "spool_drive_left": make_spool_drive(-spool_x), "spool_drive_right": make_spool_drive(spool_x),
        "spool_left": make_spool(-spool_x), "spool_right": make_spool(spool_x),
        "spool_cap_left": make_cap(-spool_x), "spool_cap_right": make_cap(spool_x),
        "sun_gear_shaft": make_sun(), "swing_arm": make_arm(90), "idler_gear": make_idler(90), "crank": make_crank(),
    }

    # ---- collision checks in the assembled state (volume of overlap, mm^3) ----
    # (brake bumps pressing 0.6 mm into the spool flanges is intended, so spool x deck is not listed)
    checks = [("tray", "spool_drive_left"), ("tray", "spool_drive_right"), ("tray", "sun_gear_shaft"), ("tray", "deck"),
              ("tray", "lid"), ("deck", "spool_drive_left"), ("deck", "sun_gear_shaft"), ("deck", "swing_arm"),
              ("deck", "idler_gear"), ("spool_left", "spool_drive_left"), ("spool_cap_left", "spool_left"),
              ("lid", "spool_cap_left"), ("lid", "sun_gear_shaft"), ("idler_gear", "tray"),
              ("swing_arm", "tray"), ("swing_arm", "spool_drive_left"), ("crank", "lid"), ("sun_gear_shaft", "spool_drive_left")]
    bad = []
    for a, b in checks:
        v = clash(parts[a], parts[b])
        flag = "" if v < 1.0 else "  <-- CLASH"
        if v >= 1.0: bad.append((a, b, v))
        print(f"  {a:18s} x {b:18s}: {v:8.2f}{flag}")
    # gear meshes: spin the idler about its own axis through one tooth pitch. A real mesh has a phase with
    # (almost) no overlap (teeth interleave) and phases with a lot of overlap (teeth reach into each other).
    def idler_spun(ang, spin):
        g = gear(z_idler).cut(cyl(idler_bore, gear_t + 2, 0, 0, -1)).rotate((0, 0, 0), (0, 0, 1), spin).translate((arm_len, 0, gear_z0))
        return g.rotate((0, 0, 0), (0, 0, 1), ang).translate((0, sun_y, 0))
    pitch = 360.0 / z_idler
    for label, ang, other in [("idler->sun   (arm forward)", 90.0, parts["sun_gear_shaft"]),
                              ("idler->right spool (rewind)", right, parts["spool_drive_right"]),
                              ("idler->left spool (play)", left, parts["spool_drive_left"])]:
        vols = [clash(idler_spun(ang, pitch * k / 12), other) for k in range(12)]
        ok = min(vols) < 1.0 and max(vols) > 20.0
        print(f"  {label:28s}: overlap min {min(vols):6.2f}  max {max(vols):6.2f}  -> {'meshes' if ok else 'PROBLEM'}")
        if not ok: bad.append((label, min(vols), max(vols)))
        print(f"  idler at {ang:6.1f} deg x tray: {clash(make_idler(ang), parts['tray']):6.2f}")
    # brake bumps intentionally press into the spool flanges (that is the drag); report, do not fail
    if bad:
        print("COLLISIONS:", bad)

    # ---- export in print orientation ----
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True); os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    for name, shp in parts.items():
        if name.endswith("_right"):                   # left and right parts are identical: export once, print twice
            continue
        name = name.replace("_left", "")
        bb = shp.val().BoundingBox()
        s = shp.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))
        if name in PRINT_FLIP:
            s = s.rotate((0, 0, 0), (1, 0, 0), 180)
            bb2 = s.val().BoundingBox(); s = s.translate((0, 0, -bb2.zmin))
        if name == "swing_arm":                       # lay the arm along X
            pass
        cq.exporters.export(s, os.path.join(HERE, "stl", f"{name}.stl"), **TOL)
        cq.exporters.export(s, os.path.join(HERE, "step", f"{name}.step"))
        b = s.val().BoundingBox()
        print(f"exported {name:18s} {b.xlen:6.1f} x {b.ylen:6.1f} x {b.zlen:6.1f} mm")
    # whole assembly (for viewing in a CAD program)
    asm = cq.Assembly()
    for name, shp in parts.items():
        asm.add(shp, name=name)
    asm.save(os.path.join(HERE, "step", "year_cassette_assembly.step"))
    print("exported assembly STEP")
    sys.exit(1 if bad else 0)
