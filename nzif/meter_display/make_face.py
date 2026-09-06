#!/usr/bin/env python3
"""
make_face.py — render the NZIF meter face artwork for the Nextion panel,
and emit the matching geometry header for the firmware.

The artwork and the firmware MUST agree pixel for pixel: if the background's
arc centre and the firmware's needle pivot disagree by even a few pixels, the
needle points off the marks. So this file is the single source of truth for the
geometry, and writes face_geom.h for the C side to include.

Proportions follow the real Model 540 face, measured at 1.75 x 0.75 inches
(2.333:1). Rendered larger than life — at 6.5 px/mm the panel would only give
290 x 124 px at true size, which wastes the glass and hurts legibility.

    python3 make_face.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PNG = os.path.join(HERE, "artwork", "meter_face_480x320.png")
OUT_H = os.path.join(os.path.dirname(HERE), "..", "firmware", "meter_demo", "face_geom.h")

FONT_R = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Regular.otf"
FONT_B = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf"

SS = 4                      # supersample factor, for antialiasing

# ---------------------------------------------------------------- geometry
SCR_W, SCR_H = 480, 320

# The amber face, at the original's 2.333:1, inset slightly so the black panel
# reads as a bezel around it.
FACE_X, FACE_Y = 6, 6
FACE_W = 468
FACE_H = int(round(FACE_W / (1.75 / 0.75)))        # 201

CX = FACE_X + FACE_W / 2.0                          # 240.0
SWEEP_DEG = 27.0
ARC_HALF_W = 206.0                                  # half the arc's chord, px
ARC_R = ARC_HALF_W / math.sin(math.radians(SWEEP_DEG))
ARC_APEX_Y = FACE_Y + 60.0                          # top of the arc
CY = ARC_APEX_Y + ARC_R                             # pivot, well below the glass

TICK_MAJ = 12.0
TICK_MIN = 6.0
S_LABEL_R = ARC_R + 23.0
SWR_LABEL_R = ARC_R - 22.0
S_NAME_R = ARC_R + 46.0
SWR_NAME_R = ARC_R - 46.0

# Needle. The inner end is set by the *edge* of the sweep: at full deflection
# the base must still sit on the amber, not on the black strip below it.
NEEDLE_ROUT = ARC_R                                 # tip reaches the scale line
NEEDLE_RIN = (CY - (FACE_Y + FACE_H - 4)) / math.cos(math.radians(SWEEP_DEG))

READOUT_Y = FACE_Y + FACE_H + 6

# ---------------------------------------------------------------- scale
S9_DBM, DB_PER_S = -73.0, 6.0
ANCH = [(-48, 0.000), (-36, 0.205), (-24, 0.393), (-12, 0.564),
        (0, 0.701), (10, 0.769), (20, 0.897), (30, 1.000)]


def dbm_sweep(dbm):
    r = dbm - S9_DBM
    if r <= ANCH[0][0]:
        return 0.0
    if r >= ANCH[-1][0]:
        return 1.0
    for i in range(len(ANCH) - 1):
        if r <= ANCH[i + 1][0]:
            t = (r - ANCH[i][0]) / (ANCH[i + 1][0] - ANCH[i][0])
            return ANCH[i][1] + t * (ANCH[i + 1][1] - ANCH[i][1])
    return 1.0


def swr_sweep(s):
    return (s - 1.0) / (s + 1.0)          # rho: a moving coil deflects on voltage


def ang(f):
    return -math.pi / 2 + (2 * f - 1) * math.radians(SWEEP_DEG)


def polar(a, r):
    return (CX + r * math.cos(a), CY + r * math.sin(a))


# ---------------------------------------------------------------- painting
INK = (18, 13, 8)
PANEL = (8, 8, 9)

# Lamp-lit amber. The hotspot sits left of centre, as the incandescent lamp
# does behind the real face.
RAMP = [(0.00, (255, 226, 158)), (0.20, (252, 199, 112)), (0.46, (238, 168,  70)),
        (0.74, (208, 132,  44)), (1.00, (168,  96,  28))]
HOT = (0.34, 0.52)          # in face-relative coordinates


def amber_field(w, h):
    """Radial lamp gradient as an (h, w, 3) uint8 array."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hx, hy = HOT[0] * w, HOT[1] * h
    # Elliptical falloff: the face is much wider than tall, so a circular
    # gradient would band vertically long before it reached the ends.
    d = np.sqrt(((xx - hx) / (w * 0.62)) ** 2 + ((yy - hy) / (h * 1.05)) ** 2)
    d = np.clip(d / 0.80, 0.0, 1.0)

    stops = np.array([s for s, _ in RAMP], dtype=np.float32)
    cols = np.array([c for _, c in RAMP], dtype=np.float32)
    out = np.zeros((h, w, 3), dtype=np.float32)
    for ch in range(3):
        out[:, :, ch] = np.interp(d, stops, cols[:, ch])
    return out


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return m


