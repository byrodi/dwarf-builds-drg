"""Loadout scan: DB_Scan (the layer) and DB_ScanItem (one floating item).

While the laser pointer rests on a teammate, their primary and secondary weapon (with overclock), grenade and
perks float around them, tied to them by thin lines. The pointer is the game's scanner (it already names what it
points at), so this reads as one more thing it can scan.

How it feels (the constants below):
  - Lock: the pointer must stay on a dwarf for DWELL, so sweeping across the team shows nothing. Then a hexagon
    closes in on the dwarf, a second one pulses outward once, and the items fly out of the dwarf one after
    another (DELAY apart), each on its own spring: they overshoot a little and settle.
  - Hold: the items are placed around the dwarf's place on screen, not on the screen itself. They follow the
    dwarf through their springs, so they trail when the dwarf runs or jumps and catch up; the small ones are on
    softer springs than the weapons, which reads as depth. Each bobs slowly with its own phase. A line runs from
    every item to the hexagon on the dwarf. Size and distance follow how big the dwarf is on screen (Unit, the
    pixels of one metre at the dwarf), so it holds together from 2 to 40 m and with any FOV.
  - Slip: when the pointer leaves the dwarf, the scan dims and stays for GRACE (a running dwarf slips off the
    beam all the time). Back on the dwarf in that time: full again. Else the items fall back into the dwarf and
    fade. Pointing at another dwarf for DWELL moves the scan there at once.
  - Colour: the hexagon, the lines, the pictures and the rules take the dwarf's class colour; an overclock keeps
    its type colour. Items flicker for a moment when they appear, like a hologram switching on.
What is shown: the two weapons with their overclocks (what differs between two dwarves of a class), the grenade
and the perks when they are known. Traversal tool, support tool and armor are one per class: not shown. The
full build is in the window (B).

Cost: DB_Scan is collapsed (no Tick) until the pointer is out. With the pointer out and no dwarf under it a Tick
reads the pointer's own hit result (ALaserPointerItem.LookAtHit, which the game fills for its display anyway: no
trace of our own) and stops. Only during a scan it moves widgets, by render transform only (no layout pass).
The build is read once per lock (DB_Data.CodeOf, DecodeSlot, ItemVisual, OverclockTip, PerksOf).
BPForge has no locals, so a function's working values are member variables (T...); a pure node is evaluated
again by every node that reads it, so values used more than once are stored first.

Dev build (common.DEV, Tools/dwarfbuilds_build.py --dev): to test alone, the scan also takes any other pawn
under the pointer (a bot of the Beard Bots mod, an enemy) and shows a sample build on it, the next of DEV_CODES
on every lock. Such a pawn is no player: it has no class, no loadout and no player state, so there is nothing
real to show. None of this is in a release build.
"""
from dwarfbuilds.common import (ACTOR, CARBON, DATA, DEV, GS, ITEMID, KML, KSTR, LASERPOINTER, LINEAR, OVERCLOCK, PERK,
                                PERKASSET, PLAYERCHAR, RIFT, SCAN, SCANITEM, TEXTURE, UMG, USERWIDGET, WHITE, border,
                                box, cls, image, oslot, hslot, t, text, vslot, w)
from dwarfbuilds.widgets import DIM, G, deco, hbox, overlay, props, unref, vbox

VEC2 = "/Script/CoreUObject.Vector2D"
PAWN = "/Script/Engine.Pawn"
TARGET = ACTOR if DEV else PLAYERCHAR   # what can be scanned (see the dev build note above)
# Dev build: sample builds, one per class (Scout and Driller: Web/tests/code_vectors.json).
DEV_CODES = [
    "DB1:S:2-21221-3:1-12213-1:1-2122-0:1-212-0:1-3113-0:2--0:1-12-0:3.7.13.17.22.36",
    "DB1:D:1-21321-4:2-12213-0:1-3112-0:1-2121-0:1-2112-0:3--0:1-12-0:2.3.5.4.8.34",
    "DB1:E:2-21123-2:1-21322-7:1-212-0:1-1221-0:1-1213-0:4--0:1-12-0:24.27.33.23",
    "DB1:G:1-21321-2:3-12213-3:1-212-0:1-2121-0:1-2112-0:2--0:1-12-0:2.3.5.4.8.34",
]
WIDGET = UMG + "Widget:"
LAYOUT = UMG + "WidgetLayoutLibrary:"

# ---- behaviour
MAX_RANGE = 4000.0     # cm: no scan of a dwarf farther than this
DWELL = 0.14           # s the pointer must stay on a dwarf before the scan starts
GRACE = 0.45           # s the scan stays after the pointer left the dwarf
ANCHOR_Z = 15.0        # cm above the dwarf's centre: where the hexagon sits and the lines meet
DT_MAX = 0.05          # s: longest step of the springs (a hitch must not throw the items)
# ---- size on screen. Unit = pixels of one metre at the dwarf (Slate units).
UNIT_REF = 160.0       # Unit at which items have full size (about 6 m at FOV 90); smaller when farther
SCALE_MIN = 0.75       # smallest item scale (far away; below this the names get hard to read)
OFFSET_MAX = (440.0, 250.0)   # an item is never placed farther from the dwarf than this (very close dwarf)
EDGE = 6.0             # an item stays this far inside the screen
DEVICE_TOP = 0.6       # share of the screen height: the laser pointer's own screen is below this on the right,
                       # so items right of the dwarf stay above it
# ---- motion
BOB = (3.0, 5.0)       # px an item drifts sideways and up and down
BOB_SPEED = (1.1, 1.6)
FADE = 12.0            # how fast an item's opacity follows (FInterpTo speed)
DIMMED = 0.4           # opacity while the pointer is off the dwarf (GRACE)
FLICKER = (0.22, 21.0, 0.38, 0.25)   # for 0.22 s after it appears, 21 times a second, 38 % of the time at 25 %
GROW = 0.55            # an item starts at this share of its size and grows with its opacity
LINE_ALPHA = 0.55
LINE_GAP = 5.0         # px between an item's box and the start of its line
# ---- hexagon on the dwarf (the upgrade hexagon outline of the game's menus: wider than high)
RET = (66.0, 44.0)
RET_ALPHA = 0.8
RET_CLOSE = (0.22, 1.4)    # closes in for 0.22 s from 1 + 1.4 times its size
RET_PULSE = (4.0, 0.05)    # then breathes: speed, share of its size
PING = (0.45, 2.5, 0.55)   # second hexagon: for 0.45 s grows by 2.5 times its size, from 55 % opacity to 0
NOTE_DROP = 46.0           # px below the hexagon: "NO BUILD DATA"

# Item pictures and texts (Slate units at scale 1).
# The base sizes are what a dwarf at about 6 m gets (scale 1); closer it stays the same, farther it shrinks to
# SCALE_MIN. Texts get their size here, not from a render scale above 1 (an enlarged text would be blurred).
SIL_W, SIL_H = 290, 110
F_NAME, F_OC, F_NOTE = 21, 14, 13
OC_BOX, OC_ICON = 30, 20
PLATE = (0.0, 0.0, 0.0, 0.5)
SHADOW = {"ShadowOffset": "(X=1.0,Y=1.0)", "ShadowColorAndOpacity": "(R=0,G=0,B=0,A=0.85)"}
PERK_TILES = 6
SCAN_ZORDER = -5       # under the game's HUD and windows

# The floating items: Chip0 primary, Chip1 secondary, Chip2 grenade, Chip3 perks. Two columns beside the dwarf's
# head and shoulders: primary over grenade on the left, secondary over perks on the right. Nothing goes below the
# dwarf's centre, where its legs, the ground and (on the right) the laser pointer's own screen are.
# side: -1 left of the dwarf, 1 right. Place = side * min(kx * Unit + bx * scale, OFFSET_MAX x),
# clamp(ky * Unit + by * scale, OFFSET_MAX y) + drop * scale: drop puts a small item under its column's weapon
# (the weapon's half height + gap 8 + the small item's own half height at its size), also when the clamp holds.
# half: half the item's box at scale 1 (where its line starts). size: its own scale. spring: stiffness, damping.
# Half boxes at scale 1: a weapon 290 x 180 (picture 110, rule, name and overclock plate), the grenade 290 x 148,
# the perks 6 tiles of 40 = 263 x 48.
COLUMN = dict(kx=0.45, bx=190.0, ky=-0.32, by=-70.0)
WEAPON_HALF, GRENADE_HALF, PERKS_HALF = (145.0, 90.0), (145.0, 74.0), (132.0, 24.0)
GRENADE_SIZE, PERKS_SIZE = 0.85, 1.0
CHIPS = [
    dict(COLUMN, side=-1, drop=0.0, delay=0.00, half=WEAPON_HALF, size=1.0, phase=0.0, spring=(95.0, 13.0)),
    dict(COLUMN, side=1, drop=0.0, delay=0.07, half=WEAPON_HALF, size=1.0, phase=1.7, spring=(95.0, 13.0)),
    dict(COLUMN, side=-1, drop=WEAPON_HALF[1] + 8 + GRENADE_HALF[1] * GRENADE_SIZE, delay=0.14, half=GRENADE_HALF,
         size=GRENADE_SIZE, phase=3.1, spring=(72.0, 11.5)),
    dict(COLUMN, side=1, drop=WEAPON_HALF[1] + 8 + PERKS_HALF[1] * PERKS_SIZE, delay=0.21, half=PERKS_HALF,
         size=PERKS_SIZE, phase=4.4, spring=(72.0, 11.5)),
]
N = len(CHIPS)
FLOAT_NAMES = ["Chip%d" % i for i in range(N)] + ["Line%d" % i for i in range(N)] + ["Ret", "Ping", "Note"]


def num(value):
    return "%g" % value