def rot_text(img, cx, cy, text, font, rot_rad, fill):
    """Draw `text` centred on (cx, cy), rotated. PIL cannot rotate text in
    place, so each label is rendered to its own tile and pasted."""
    tmp = Image.new("RGBA", (10, 10))
    box = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    pad = max(tw, th)
    tile = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad - box[0], pad - box[1]), text, font=font, fill=fill)
    tile = tile.rotate(-math.degrees(rot_rad), resample=Image.BICUBIC, expand=True)
    img.alpha_composite(tile, (int(round(cx - tile.width / 2)),
                               int(round(cy - tile.height / 2))))


def main():
    W, H = SCR_W * SS, SCR_H * SS

    # --- panel ground, then the lit face inset into it
    img = Image.new("RGBA", (W, H), PANEL + (255,))

    fw, fh = FACE_W * SS, FACE_H * SS
    field = amber_field(fw, fh)
    face = Image.fromarray(field.astype(np.uint8), "RGB").convert("RGBA")
    face.putalpha(rounded_mask(fw, fh, 5 * SS))
    img.alpha_composite(face, (FACE_X * SS, FACE_Y * SS))

    d = ImageDraw.Draw(img)

    def line(p0, p1, width, fill=INK):
        d.line([p0[0] * SS, p0[1] * SS, p1[0] * SS, p1[1] * SS],
               fill=fill + (255,), width=int(round(width * SS)))

    # --- bezel: a hairline shadow just inside the face edge gives the glass
    #     a sense of depth without a heavy border.
    d.rounded_rectangle([FACE_X * SS, FACE_Y * SS,
                         (FACE_X + FACE_W) * SS - 1, (FACE_Y + FACE_H) * SS - 1],
                        radius=5 * SS, outline=(120, 74, 22, 255), width=max(1, SS // 2))

    # --- scale arc
    N = 400
    for i in range(N):
        line(polar(ang(i / N), ARC_R), polar(ang((i + 1) / N), ARC_R), 1.4)

    # --- S-unit ticks: every S-unit, plus the over-9 decade marks
    for s in range(1, 10):
        a = ang(dbm_sweep(S9_DBM + (s - 9) * DB_PER_S))
        line(polar(a, ARC_R), polar(a, ARC_R + TICK_MAJ), 1.6)
    for over in (5, 10, 15, 20, 25, 30):
        a = ang(dbm_sweep(S9_DBM + over))
        major = over % 10 == 0
        line(polar(a, ARC_R), polar(a, ARC_R + (TICK_MAJ if major else TICK_MIN)),
             1.6 if major else 1.1)

    # --- SWR ticks, inside the arc
    for v, major in ((1.0, True), (1.5, False), (2.0, True), (2.5, False),
                     (3.0, True), (4.0, False), (5.0, True)):
        a = ang(swr_sweep(v))
        line(polar(a, ARC_R - (TICK_MAJ if major else TICK_MIN)), polar(a, ARC_R),
             1.6 if major else 1.1)

    f_num = ImageFont.truetype(FONT_R, int(round(20 * SS)))
    f_swr = ImageFont.truetype(FONT_R, int(round(17 * SS)))
    f_name = ImageFont.truetype(FONT_R, int(round(15 * SS)))

    # --- numerals, set radially as on the original face
    for lbl, db in (("3", -36), ("5", -24), ("7", -12), ("9", 0)):
        a = ang(dbm_sweep(S9_DBM + db))
        x, y = polar(a, S_LABEL_R)
        rot_text(img, x * SS, y * SS, lbl, f_num, a + math.pi / 2, INK + (255,))
    for lbl, over in (("10", 10), ("20", 20), ("30", 30)):
        a = ang(dbm_sweep(S9_DBM + over))
        x, y = polar(a, S_LABEL_R)
        rot_text(img, x * SS, y * SS, lbl, f_num, a + math.pi / 2, INK + (255,))

    for lbl, v in (("1", 1.0), ("2", 2.0), ("3", 3.0), ("5", 5.0)):
        a = ang(swr_sweep(v))
        x, y = polar(a, SWR_LABEL_R)
        rot_text(img, x * SS, y * SS, lbl, f_swr, a + math.pi / 2, INK + (255,))

    # --- silkscreened scale names
    a = ang(0.085)
    x, y = polar(a, S_NAME_R)
    rot_text(img, x * SS, y * SS, "S UNITS", f_name, a + math.pi / 2, INK + (255,))

    a = ang(0.945)
    x, y = polar(a, SWR_NAME_R)
    rot_text(img, x * SS, y * SS, "SWR", f_name, a + math.pi / 2, INK + (255,))

    # --- readout strip separator
    d.line([8 * SS, (READOUT_Y - 3) * SS, (SCR_W - 8) * SS, (READOUT_Y - 3) * SS],
           fill=(72, 46, 16, 255), width=max(1, SS // 2))

    out = img.convert("RGB").resize((SCR_W, SCR_H), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    out.save(OUT_PNG)
    print("wrote %s  (%d x %d)" % (OUT_PNG, out.width, out.height))

    write_header()


def write_header():
    hdr = '''/*
 * face_geom.h — GENERATED by nzif/meter_display/make_face.py. Do not edit.
 *
 * The background artwork and this firmware must agree pixel for pixel: the
 * needle pivots about (FG_CX, FG_CY), and the arc drawn into the PNG is
 * centred on exactly the same point. Regenerate both together.
 *
 * Face proportions follow the real Model 540 at 1.75 x 0.75 inches.
 */
#ifndef NZIF_FACE_GEOM_H
#define NZIF_FACE_GEOM_H

#define FG_SCR_W        %d
#define FG_SCR_H        %d

#define FG_FACE_X       %d
#define FG_FACE_Y       %d
#define FG_FACE_W       %d
#define FG_FACE_H       %d

#define FG_CX           %.4ff
#define FG_CY           %.4ff
#define FG_ARC_R        %.4ff
#define FG_SWEEP_DEG    %.4ff

#define FG_NEEDLE_RIN   %.4ff
#define FG_NEEDLE_ROUT  %.4ff

#define FG_READOUT_Y    %d

#endif /* NZIF_FACE_GEOM_H */
''' % (SCR_W, SCR_H, FACE_X, FACE_Y, FACE_W, FACE_H,
       CX, CY, ARC_R, SWEEP_DEG, NEEDLE_RIN, NEEDLE_ROUT, READOUT_Y)
    path = os.path.normpath(OUT_H)
    with open(path, "w") as fh:
        fh.write(hdr)
    print("wrote %s" % path)
    print("  face   %d x %d  (%.3f:1)" % (FACE_W, FACE_H, FACE_W / FACE_H))
    print("  pivot  (%.1f, %.1f)  R=%.1f  sweep +/-%.0f deg" % (CX, CY, ARC_R, SWEEP_DEG))
    print("  needle r %.1f .. %.1f  (%.1f px visible)" % (NEEDLE_RIN, NEEDLE_ROUT,
                                                          NEEDLE_ROUT - NEEDLE_RIN))


if __name__ == "__main__":
    main()