class S(G):
    """G with float and Vector2D maths."""

    def k(self, fn, out="ReturnValue", **pins):
        return self.rv(KML + ":" + fn, out, **pins)

    def fadd(self, a, b):
        return self.k("Add_FloatFloat", A=a, B=b)

    def fsub(self, a, b):
        return self.k("Subtract_FloatFloat", A=a, B=b)

    def fmul(self, a, b):
        return self.k("Multiply_FloatFloat", A=a, B=b)

    def fdiv(self, a, b):
        return self.k("Divide_FloatFloat", A=a, B=b)

    def fmin(self, a, b):
        return self.k("FMin", A=a, B=b)

    def fmax(self, a, b):
        return self.k("FMax", A=a, B=b)

    def clamp(self, value, low, high):
        return self.k("FClamp", Value=value, Min=low, Max=high)

    def fgt(self, a, b):
        return self.k("Greater_FloatFloat", A=a, B=b)

    def fge(self, a, b):
        return self.k("GreaterEqual_FloatFloat", A=a, B=b)

    def flt(self, a, b):
        return self.k("Less_FloatFloat", A=a, B=b)

    def or_(self, a, b):
        return self.k("BooleanOR", A=a, B=b)

    def pick(self, cond, a, b):
        """a when cond, else b (float)."""
        return self.k("SelectFloat", A=a, B=b, bPickA=cond)

    def sin(self, a):
        return self.k("Sin", A=a)

    def vec(self, x, y):
        return self.k("MakeVector2D", X=x, Y=y)

    def vx(self, v):
        return self.k("BreakVector2D", "X", InVec=v)

    def vy(self, v):
        return self.k("BreakVector2D", "Y", InVec=v)

    def vadd(self, a, b):
        return self.k("Add_Vector2DVector2D", A=a, B=b)

    def vsub(self, a, b):
        return self.k("Subtract_Vector2DVector2D", A=a, B=b)

    def vmul(self, a, b):
        return self.k("Multiply_Vector2DFloat", A=a, B=b)

    def vlen(self, v):
        return self.k("VSize2D", A=v)

    # render transform of a widget variable (node ids)
    def move(self, name, where):
        return self.f(WIDGET + "SetRenderTranslation", target=self.v(name), Translation=where)

    def scale(self, name, x, y=None):
        return self.f(WIDGET + "SetRenderScale", target=self.v(name), Scale=self.vec(x, y if y is not None else x))

    def turn(self, name, angle):
        return self.f(WIDGET + "SetRenderTransformAngle", target=self.v(name), Angle=angle)

    def fade(self, name, opacity):
        return self.f(WIDGET + "SetRenderOpacity", target=self.v(name), InOpacity=opacity)


# ============================================================================= DB_ScanItem

def item_tree():
    """The picture (the item's outline over its fill at 40 %, both in the class colour) floats free; under it a
    small dark plate with a class-colour rule: the name, and for weapons the overclock (its frame and icon, its
    name in the type colour). Everything is centred, so the same item sits left or right of a dwarf."""
    picture = box("SilBox", SIL_W, SIL_H, var=True, slot=vslot(halign="HAlign_Center"), child=w(
        "ScaleBox", "SilScale", props={"Stretch": "ScaleToFit"}, children=[overlay("Sil", [
            props(deco(image("SilFill", WHITE, var=True, slot=oslot())), RenderOpacity="0.4"),
            deco(image("SilLine", WHITE, var=True, slot=oslot())),
        ], slot=oslot("HAlign_Center", "VAlign_Center"))]))
    name = props(text("NameText", "ITEM", RIFT, F_NAME, WHITE, var=True, justify="Center",
                      slot=vslot(halign="HAlign_Center")), **SHADOW)
    oc_icon = box("OcBox", OC_BOX, OC_BOX, var=True, slot=hslot(pad=(0, 0, 6, 0)), child=overlay("OcStack", [
        deco(image("OcFrame", WHITE, var=True, slot=oslot())),
        deco(image("OcIcon", WHITE, size=(OC_ICON, OC_ICON), var=True, slot=oslot("HAlign_Center", "VAlign_Center"))),
    ]))
    oc_name = props(text("OcName", "NO OVERCLOCK", CARBON, F_OC, DIM, var=True, slot=hslot()), **SHADOW)
    oc_row = hbox("OcRow", [oc_icon, oc_name], slot=vslot(halign="HAlign_Center", pad=(0, 1, 0, 0)), var=True)
    plate = border("Plate", PLATE, child=vbox("Texts", [name, oc_row]), pad=(12, 4, 12, 5))
    label = vbox("Label", [deco(image("Rule", WHITE, size=(8, 2), var=True)), plate],
                 slot=vslot(halign="HAlign_Center", pad=(0, 4, 0, 0)))
    return deco(vbox("Root", [picture, label]))


def g_item_show():
    g = S()
    item, oc, tint = "@entry.Item", "@entry.Overclock", "@entry.Tint"
    colours = [g.tint("SilLine", tint), g.tint("SilFill", tint), g.tint("Rule", tint)]
    known = g.br(g.and_(g.valid(item), g.valid(g.v("Data"))))
    visual = g.f(cls(DATA) + ":ItemVisual", target=g.v("Data"), Item=item)
    line = "@%s.Line" % visual
    shown = [visual, g.set_text("NameText", "@%s.Name" % visual),
             g.set_image("SilFill", "@%s.Fill" % visual, match=True), g.set_image("SilLine", line, match=True),
             g.set_vis(g.v("SilBox"), g.vis_if(g.valid(line), "HitTestInvisible", "Collapsed"))]
    unknown = [g.set_text("NameText", "UNKNOWN"), g.set_vis(g.v("SilBox"), "Collapsed")]
    with_oc = g.br("@entry.WithOc")
    g.flow("entry", *colours, known, *shown, with_oc)
    g.flow(known + ".else", *unknown, with_oc)

    g.flow(with_oc + ".else", g.set_vis(g.v("OcRow"), "Collapsed"))
    row_on = g.set_vis(g.v("OcRow"), "HitTestInvisible")
    has_oc = g.br(g.and_(g.valid(oc), g.valid(g.v("Data"))))
    tip = g.f(cls(DATA) + ":OverclockTip", target=g.v("Data"), Overclock=oc)
    out = lambda pin: "@%s.%s" % (tip, pin)  # noqa: E731
    framed = g.valid(out("Frame"))
    full = [tip, g.set_text("OcName", out("Title")), g.set_text_colour("OcName", g.slate_colour(out("Color"))),
            g.set_image("OcFrame", out("Frame")), g.tint("OcFrame", out("Color")),
            g.set_vis(g.v("OcFrame"), g.vis_if(framed, "HitTestInvisible", "Hidden")),
            g.set_image("OcIcon", out("Icon")),
            # On its frame the icon is white; without the frame (not loaded) it takes the type colour itself.
            g.tint("OcIcon", g.pick_colour(framed, "(R=1,G=1,B=1,A=1)", out("Color"))),
            g.set_vis(g.v("OcBox"), g.vis_if(g.valid(out("Icon")), "HitTestInvisible", "Collapsed"))]
    none = [g.set_text("OcName", "NO OVERCLOCK"), g.set_text_colour("OcName", DIM),
            g.set_vis(g.v("OcBox"), "Collapsed")]
    g.flow(with_oc, row_on, has_oc, *full)
    g.flow(has_oc + ".else", *none)
    return g.data()


# ============================================================================= DB_Scan

def cslot(width=None, height=None, align=(0.5, 0.5)):
    """Canvas slot at the canvas origin: the widget is put in place by its render translation alone. Without a
    size it takes its own."""
    data = "(Offsets=(Left=0,Top=0,Right=%g,Bottom=%g),Anchors=(Minimum=(X=0,Y=0),Maximum=(X=0,Y=0))," \
           "Alignment=(X=%g,Y=%g))" % (width or 0, height or 0, align[0], align[1])
    return {"LayoutData": data, "bAutoSize": "False" if width else "True"}


def scan_tree():
    """A full-screen canvas; every child sits at its origin, invisible, and is moved by render transform. Draw
    order: pulse, hexagon, lines, items, note. A line is 100 x 2 with its pivot at its left end: it is turned,
    stretched and moved from there."""
    def hidden(node):
        return props(deco(node), RenderOpacity="0.0")

    def hexagon(name):
        return hidden(image(name, WHITE, var=True, slot=cslot(*RET)))

    lines = [props(hidden(image("Line%d" % i, WHITE, var=True, slot=cslot(100, 2, (0.0, 0.5)))),
                   RenderTransformPivot="(X=0.0,Y=0.5)") for i in range(N)]
    items = [hidden(w(cls(SCANITEM), "Chip%d" % i, True, slot=cslot())) for i in range(N - 1)]
    tiles = [props(w(cls(PERK), "T%d" % i, True, slot=hslot(pad=(3 if i else 0, 0, 0, 0))), Visibility="Collapsed")
             for i in range(PERK_TILES)]
    perks = hidden(border("Chip%d" % (N - 1), PLATE, child=hbox("Tiles", tiles), pad=(4, 4, 4, 4), var=True,
                          slot=cslot()))
    note = hidden(border("Note", PLATE, child=props(text("NoteText", "NO BUILD DATA", CARBON, F_NOTE, DIM), **SHADOW),
                         pad=(8, 3, 8, 3), var=True, slot=cslot(align=(0.5, 0.0))))
    return w("CanvasPanel", "Root", props={"Visibility": "HitTestInvisible"},
             children=[hexagon("Ping"), hexagon("Ret")] + lines + items + [perks, note])


def scan_members():
    """Pointer, On: the laser pointer while it is out. Hit: the dwarf under it this Tick; Cand, CandT: the dwarf
    it rests on and for how long; Target: the scanned dwarf (kept until the items have faded); Locked: the scan
    is up; LostT: time since the pointer left Target; Age: time since the lock; Snap: the items start from the
    dwarf on the next Tick; AnyShown: something may be visible. A, AOk, Unit, Sc: the dwarf's place on screen,
    whether it is in front of the camera, pixels per metre there, the item scale. Per item: Pos, Vel (spring),
    Alpha, Show (it has something to show). T...: working values of one item's step."""
    f, b = "float", "bool"
    variables = [
        t("Pointer", "object", LASERPOINTER), t("On", b),
        t("Hit", "object", TARGET), t("Cand", "object", TARGET), t("Target", "object", TARGET),
        t("CandT", f), t("LostT", f), t("Age", f), t("Clock", f), t("Dt", f),
        t("Locked", b), t("HasBuild", b), t("Snap", b), t("AnyShown", b), t("AOk", b), t("HasHex", b),
        t("A", "struct", VEC2), t("Unit", f), t("Sc", f, default="1.0"), t("ViewW", f), t("ViewH", f),
        t("RetA", f), t("NoteA", f), t("Tint", "struct", LINEAR), t("Code", "string"),
        t("ScanPerks", "object", PERKASSET, array=True), t("ScanRanks", "int", array=True),
        t("TAct", b), t("TGoal", "struct", VEC2), t("TAlpha", f), t("TSc", f), t("TPos", "struct", VEC2),
        t("TD", "struct", VEC2), t("TLen", f), t("TEdge", f), t("TL", f),
    ]
    for i in range(N):
        variables += [t("Pos%d" % i, "struct", VEC2), t("Vel%d" % i, "struct", VEC2), t("Alpha%d" % i, f),
                      t("Show%d" % i, b)]
    if DEV:
        # Fill: Target as a player (None for a stand-in); how many stand-ins were scanned (picks the sample).
        variables += [t("Dwarf", "object", PLAYERCHAR), t("DevN", "int")]
    return {"variables": variables, "functions": [{"name": "Lock"}, {"name": "Fill"}, {"name": "HideAll"}]}


def g_scan_point():
    """Out: the layer is drawn again (its Tick runs). Away: the scan lets go; the Tick fades it and collapses the
    layer when nothing is left."""
    g = S()
    keep = [g.put("Pointer", "@entry.Pointer"), g.put("On", g.valid(g.v("Pointer"))), g.put("Cand"),
            g.put("CandT", "0")]
    out = g.br(g.v("On"))
    g.flow("entry", *keep, out, g.set_vis(g.me(), "HitTestInvisible"))
    g.flow(out + ".else", g.put("Locked", "false"))
    return g.data()


def g_scan_lock():
    g = S()
    g.flow("entry", g.put("Target", g.v("Cand")), g.put("Locked", "true"), g.put("LostT", "0"), g.put("Age", "0"),
           g.put("Snap", "true"), g.put("AnyShown", "true"), g.f("Fill"))
    return g.data()


def g_scan_hide_all():
    g = S()
    steps = [g.fade(name, "0") for name in FLOAT_NAMES]
    steps += [g.put("Alpha%d" % i, "0") for i in range(N)]
    steps += [g.put("RetA", "0"), g.put("NoteA", "0"), g.put("AnyShown", "false")]
    g.flow("entry", *steps)
    return g.data()


def g_scan_fill():
    """Target's build into the items, once per lock. First the code, the perks and the colour (a player: from
    DB_Data, the class colour of the dwarf; a dev build's stand-in: a sample code and its class colour), then the
    colours (they also show without a build) and the items. No Data, no player state or no code: HasBuild stays
    false and the note shows."""
    g = S()
    data = g.v("Data")
    last = "Show%d" % (N - 1)
    reset = [g.put("HasBuild", "false")] + [g.put("Show%d" % i, "false") for i in range(N)]
    has_data = g.br(g.valid(data))
    g.flow("entry", *reset, has_data)

    # ---- a player
    dwarf = g.v("Dwarf") if DEV else g.v("Target")
    tint = g.put("Tint", g.rv(PLAYERCHAR + ":GetHeroColor", target=dwarf))
    state = g.rv(PLAYERCHAR + ":GetPlayerState", target=dwarf)
    has_state = g.br(g.valid(state))
    code = g.f(cls(DATA) + ":CodeOf", target=data, Player=state)
    # Perks: only when they are known (state 0); else the perk item is left out.
    perks = g.f(cls(DATA) + ":PerksOf", target=data, Player=state)
    player = [code, g.put("Code", "@%s.Code" % code),
              g.put("HasBuild", g.gt(g.rv(KSTR + ":Len", S=g.v("Code")), "0")),
              perks, g.put("ScanPerks", "@%s.Perks" % perks), g.put("ScanRanks", "@%s.Ranks" % perks),
              g.put(last, g.and_(g.eq("@%s.State" % perks, "0"), g.gt(g.length(g.v("ScanPerks")), "0")))]
    paint = g.tint("Ret", g.v("Tint"))
    g.flow(tint, has_state, *player, paint)
    g.flow(has_state + ".else", paint)
    if not DEV:
        g.flow(has_data, tint)
    else:
        # ---- dev build: anything else under the pointer gets the next sample build.
        g.cast("asDwarf", PLAYERCHAR, unref(g.v("Target")))
        index = g.rv(KML + ":Percent_IntInt", A=g.v("DevN"), B=str(len(DEV_CODES)))
        sample = DEV_CODES[-1]
        for i in range(len(DEV_CODES) - 2, -1, -1):
            sample = g.pick_string(g.eq(index, str(i)), DEV_CODES[i], sample)
        header = g.f(cls(DATA) + ":HeaderOfCode", target=data, Code=g.v("Code"))
        code_perks = g.f(cls(DATA) + ":PerksOfCode", target=data, Code=g.v("Code"))
        stand_in = [g.put("Code", sample), g.put("DevN", g.add(g.v("DevN"), "1")), g.put("HasBuild", "true"),
                    header, g.put("Tint", "@%s.Color" % header),
                    code_perks, g.put("ScanPerks", "@%s.Perks" % code_perks),
                    g.put("ScanRanks", "@%s.Ranks" % code_perks), g.put(last, "@%s.Found" % code_perks)]
        g.flow(has_data, "asDwarf", g.put("Dwarf", "@asDwarf.$cast"), tint)
        g.flow("asDwarf.CastFailed", *stand_in, paint)

    # ---- colours, then the items
    tints = [g.tint(name, g.v("Tint")) for name in ["Ping"] + ["Line%d" % i for i in range(N)]]
    outline = g.v("HexOutline", cls(DATA), data)
    has_hex = g.br(g.valid(outline))
    hexes = [g.set_image("Ret", outline), g.set_image("Ping", outline), g.put("HasHex", "true")]
    no_hex = g.put("HasHex", "false")
    has_build = g.br(g.v("HasBuild"))
    g.flow(paint, *tints, has_hex, *hexes, has_build)
    g.flow(has_hex + ".else", no_hex, has_build)
    steps = []
    for chip, slot, with_oc in ((0, 0, True), (1, 1, True), (2, 5, False)):
        decoded = g.f(cls(DATA) + ":DecodeSlot", target=data, Code=g.v("Code"), Slot=str(slot))
        out = lambda pin, node=decoded: "@%s.%s" % (node, pin)  # noqa: E731
        widget = g.v("Chip%d" % chip)
        steps += [decoded, g.put("Data", data, cls(SCANITEM), widget),
                  g.f(cls(SCANITEM) + ":Show", target=widget, Item=g.pick_obj(out("Found"), out("Item"), ITEMID),
                      Overclock=out("Overclock"), Tint=g.v("Tint"), WithOc="true" if with_oc else "false"),
                  g.put("Show%d" % chip, out("Found"))]
    g.flow(has_build, *steps)
    tails = [steps[-1]]
    for i in range(PERK_TILES):
        tile = g.v("T%d" % i)
        there = g.br(g.lt(str(i), g.length(g.v("ScanPerks"))))
        fill = [g.f(cls(PERK) + ":Set", target=tile, Perk=g.at(g.v("ScanPerks"), str(i)),
                    Rank=g.at(g.v("ScanRanks"), str(i))), g.set_vis(tile, "HitTestInvisible")]
        hide = g.set_vis(tile, "Collapsed")
        g.after(tails, there)
        g.flow(there, *fill)
        g.flow(there + ".else", hide)
        tails = [fill[-1], hide]
    return g.data()


def chip_step(g, i):
    """One item's Tick. Returns (first node, exits)."""
    cfg = CHIPS[i]
    chip, line = "Chip%d" % i, "Line%d" % i
    pos, vel, alpha = "Pos%d" % i, "Vel%d" % i, "Alpha%d" % i
    stiffness, damping = cfg["spring"]
    half_w, half_h = cfg["half"]
    age = g.fsub(g.v("Age"), num(cfg["delay"]))
    # Out (it has something to show and its turn has come) or in (back into the dwarf).
    active = g.put("TAct", g.and_(g.and_(g.v("Locked"), g.v("HasBuild")),
                                  g.and_(g.v("Show%d" % i), g.fge(age, "0"))))
    out = g.br(g.v("TAct"))
    off_x = g.fmul(num(cfg["side"]), g.fmin(g.fadd(g.fmul(g.v("Unit"), num(cfg["kx"])),
                                                  g.fmul(g.v("Sc"), num(cfg["bx"]))), num(OFFSET_MAX[0])))
    raw_y = g.fadd(g.fmul(g.v("Unit"), num(cfg["ky"])), g.fmul(g.v("Sc"), num(cfg["by"])))
    off_y = g.fadd(g.clamp(raw_y, num(-OFFSET_MAX[1]), num(OFFSET_MAX[1])), g.fmul(g.v("Sc"), num(cfg["drop"])))
    bob_x = g.fmul(g.sin(g.fadd(g.fmul(g.v("Clock"), num(BOB_SPEED[0])), num(cfg["phase"]))),
                   g.fmul(g.v("Sc"), num(BOB[0])))
    bob_y = g.fmul(g.sin(g.fadd(g.fmul(g.v("Clock"), num(BOB_SPEED[1])), num(cfg["phase"] * 1.3))),
                   g.fmul(g.v("Sc"), num(BOB[1])))
    goal_out = [g.put("TGoal", g.vadd(g.v("A"), g.vec(g.fadd(off_x, bob_x), g.fadd(off_y, bob_y)))),
                g.put("TAlpha", g.pick(g.fgt(g.v("LostT"), "0.06"), num(DIMMED), "1.0"))]
    goal_in = [g.put("TGoal", g.v("A")), g.put("TAlpha", "0")]
    # Spring: the speed first, then the place with the new speed.
    pull = g.vsub(g.vmul(g.vsub(g.v("TGoal"), g.v(pos)), num(stiffness)), g.vmul(g.v(vel), num(damping)))
    spring = [g.put(vel, g.vadd(g.v(vel), g.vmul(pull, g.v("Dt")))),
              g.put(pos, g.vadd(g.v(pos), g.vmul(g.v(vel), g.v("Dt")))),
              g.put(alpha, g.k("FInterpTo", Current=g.v(alpha), Target=g.v("TAlpha"), DeltaTime=g.v("Dt"),
                               InterpSpeed=num(FADE)))]
    seen = g.br(g.or_(g.v("TAct"), g.fgt(g.v(alpha), "0.004")))
    gone = [g.fade(chip, "0"), g.fade(line, "0"), g.put(pos, g.v("A")), g.put(vel, g.vec("0", "0")),
            g.put(alpha, "0")]
    g.flow(active, out, *goal_out, spring[0])
    g.flow(out + ".else", *goal_in, spring[0])
    g.flow(*spring, seen)
    g.flow(seen + ".else", *gone)

    # Drawn: size grows with the opacity; the place is kept inside the screen.
    size = g.put("TSc", g.fmul(g.fmul(g.v("Sc"), num(cfg["size"])),
                               g.fadd(num(GROW), g.fmul(g.v(alpha), num(1.0 - GROW)))))
    reach_x = g.fadd(g.fmul(g.v("TSc"), num(half_w)), num(EDGE))
    reach_y = g.fadd(g.fmul(g.v("TSc"), num(half_h)), num(EDGE))
    # Right of the dwarf the laser pointer's screen takes the bottom of the view.
    bottom = g.fmul(g.v("ViewH"), num(DEVICE_TOP)) if cfg["side"] > 0 else g.v("ViewH")
    place = g.put("TPos", g.vec(
        g.clamp(g.vx(g.v(pos)), reach_x, g.fmax(reach_x, g.fsub(g.v("ViewW"), reach_x))),
        g.clamp(g.vy(g.v(pos)), reach_y, g.fmax(reach_y, g.fsub(bottom, reach_y)))))
    span, rate, share, low = FLICKER
    flick = g.pick(g.and_(g.flt(age, num(span)), g.flt(g.k("Fraction", A=g.fmul(age, num(rate))), num(share))),
                   num(low), "1.0")
    draw = [size, place, g.move(chip, g.v("TPos")), g.scale(chip, g.v("TSc")),
            g.fade(chip, g.fmul(g.v(alpha), flick))]
    # The line: from the item's box (where the way to the dwarf leaves it) to the hexagon's edge.
    way = [g.put("TD", g.vsub(g.v("A"), g.v("TPos"))), g.put("TLen", g.fmax(g.vlen(g.v("TD")), "1.0"))]
    dir_x = g.fmax(g.fdiv(g.k("Abs", A=g.vx(g.v("TD"))), g.v("TLen")), "0.001")
    dir_y = g.fmax(g.fdiv(g.k("Abs", A=g.vy(g.v("TD"))), g.v("TLen")), "0.001")
    edge = g.put("TEdge", g.fadd(g.fmin(g.fdiv(g.fmul(g.v("TSc"), num(half_w)), dir_x),
                                        g.fdiv(g.fmul(g.v("TSc"), num(half_h)), dir_y)), num(LINE_GAP)))
    length = g.put("TL", g.fsub(g.fsub(g.v("TLen"), g.v("TEdge")), g.fmul(g.v("Sc"), num(RET[0] * 0.5))))
    long_enough = g.br(g.fgt(g.v("TL"), "4.0"))
    start = g.vadd(g.v("TPos"), g.vmul(g.v("TD"), g.fdiv(g.v("TEdge"), g.v("TLen"))))
    drawn = [g.move(line, start), g.turn(line, g.k("DegAtan2", Y=g.vy(g.v("TD")), X=g.vx(g.v("TD")))),
             g.scale(line, g.fdiv(g.v("TL"), "100.0"), "1.0"), g.fade(line, g.fmul(g.v(alpha), num(LINE_ALPHA)))]
    short = g.fade(line, "0")
    g.flow(seen, *draw, *way, edge, length, long_enough, *drawn)
    g.flow(long_enough + ".else", short)
    return active, [gone[-1], drawn[-1], short]


def g_scan_events():
    """Tick: what is under the pointer, the scan's state, then (with a scanned dwarf) its place on screen, the
    items, the hexagon and the note. See the module text."""
    g = S()
    g.node("tick", "event", name="Tick", **{"class": USERWIDGET})
    size = g.rv(UMG + "SlateBlueprintLibrary:GetLocalSize", Geometry="@tick.MyGeometry")
    start = [g.put("Dt", g.fmin("@tick.InDeltaTime", num(DT_MAX))), g.put("Clock", g.fadd(g.v("Clock"), g.v("Dt"))),
             g.put("ViewW", g.vx(size)), g.put("ViewH", g.vy(size)), g.put("Hit")]

    # ---- the dwarf under the pointer: the pointer's own hit result (the game fills it for its display).
    pointer = g.v("Pointer")
    out = g.br(g.and_(g.v("On"), g.valid(pointer)))
    near = g.br(g.flt(g.v("LookAtDistance", LASERPOINTER, pointer), num(MAX_RANGE)))
    hit_actor = g.rv(GS + ":BreakHitResult", "HitActor", Hit=g.v("LookAtHit", LASERPOINTER, pointer))
    g.cast("asDwarf", PLAYERCHAR, unref(hit_actor))
    keep_hit = g.put("Hit", "@asDwarf.$cast")

    # ---- state
    hit = g.br(g.valid(g.v("Hit")))
    same = g.br(g.and_(g.v("Locked"), g.obj_eq(g.v("Hit"), g.v("Target"))))
    held = g.put("LostT", "0")
    resting = g.br(g.obj_eq(g.v("Hit"), g.v("Cand")))
    dwell = g.put("CandT", g.fadd(g.v("CandT"), g.v("Dt")))
    ready = g.br(g.fge(g.v("CandT"), num(DWELL)))
    lock = g.f("Lock")
    new_cand = [g.put("Cand", g.v("Hit")), g.put("CandT", "0")]
    no_cand = [g.put("Cand"), g.put("CandT", "0")]
    lost = g.put("LostT", g.fadd(g.v("LostT"), g.v("Dt")))
    release = g.br(g.and_(g.v("Locked"), g.fgt(g.v("LostT"), num(GRACE))))
    unlock = g.put("Locked", "false")
    aging = g.br(g.v("Locked"))
    age = g.put("Age", g.fadd(g.v("Age"), g.v("Dt")))
    scanned = g.br(g.valid(g.v("Target")))

    g.flow("tick", *start, out, near, "asDwarf", keep_hit, hit)
    g.flow(out + ".else", hit)
    g.flow(near + ".else", hit)
    if DEV:
        # Dev build: any other pawn can be scanned too.
        g.cast("asPawn", PAWN, unref(hit_actor))
        g.flow("asDwarf.CastFailed", "asPawn", g.put("Hit", "@asPawn.$cast"), hit)
        g.flow("asPawn.CastFailed", hit)
    else:
        g.flow("asDwarf.CastFailed", hit)
    g.flow(hit, same, held, release)
    g.flow(same + ".else", resting, dwell, ready, lock, release)
    g.flow(ready + ".else", lost)
    g.flow(resting + ".else", *new_cand, lost)
    g.flow(hit + ".else", *no_cand, lost)
    g.flow(lost, release, unlock, aging)
    g.flow(release + ".else", aging)
    g.flow(aging, age, scanned)
    g.flow(aging + ".else", scanned)

    # ---- nothing scanned (or the dwarf is gone): hide what is left; with the pointer away, stop ticking.
    left = g.br(g.v("AnyShown"))
    idle = g.br(g.v("On"))
    collapse = g.set_vis(g.me(), "Collapsed")
    g.flow(scanned + ".else", left, g.f("HideAll"), g.put("Locked", "false"), idle)
    g.flow(left + ".else", idle)
    g.flow(idle + ".else", collapse)

    # ---- the dwarf on screen: its place, and the pixels of one metre there.
    owner = g.rv(WIDGET + "GetOwningPlayer")
    where = g.k("Add_VectorVector", A=g.rv(ACTOR + ":K2_GetActorLocation", target=g.v("Target")),
                B=g.k("MakeVector", X="0", Y="0", Z=num(ANCHOR_Z)))
    centre = g.f(LAYOUT + "ProjectWorldLocationToWidgetPosition", PlayerController=owner, WorldLocation=where,
                 bPlayerViewportRelative="false")
    above = g.rv(LAYOUT + "ProjectWorldLocationToWidgetPosition", "ScreenPosition", PlayerController=owner,
                 WorldLocation=g.k("Add_VectorVector", A=where, B=g.k("MakeVector", X="0", Y="0", Z="100")),
                 bPlayerViewportRelative="false")
    placed = [g.put("AOk", "@%s.ReturnValue" % centre), g.put("A", "@%s.ScreenPosition" % centre),
              g.put("Unit", g.vlen(g.vsub(above, g.v("A")))),
              g.put("Sc", g.clamp(g.fdiv(g.v("Unit"), num(UNIT_REF)), num(SCALE_MIN), "1.0"))]
    in_front = g.br(g.v("AOk"))
    g.flow(scanned, *placed, in_front)
    g.flow(in_front + ".else", g.f("HideAll"), g.put("Locked", "false"), g.put("Target"))

    # A new lock: every item starts in the dwarf, still.
    snap = g.br(g.v("Snap"))
    snapped = [g.put("Snap", "false")]
    for i in range(N):
        snapped += [g.put("Pos%d" % i, g.v("A")), g.put("Vel%d" % i, g.vec("0", "0")), g.put("Alpha%d" % i, "0")]
    g.flow(in_front, snap, *snapped)
    tails = [snapped[-1], snap + ".else"]
    for i in range(N):
        first, exits = chip_step(g, i)
        g.after(tails, first)
        tails = exits

    # ---- the hexagon on the dwarf, its pulse, the note.
    dimmed = g.pick(g.fgt(g.v("LostT"), "0.06"), num(RET_ALPHA * DIMMED), num(RET_ALPHA))
    ret_goal = g.pick(g.and_(g.v("Locked"), g.v("HasHex")), dimmed, "0")
    close_t = g.fmax(g.fsub("1.0", g.fdiv(g.v("Age"), num(RET_CLOSE[0]))), "0")
    ret_size = g.fmul(g.v("Sc"), g.fadd(g.fadd("1.0", g.fmul(g.fmul(close_t, close_t), num(RET_CLOSE[1]))),
                                        g.fmul(g.sin(g.fmul(g.v("Clock"), num(RET_PULSE[0]))), num(RET_PULSE[1]))))
    ping_t = g.fdiv(g.v("Age"), num(PING[0]))
    ping_on = g.and_(g.and_(g.v("Locked"), g.v("HasHex")), g.flt(ping_t, "1.0"))
    note_goal = g.pick(g.and_(g.v("Locked"), g.not_(g.v("HasBuild"))), "1.0", "0")
    rest = [
        g.put("RetA", g.k("FInterpTo", Current=g.v("RetA"), Target=ret_goal, DeltaTime=g.v("Dt"),
                          InterpSpeed=num(FADE))),
        g.move("Ret", g.v("A")), g.scale("Ret", ret_size), g.fade("Ret", g.v("RetA")),
        g.move("Ping", g.v("A")), g.scale("Ping", g.fmul(g.v("Sc"), g.fadd("1.0", g.fmul(ping_t, num(PING[1]))))),
        g.fade("Ping", g.pick(ping_on, g.fmul(g.fsub("1.0", ping_t), num(PING[2])), "0")),
        g.put("NoteA", g.k("FInterpTo", Current=g.v("NoteA"), Target=note_goal, DeltaTime=g.v("Dt"),
                           InterpSpeed=num(FADE))),
        g.move("Note", g.vadd(g.v("A"), g.vec("0", g.fmul(g.v("Sc"), num(NOTE_DROP))))),
        g.fade("Note", g.v("NoteA")),
    ]
    g.after(tails, rest[0])
    g.flow(*rest)

    # ---- all faded after the scan let go: forget the dwarf; with the pointer away, stop ticking.
    total = g.fadd(g.v("RetA"), g.v("NoteA"))
    for i in range(N):
        total = g.fadd(total, g.v("Alpha%d" % i))
    over = g.br(g.and_(g.not_(g.v("Locked")), g.flt(total, "0.02")))
    away = g.br(g.v("On"))
    g.flow(rest[-1], over, g.f("HideAll"), g.put("Target"), away)
    g.flow(away + ".else", g.set_vis(g.me(), "Collapsed"))
    return g.data()


# ============================================================================= module parts

def trees():
    return {SCANITEM: item_tree(), SCAN: scan_tree()}


def members():
    return {SCANITEM: {"variables": [], "functions": []}, SCAN: scan_members()}


def graphs():
    return {
        SCANITEM: {"Show": g_item_show()},
        SCAN: {"Point": g_scan_point(), "Lock": g_scan_lock(), "Fill": g_scan_fill(), "HideAll": g_scan_hide_all(),
               "EventGraph": g_scan_events()},
    }
