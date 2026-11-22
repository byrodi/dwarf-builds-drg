"""Content widgets of Dwarf Builds: tooltip, upgrade cell, perk tile, weapon card, gear card and player column.

Look: the game's own menus (gear modification and loadout screens) on the layout of the approved mockup. Panels
and cards are translucent black with a 3 px orange rule on top, titles white Rift Soft, categories Carbon,
accents orange; upgrade hexagons orange, the chosen one yellow with a white outline, joined in a tier row by a
thin dark line; action buttons are the game's (common.game_button). Every box has a fixed size (Slate units at
1920x1080), so every class takes the same space; long names are clipped.
Font sizes are UMG points. A text in a fixed row gets its own line height and a slot padding that centres its
capitals in the row (font metrics below), so a big font in a tight row is neither cut nor off centre.

Nothing ticks. Widgets change only in Set/Show, on a button click, or when the mouse enters (tooltips).
Tooltips are made on the first hover only: one DB_Tip per widget, refilled when what it shows has changed.
"""
import math

from dwarfbuilds.common import press_feedback  # noqa: E402
from dwarfbuilds.common import LINK as BUILD_LINK  # noqa: E402  (LINK is a colour here)
from dwarfbuilds.common import (ACTOR, BLACK_TEXT, BODY, CARBON, CARD, CELL, CHARID, COLUMN, DARK, DATA, FRONTEND,
                               GEAR, GEAR_LABELS, GFL, GS, ITEMID, KARR, KML, KSL, KSTR, KTXT, LIGHT_TEXT, LINEAR,
                               ORANGE, ORANGE_LIGHT, OVERCLOCK, PERK, PERK_ACTIVE, PERK_PASSIVE, PERK_PROF,
                               PERKASSET, PERKITEM, PS, RIFT, SAVEGAME, SELECTION, SGSC, SHARE, SHOWN_SLOTS, TEXTURE,
                               TIP,
                               UMG, UPGRADE, USERWIDGET, WBL, WHITE, WINDOW, Graph, border, box, cls, colour,
                               game_button, image, margin, oslot, ref, slate, t, text, vslot, hslot, w)

FSD = "/Script/FSD."
WIDGET = UMG + "Widget:"
TEXTBLOCK = UMG + "TextBlock:"
IMAGE = UMG + "Image:"
BORDER = UMG + "Border:"
VIS = UMG + "ESlateVisibility"
SLATECOLOR = "/Script/SlateCore.SlateColor"
CATEGORY = FSD + "ItemUpgradeCategory"
PROGRESS = FSD + "CharacterProgress"
PLAYERSTATE = "/Script/Engine.PlayerState"


def srgb(hexcode, a=1.0):
    """Linear colour of an sRGB hex colour of the mockup."""
    def lin(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    h = hexcode.lstrip("#")
    return (round(lin(int(h[0:2], 16)), 5), round(lin(int(h[2:4], 16)), 5), round(lin(int(h[4:6], 16)), 5), a)


# Tones. Panels: translucent black like the game's loadout cards (Black at 0.3) over the window's brown dim.
PANEL = (0.0, 0.0, 0.0, 0.4)   # card, header, gear and perk panels
INK = srgb("#17140D")          # dark text and icons on orange
DIM = srgb("#A3977A")          # gear slot labels, weapon category, notes, UNKNOWN
LIGHT = srgb("#F4EBD0")        # tooltip body
EMPTY_TILE = (DARK[0], DARK[1], DARK[2], 0.6)   # overclock box without an overclock
TIP_BG = (0.0, 0.0, 0.0, 0.9)
EXTRA_BG = (DARK[0], DARK[1], DARK[2], 0.5)     # the game's "more info" box: Main Tint Dark at 50 %
NO_DRAW = None

# Upgrade cell colours (the game's hexagons): chosen = yellow with a white outline, not chosen = orange, both with
# a black icon; empty (unknown item) = a dim dark hexagon. LINK = the line that joins the options of a tier row.
SEL_BG, SEL_LINE, SEL_ICON = ORANGE_LIGHT, WHITE, (0.0, 0.0, 0.0)
OFF_BG, OFF_LINE, OFF_ICON = ORANGE, ORANGE, (0.0, 0.0, 0.0)
EMPTY_BG, EMPTY_LINE = (0.0, 0.0, 0.0, 0.45), DARK
LINK, LINK_H = DARK, 3
# Perk row: 3 passive, 2 active, 1 proficiency tile; PERK_GAP between tiles of a kind, KIND_GAP between kinds.
PERK_TILES = [("P1", "P2", "P3"), ("A1", "A2"), ("F1",)]
PERK_GAP, KIND_GAP = 4, 10
# Perk tile without a perk: a dark rim (Frame) around a darker inside (Fill over it).
EMPTY_FRAME, EMPTY_FILL = DARK, (0.0, 0.0, 0.0, 0.7)

# Fonts (UMG points).
F_HEAD_NAME, F_HEAD_SUB, F_TAG = 24, 14, 16
F_CARD_NAME, F_CARD_CAT, F_OC_NAME, F_OC_TYPE = 24, 13, 17, 12
F_GEAR_LABEL, F_GEAR_NAME = 11, 17
F_PERKS, F_NOTE, F_BUTTON = 20, 14, 22
F_TIP_TITLE, F_TIP_CAT, F_TIP_BODY = 26, 14, 17
F_TIP_EXTRA_TITLE, F_TIP_EXTRA, F_TIP_MORE, F_TIP_KEY = 16, 16, 15, 14

# Vertical metrics of the game fonts (read from the font files), in ems: line height (ascender + descender +
# line gap), descender, capital height. UMG fonts have an em of size * 96/72 px; FreeType rounds the line
# height and the descender to whole pixels, and Slate puts the baseline one descender above the line's bottom.
VMETRICS = {RIFT: (1.2, 0.22, 0.70),        # Rift Soft Bold: ascender 980, descender 220, caps 700 (of 1000)
            CARBON: (1.024, 0.20, 0.59),    # Carbon Bold: 801 / 200 / line gap 23 / caps 590
            BODY: (1.2, 0.265, 0.679)}      # Acumin Pro Condensed: 735 / 265 / line gap 200 / caps 679

# Sizes (Slate units at 1920x1080).
# Column: header 62 | 6 | card 210 | 6 | card 210 | 6 | gear area 382 | 6 | perks 52 | 6 | buttons 44 = 990.
# Compact (SetCompact): no button row and no gap above it = 940.
COL_W, COL_H = 418, 990
HEAD_H, CARD_H, GEAR_AREA_H, PERK_H, BTN_H, GAP = 62, 210, 382, 52, 44, 6
COMPACT_H = COL_H - GAP - BTN_H   # 940
CLASS_ICON, HEAD_NAME_H, HEAD_SUB_H, TAG_H = 40, 34, 20, 26
# Upgrade grid of weapon and gear cards: 3 options a row, cells 44x29, 5 apart across and 4 down.
CELL_W, CELL_H, CELL_GAP_X, CELL_GAP_Y = 44, 29, 5, 4
CELL_ICON = 21.0   # upgrade icon size (about 70 % of the cell height)
GRID_W = 3 * CELL_W + 2 * CELL_GAP_X   # 142
# Weapon card: top row 28 (name); body = category line, silhouette and overclock left (240 wide), 5x3 upgrade grid
# right (142x161). The category row (15) is taken from the silhouette (was 105 high).
CARD_TOP_H, SIL_W, SIL_H, OC_BOX, OC_ICON = 28, 240, 92, 44, 26
CARD_CAT_H, CARD_CAT_TOP = 15, 1
# Gear card (2x2 in the gear area): label, name, then the 4x3 upgrade grid (142x128) or the item picture, left
# aligned with the texts. 188 = rule 3 + label 19 + name 24 + 2 + grid 128 + 12.
GEAR_W, GEAR_H, GEAR_TIERS, GEAR_PAD = 206, 188, 4, 12
GEAR_LABEL_H, GEAR_LABEL_TOP, GEAR_NAME_H, GEAR_NAME_TOP, GEAR_GRID_TOP = 19, 7, 24, 2.5, 2
GEAR_BODY_H = GEAR_TIERS * CELL_H + (GEAR_TIERS - 1) * CELL_GAP_Y   # 128
TILE, PERK_ICON = 40, 28
TIP_W, TIP_TILE, TIP_KEY = 480, 64, 22

TEXT_NOT_SHARED = "Not available. The host does not run this mod."
TEXT_WAITING = "Waiting for the host..."
TEXT_NO_PERKS = "Not available. The game does not share this player's perks."
# DB_Column.SameAsLast: a column is drawn again at least every FRESH_FOR seconds, and when ShowPlayer was not called
# for SEEN_GAP seconds (the window or the overlay was closed meanwhile: callers refresh once a second while shown).
FRESH_FOR = "10.0"
SEEN_GAP = "1.5"
TEXT_CODE_NO_PERKS = "No perks in this code."
TEXT_COPY, TEXT_COPIED, TEXT_TAKE = "COPY CODE", "COPIED", "TAKE BUILD"
COPIED_SECONDS = "1.5"


# ----------------------------------------------------------------------------- tree helpers

def props(node, **values):
    node.setdefault("props", {}).update(values)
    return node


def clipped(node):
    """Long text is cut at the edge of its box, never wrapped."""
    return props(node, Clipping="ClipToBounds")


def deco(node):
    """Decoration only: no hit testing."""
    return props(node, Visibility="HitTestInvisible")


def hbox(name, children, slot=None, var=False):
    return w("HorizontalBox", name, var, None, slot, children)


def vbox(name, children, slot=None, var=False):
    return w("VerticalBox", name, var, None, slot, children)


def overlay(name, children, slot=None, var=False):
    return w("Overlay", name, var, None, slot, children)


def rule(name, c=ORANGE, height=3, var=False):
    """Thin coloured line across its panel (a VerticalBox child)."""
    return deco(image(name, c, size=(8, height), var=var))


def spacer(name, width, height=1, var=False, slot=None):
    return w("Spacer", name, var, {"Size": "(X=%g,Y=%g)" % (width, height)}, slot)


def fill_slot(value, pad=(0, 0, 0, 0)):
    """HorizontalBox slot that takes `value` shares of the free width and the full height."""
    slot = hslot(True, pad, valign="VAlign_Fill")
    slot["Size"] = "(Value=%g,SizeRule=Fill)" % value
    return slot


def brush(c):
    """Solid colour brush of a button state; None draws nothing."""
    if c is None:
        return "(DrawAs=NoDrawType)"
    return "(ResourceObject=None,ResourceName=None,DrawAs=Image,TintColor=%s)" % slate(c)


def button(name, child, normal, hovered, pressed, disabled=None, slot=None, pad=(0, 0, 0, 0)):
    """Button that never takes keyboard focus (the window keeps its key events)."""
    style = "(Normal=%s,Hovered=%s,Pressed=%s,Disabled=%s,NormalPadding=%s,PressedPadding=%s)" % (
        brush(normal), brush(hovered), brush(pressed), brush(disabled if disabled is not None else normal),
        margin(*pad), margin(*pad))
    return w("Button", name, True, {"WidgetStyle": style, "IsFocusable": "False"}, slot, [child])


def content_slot(halign="HAlign_Fill", valign="VAlign_Fill"):
    """Slot of a button's child."""
    return {"HorizontalAlignment": halign, "VerticalAlignment": valign, "Padding": margin()}


def caps_pad(face, size, height, top=None):
    """(top, bottom) padding of a text slot with VAlign_Fill in a row `height` px high: the text gets exactly its
    line height, and its capitals are centred in the row (or start `top` px below the row's top). Negative
    padding lets the line box stick out of a row that is lower than the font's line height."""
    line_em, desc_em, cap_em = VMETRICS[face]
    em = size * 96.0 / 72.0
    line = round(line_em * em)
    cap = cap_em * em
    cap_top = line - math.ceil(desc_em * em - 1e-6) - cap
    pre = round(((height - cap) / 2.0 if top is None else top) - cap_top, 1)
    return pre, round(height - pre - line, 1)


def fit_slot(face, size, height, top=None, halign="HAlign_Fill", left=0, right=0, fill=False):
    """Slot (SizeBox, Button, Overlay or Horizontal/VerticalBox) of a text in a row `height` px high; see caps_pad."""
    pre, post = caps_pad(face, size, height, top)
    slot = {"Padding": margin(left, pre, right, post), "HorizontalAlignment": halign,
            "VerticalAlignment": "VAlign_Fill"}
    if fill:
        slot["Size"] = "(Value=1.0,SizeRule=Fill)"
    return slot


def capbox(name, node, face, size, height, width=None, top=None, var=False, slot=None):
    """Text `node` in a fixed-height box, capitals centred (see caps_pad)."""
    node["slot"] = fit_slot(face, size, height, top)
    return box(name, width, height, child=node, var=var, slot=slot)


# ----------------------------------------------------------------------------- graph helpers

def unref(pin):
    return pin[1:] if pin.startswith("@") else pin


class G(Graph):
    """Graph with short helpers. Values are refs ("@node.pin") or pin defaults; helpers that make a value return
    a ref, helpers that run return the node id (for flow)."""

    def v(self, name, owner=None, target=None):
        nid = self.uid("get")
        self.get(nid, name, owner, unref(target) if target else None)
        return "@%s.%s" % (nid, name)

    def f(self, fn, **pins):
        nid = self.uid("call")
        self.call(nid, fn, **pins)
        return nid

    def rv(self, fn, out="ReturnValue", **pins):
        return "@%s.%s" % (self.f(fn, **pins), out)

    def br(self, cond):
        nid = self.uid("br")
        self.node(nid, "branch")
        self.pins(nid, {"Condition": cond})
        return nid

    def put(self, var, value=None, owner=None, target=None):
        nid = self.uid("set")
        self.node(nid, "set", var=var, **({"class": owner} if owner else {}))
        if target:
            self.link(unref(target), nid + ".self")
        if value is not None:
            self.pins(nid, {var: value})
        return nid

    def me(self):
        return "@" + self.self_()

    # values
    def valid(self, obj):
        return self.rv(KSL + ":IsValid", Object=obj)

    def and_(self, a, b):
        return self.rv(KML + ":BooleanAND", A=a, B=b)

    def not_(self, a):
        return self.rv(KML + ":Not_PreBool", A=a)

    def lt(self, a, b):
        return self.rv(KML + ":Less_IntInt", A=a, B=b)

    def gt(self, a, b):
        return self.rv(KML + ":Greater_IntInt", A=a, B=b)

    def eq(self, a, b):
        return self.rv(KML + ":EqualEqual_IntInt", A=a, B=b)

    def add(self, a, b):
        return self.rv(KML + ":Add_IntInt", A=a, B=b)

    def sub(self, a, b):
        return self.rv(KML + ":Subtract_IntInt", A=a, B=b)

    def mul(self, a, b):
        return self.rv(KML + ":Multiply_IntInt", A=a, B=b)

    def obj_eq(self, a, b):
        return self.rv(KML + ":EqualEqual_ObjectObject", A=a, B=b)

    def obj_ne(self, a, b):
        return self.rv(KML + ":NotEqual_ObjectObject", A=a, B=b)

    def str_eq(self, a, b):
        return self.rv(KSTR + ":EqualEqual_StrStr", A=a, B=b)

    def str_ne(self, a, b):
        return self.rv(KSTR + ":NotEqual_StrStr", A=a, B=b)

    def length(self, arr):
        return self.rv(KARR + ":Array_Length", TargetArray=arr)

    def at(self, arr, index):
        return self.rv(KARR + ":Array_Get", "Item", TargetArray=arr, Index=index)

    def as_text(self, s):
        return self.rv(KTXT + ":Conv_StringToText", InString=s)

    def int_str(self, i):
        return self.rv(KSTR + ":Conv_IntToString", InInt=i)

    def concat(self, *parts):
        acc = parts[0]
        for part in parts[1:]:
            acc = self.rv(KSTR + ":Concat_StrStr", A=acc, B=part)
        return acc

    def pick_colour(self, cond, a, b):
        """a when cond, else b (FLinearColor)."""
        return self.rv(KML + ":SelectColor", A=a, B=b, bPickA=cond)

    def pick_string(self, cond, a, b):
        return self.rv(KML + ":SelectString", A=a, B=b, bPickA=cond)

    def pick_obj(self, cond, obj, cls_):
        """obj when cond, else None."""
        nid = self.uid("sel")
        self.node(nid, "select", index="bool", type={"type": "object", "class": cls_})
        self.pins(nid, {"Index": cond, "Option 1": obj})
        return "@%s.ReturnValue" % nid

    def vis_if(self, cond, on="Visible", off="Collapsed"):
        nid = self.uid("sel")
        self.node(nid, "select", index="bool", type={"type": "enum", "class": VIS})
        self.pins(nid, {"Index": cond, "Option 0": off, "Option 1": on})
        return "@%s.ReturnValue" % nid

    def slate_colour(self, c):
        nid = self.uid("mk")
        self.node(nid, "makestruct", struct=SLATECOLOR)
        self.pins(nid, {"SpecifiedColor": c})
        return "@%s.SlateColor" % nid

    def vec2(self, x, y):
        return self.rv(KML + ":MakeVector2D", X=x, Y=y)

    # actions (return node ids)
    def set_vis(self, target, vis):
        return self.f(WIDGET + "SetVisibility", target=target, InVisibility=vis)

    def set_text(self, widget, value):
        return self.f(TEXTBLOCK + "SetText", target=self.v(widget), InText=value)

    def set_text_colour(self, widget, c):
        """c: a colour tuple (default) or a ref to an FSlateColor."""
        return self.f(TEXTBLOCK + "SetColorAndOpacity", target=self.v(widget),
                      InColorAndOpacity=c if isinstance(c, str) else slate(c))

    def set_image(self, widget, texture, match=False):
        return self.f(IMAGE + "SetBrushFromTexture", target=self.v(widget), Texture=texture,
                      bMatchSize="true" if match else "false")

    def tint(self, widget, c):
        return self.f(IMAGE + "SetColorAndOpacity", target=self.v(widget),
                      InColorAndOpacity=c if isinstance(c, str) else colour(c))

    def border_colour(self, widget, c):
        return self.f(BORDER + "SetBrushColor", target=self.v(widget),
                      InBrushColor=c if isinstance(c, str) else colour(c))

    def tooltip(self, target, tip=None):
        """SetToolTip on a widget; tip None removes it."""
        return self.f(WIDGET + "SetToolTip", target=target, **({"Widget": tip} if tip else {}))

    def make_tip(self, var):
        """Creates a DB_Tip into member var when it has none and registers it with Data (Data must be valid).
        Returns (first node, exits); link every exit to the next step with after()."""
        has = self.br(self.valid(self.v(var)))
        owner = self.rv(WIDGET + "GetOwningPlayer", target=self.me())
        create = self.f(WBL + ":Create", WidgetType=cls(TIP), OwningPlayer=owner)
        cast = self.uid("cast")
        self.cast(cast, cls(TIP), create + ".ReturnValue")
        keep = self.put(var, "@%s.$cast" % cast)
        register = self.f(cls(DATA) + ":RegisterTip", target=self.v("Data"), Tip=self.v(var))
        self.flow(has + ".else", create, cast, keep, register)
        return has, [has + ".then", register]

    def after(self, exits, node):
        for pin in exits:
            self.flow(pin, node)

    def hover_tip(self, start, subject, tip_for, tip_var, owner, fill):
        """Tooltip on hover. start: the hover event (node id). subject: member var of what the tip shows; tip_for:
        member var of what it was filled for; owner: the widget that gets the tooltip; fill(tip_var) -> node ids
        that fill the tip, in order. Nothing without a subject or Data. The tip is made on the first hover and
        refilled when the subject changed. On every hover it is made visible again (Data.HideTips collapses
        tips) and gets the more-info setting (Data.MoreInfo)."""
        shown = self.br(self.and_(self.valid(self.v(subject)), self.valid(self.v("Data"))))
        changed = self.br(self.obj_ne(self.v(subject), self.v(tip_for)))
        first, made = self.make_tip(tip_var)
        steps = fill(tip_var)
        visible = self.set_vis(self.v(tip_var), "HitTestInvisible")
        more = self.f(cls(DATA) + ":MoreInfo", target=self.v("Data"))
        extra = self.f(cls(TIP) + ":ShowExtra", target=self.v(tip_var), On="@%s.On" % more)
        self.flow(start, shown, changed, first)
        self.after(made, steps[0])
        self.flow(*steps, self.tooltip(owner, self.v(tip_var)), self.put(tip_for, self.v(subject)), visible)
        self.flow(changed + ".else", visible)
        self.flow(visible, more, extra)


def tip_fill(g, var, title, category, body, accent, icon):
    return g.f(cls(TIP) + ":Set", target=g.v(var), Title=title, Category=category, Body=body, Accent=accent, Icon=icon)


def tip_extra(g, var, title=None, extra=None):
    """SetExtra on a tip; no texts = no "more info" box."""
    return g.f(cls(TIP) + ":SetExtra", target=g.v(var), ExtraTitle=title, Extra=extra)


# ----------------------------------------------------------------------------- DB_Tip

def tip_tree():
    """480 wide: orange rules top and bottom; 64x64 icon tile, title and category; body text. Then, as in the
    game's upgrade tooltip, the "more info" box (a darker inner panel: Carbon title, body text) and a footer
    "MORE INFO" / "LESS INFO" with the key E; both collapsed until SetExtra gives a text."""
    title = text("TitleText", "Title", RIFT, F_TIP_TITLE, ORANGE, var=True)
    props(title, WrapTextAt=str(TIP_W - 32 - TIP_TILE - 14))
    category = text("CategoryText", "CATEGORY", CARBON, F_TIP_CAT, WHITE, var=True, slot=vslot(pad=(0, 2, 0, 0)))
    body = text("BodyText", "", BODY, F_TIP_BODY, LIGHT, var=True, slot=vslot(pad=(16, 12, 16, 0)))
    props(body, WrapTextAt=str(TIP_W - 32))
    icon = TIP_TILE - 20
    tile = box("TileBox", TIP_TILE, TIP_TILE, var=True, slot=hslot(valign="VAlign_Center"), child=overlay("Tile", [
        image("TileBg", ORANGE, var=True, slot=oslot()),
        w("ScaleBox", "TileScale", props={"Stretch": "ScaleToFit"}, slot=oslot(pad=(10, 10, 10, 10)), children=[
            image("TipIcon", INK, size=(icon, icon), var=True, slot=oslot("HAlign_Center", "VAlign_Center"))]),
    ]))
    head = hbox("Head", [tile, vbox("Titles", [title, category], slot=hslot(True, (14, 0, 0, 0)))],
                slot=vslot(pad=(16, 12, 16, 0)))
    # More info box: 448 wide, 10 px inside, so its text wraps at 428.
    extra_title = text("ExtraTitleText", "", CARBON, F_TIP_EXTRA_TITLE, WHITE, var=True, upper=True, slot=vslot())
    extra_body = text("ExtraBodyText", "", BODY, F_TIP_EXTRA, LIGHT, var=True, slot=vslot(pad=(0, 4, 0, 0)))
    props(extra_body, WrapTextAt=str(TIP_W - 32 - 20))
    extra = props(border("ExtraBox", EXTRA_BG, var=True, pad=(10, 8, 10, 10), slot=vslot(pad=(16, 12, 16, 0)),
                         child=vbox("ExtraRows", [extra_title, extra_body])), Visibility="Collapsed")
    more = capbox("MoreBox", text("MoreText", "MORE INFO", CARBON, F_TIP_MORE, ORANGE, var=True), CARBON,
                  F_TIP_MORE, TIP_KEY, slot=hslot())
    key_text = text("KeyText", "E", CARBON, F_TIP_KEY, BLACK_TEXT, justify="Center")
    key_text["slot"] = fit_slot(CARBON, F_TIP_KEY, TIP_KEY, halign="HAlign_Center")
    key = box("KeyBox", TIP_KEY, TIP_KEY, slot=hslot(pad=(8, 0, 0, 0)), child=overlay("Key", [
        image("KeyBg", WHITE, slot=oslot()), key_text]))
    footer = props(hbox("Footer", [more, key], var=True, slot=vslot(pad=(16, 10, 16, 0))), Visibility="Collapsed")
    bottom = rule("RuleBottom")
    bottom["slot"] = vslot(pad=(0, 14, 0, 0))
    rows = vbox("Rows", [rule("RuleTop"), head, body, extra, footer, bottom])
    return deco(box("Root", width=TIP_W, child=border("Panel", TIP_BG, child=rows)))


def tip_members():
    return {"variables": [
        t("HasExtra", "bool"),   # SetExtra got a text
        t("ExtraOn", "bool"),    # ShowExtra(On)
    ], "functions": [{"name": "ApplyExtra"}]}


def g_tip_set():
    g = G()
    empty = g.rv(KTXT + ":TextIsEmpty", InText="@entry.Body")
    steps = [
        g.set_text("TitleText", "@entry.Title"),
        g.set_text("CategoryText", "@entry.Category"),
        g.set_text("BodyText", "@entry.Body"),
        g.set_vis(g.v("BodyText"), g.vis_if(g.not_(empty), "HitTestInvisible", "Collapsed")),
    ]
    has_icon = g.br(g.valid("@entry.Icon"))
    show = [g.set_image("TipIcon", "@entry.Icon", match=True), g.tint("TileBg", "@entry.Accent"),
            g.set_vis(g.v("TileBox"), "HitTestInvisible")]
    g.flow("entry", *steps, has_icon, *show)
    g.flow(has_icon + ".else", g.set_vis(g.v("TileBox"), "Collapsed"))
    return g.data()


def g_tip_set_extra():
    """Texts of the more-info box. Set does not touch them."""
    g = G()
    title_empty = g.rv(KTXT + ":TextIsEmpty", InText="@entry.ExtraTitle")
    g.flow("entry",
           g.put("HasExtra", g.not_(g.rv(KTXT + ":TextIsEmpty", InText="@entry.Extra"))),
           g.set_text("ExtraTitleText", "@entry.ExtraTitle"),
           g.set_vis(g.v("ExtraTitleText"), g.vis_if(g.not_(title_empty), "HitTestInvisible", "Collapsed")),
           g.set_text("ExtraBodyText", "@entry.Extra"),
           g.f("ApplyExtra"))
    return g.data()


def g_tip_show_extra():
    g = G()
    g.flow("entry", g.put("ExtraOn", "@entry.On"), g.f("ApplyExtra"))
    return g.data()


def g_tip_apply_extra():
    """Box shown when there is a text and more info is on; footer shown when there is a text."""
    g = G()
    on = g.and_(g.v("HasExtra"), g.v("ExtraOn"))
    g.flow("entry",
           g.set_vis(g.v("ExtraBox"), g.vis_if(on, "HitTestInvisible", "Collapsed")),
           g.set_vis(g.v("Footer"), g.vis_if(g.v("HasExtra"), "HitTestInvisible", "Collapsed")),
           g.set_text("MoreText", g.as_text(g.pick_string(g.v("ExtraOn"), "LESS INFO", "MORE INFO"))))
    return g.data()


# ----------------------------------------------------------------------------- DB_UpgCell

def cell_tree():
    """Hexagon: background and outline textures (Data.HexBg / HexOutline), category icon on top. Fills its box.
    Until Data has loaded the textures, a plain coloured box."""
    return overlay("Root", [
        deco(image("HexBg", EMPTY_BG, var=True, slot=oslot())),
        props(deco(image("HexLine", EMPTY_LINE, var=True, slot=oslot())), Visibility="Collapsed"),
        props(deco(image("Icon", INK, size=(CELL_ICON, CELL_ICON), var=True, slot=oslot("HAlign_Center", "VAlign_Center"))),
              Visibility="Collapsed"),
    ])


def cell_members():
    return {"variables": [
        t("CellUpgrade", "object", UPGRADE), t("CellSelected", "bool"),
        t("HexDone", "bool"),   # the hexagon textures are on the images
        t("IconPx", "float", default=str(CELL_ICON)),   # icon size, the same in weapon and gear cards
        t("IconTex", "object", TEXTURE),
        t("CellTip", "object", cls(TIP)), t("TipFor", "object", UPGRADE),
    ], "functions": []}


def g_cell_set():
    g = G()
    upgrade = "@entry.Upgrade"
    keep = [g.put("CellUpgrade", upgrade), g.put("CellSelected", "@entry.Selected")]
    has = g.valid(upgrade)
    chosen = g.and_(has, "@entry.Selected")
    paint = [
        g.tint("HexBg", g.pick_colour(has, g.pick_colour(chosen, colour(SEL_BG), colour(OFF_BG)), colour(EMPTY_BG))),
        g.tint("HexLine", g.pick_colour(has, g.pick_colour(chosen, colour(SEL_LINE), colour(OFF_LINE)), colour(EMPTY_LINE))),
    ]
    # Hexagon textures: taken from Data once both are loaded (checked on every Set until then).
    need = g.br(g.not_(g.v("HexDone")))
    has_data = g.br(g.valid(g.v("Data")))
    hex_bg = g.v("HexBg", cls(DATA), g.v("Data"))
    hex_line = g.v("HexOutline", cls(DATA), g.v("Data"))
    loaded = g.br(g.and_(g.valid(hex_bg), g.valid(hex_line)))
    put_hex = [g.set_image("HexBg", hex_bg), g.set_image("HexLine", hex_line),
               g.set_vis(g.v("HexLine"), "HitTestInvisible"), g.put("HexDone", "true")]
    g.flow("entry", *keep, need, has_data, loaded, *put_hex, paint[0])
    g.after([need + ".else", has_data + ".else", loaded + ".else"], paint[0])
    g.flow(*paint)

    # Icon: the upgrade's category icon; Data.UpgradeTip only when the category has none.
    br_has = g.br(has)
    category = g.v("Category", UPGRADE, upgrade)
    br_cat = g.br(g.valid(category))
    icon_cat = g.put("IconTex", g.v("CategoryIcon", CATEGORY, g.v("Category", UPGRADE, upgrade)))
    icon_none = g.put("IconTex")
    br_tex = g.br(g.valid(g.v("IconTex")))
    br_data = g.br(g.valid(g.v("Data")))
    tip = g.f(cls(DATA) + ":UpgradeTip", target=g.v("Data"), Upgrade=upgrade)
    icon_tip = g.put("IconTex", "@%s.Icon" % tip)
    show = [g.set_image("Icon", g.v("IconTex")),
            g.f(IMAGE + "SetBrushSize", target=g.v("Icon"), DesiredSize=g.vec2(g.v("IconPx"), g.v("IconPx"))),
            g.tint("Icon", g.pick_colour("@entry.Selected", colour(SEL_ICON), colour(OFF_ICON))),
            g.set_vis(g.v("Icon"), g.vis_if(g.valid(g.v("IconTex")), "HitTestInvisible", "Collapsed"))]
    hide = g.set_vis(g.v("Icon"), "Collapsed")
    g.flow(paint[-1], br_has, br_cat, icon_cat, br_tex)
    g.flow(br_cat + ".else", icon_none, br_tex)
    g.flow(br_tex + ".then", show[0])
    g.flow(br_tex + ".else", br_data, tip, icon_tip, show[0])
    g.flow(br_data + ".else", show[0])
    g.flow(*show)
    g.flow(br_has + ".else", hide)

    # A tooltip made for another upgrade is dropped; the next hover makes it again.
    stale = g.br(g.and_(g.valid(g.v("TipFor")), g.obj_ne(g.v("TipFor"), upgrade)))
    drop = [g.tooltip(g.me()), g.put("TipFor")]
    g.flow(show[-1], stale, *drop)
    g.flow(hide, stale)
    return g.data()


def g_cell_events():
    """Upgrade tooltip with the category's more-info box."""
    g = G()
    g.node("enter", "event", name="OnMouseEnter", **{"class": USERWIDGET})

    def fill(tip_var):
        tip = g.f(cls(DATA) + ":UpgradeTip", target=g.v("Data"), Upgrade=g.v("CellUpgrade"))
        out = lambda pin: "@%s.%s" % (tip, pin)  # noqa: E731
        return [tip, tip_fill(g, tip_var, out("Title"), out("Category"), out("Body"), colour(ORANGE), out("Icon")),
                tip_extra(g, tip_var, out("ExtraTitle"), out("Extra"))]
    g.hover_tip("enter", "CellUpgrade", "TipFor", "CellTip", g.me(), fill)
    return g.data()


# ----------------------------------------------------------------------------- DB_PerkTile

def perk_tree():
    """40x40 tile: 28 px perk icon on the perk type colour (passive red, active green, proficiency orange); a dark
    rim around a darker inside when empty. The same size for every kind."""
    icon = props(deco(image("Icon", INK, size=(PERK_ICON, PERK_ICON), var=True)), Visibility="Collapsed")
    fill = border("Fill", EMPTY_FILL, child=icon, var=True, halign="HAlign_Center", valign="VAlign_Center")
    return box("Root", TILE, TILE, child=border("Frame", EMPTY_FRAME, child=fill, pad=(1, 1, 1, 1), var=True))


def perk_members():
    return {"variables": [
        t("TilePerk", "object", PERKASSET), t("TileRank", "int"),
        t("TileTip", "object", cls(TIP)), t("TipFor", "object", PERKASSET), t("TipRank", "int"),
    ], "functions": []}


def g_perk_set():
    """Draws only the perk icon and the type colour. The tooltip texts (Data.PerkTip) are made on hover."""
    g = G()
    perk, rank = "@entry.Perk", "@entry.Rank"
    keep = [g.put("TilePerk", perk), g.put("TileRank", rank)]
    known = g.br(g.valid(perk))
    icon = g.v("Icon", PERKASSET, perk)
    passive = g.rv(PERKASSET + ":IsUsageType", target=perk, InType="Passive")
    active = g.rv(PERKASSET + ":IsUsageType", target=perk, InType="Active")
    # Passive, active, else proficiency (the game's third kind).
    tone = g.pick_colour(passive, colour(PERK_PASSIVE), g.pick_colour(active, colour(PERK_ACTIVE), colour(PERK_PROF)))
    full = [g.border_colour("Frame", tone), g.border_colour("Fill", tone), g.set_image("Icon", icon),
            g.set_vis(g.v("Icon"), g.vis_if(g.valid(icon), "HitTestInvisible", "Collapsed"))]
    empty = [g.border_colour("Frame", EMPTY_FRAME), g.border_colour("Fill", EMPTY_FILL),
             g.set_vis(g.v("Icon"), "Collapsed")]
    changed = g.and_(g.valid(g.v("TipFor")),
                     g.rv(KML + ":BooleanOR", A=g.obj_ne(g.v("TipFor"), perk), B=g.rv(KML + ":NotEqual_IntInt",
                                                                                   A=g.v("TipRank"), B=rank)))
    stale = g.br(changed)
    g.flow("entry", *keep, known, *full, stale, g.tooltip(g.me()), g.put("TipFor"))
    g.flow(known + ".else", *empty, stale)
    return g.data()


def g_perk_events():
    """Perk tooltip. Set clears TipFor when the perk or rank changed, so the tip is refilled only then."""
    g = G()
    g.node("enter", "event", name="OnMouseEnter", **{"class": USERWIDGET})

    def fill(tip_var):
        tip = g.f(cls(DATA) + ":PerkTip", target=g.v("Data"), Perk=g.v("TilePerk"), Rank=g.v("TileRank"))
        out = lambda pin: "@%s.%s" % (tip, pin)  # noqa: E731
        return [tip, tip_fill(g, tip_var, out("Title"), out("Category"), out("Body"), out("Color"), out("Icon")),
                tip_extra(g, tip_var), g.put("TipRank", g.v("TileRank"))]
    g.hover_tip("enter", "TilePerk", "TipFor", "TileTip", g.me(), fill)
    return g.data()


# ----------------------------------------------------------------------------- DB_WeaponCard

TRANSPARENT = dict(normal=NO_DRAW, hovered=NO_DRAW, pressed=NO_DRAW, disabled=NO_DRAW)


def silhouette(name, width, height, var=True, slot=None, halign="HAlign_Left"):
    """Item picture: the Line texture in orange over the Fill texture at 30 %, scaled to fit the box."""
    return box(name + "Box", width, height, var=var, slot=slot, child=w(
        "ScaleBox", name + "Scale", props={"Stretch": "ScaleToFit"}, children=[overlay(name, [
            deco(image(name + "Fill", (ORANGE[0], ORANGE[1], ORANGE[2], 0.3), var=True, slot=oslot())),
            deco(image(name + "Line", ORANGE, var=True, slot=oslot())),
        ], slot=oslot(halign, "VAlign_Center"))]))


def grid_rows(cell_prefix, box_prefix, link_prefix, tiers):
    """Upgrade grid rows: `tiers` rows of 3 hidden cells (CELL_W x CELL_H), cell [tier, option] named
    cell_prefix + "<tier><option>". The same in weapon and gear cards.
    Behind the cells, as in the game, a LINK_H dark line joins the options of a row: link [tier, option] (named
    link_prefix + "<tier><option>", hidden) runs from the centre of the option before to this option's centre, so
    it is shown with its cell. Link [tier, 0] is 0 wide (it draws nothing) and only keeps the index the cell's."""
    def cell(tier, option):
        node = w(cls(CELL), "%s%d%d" % (cell_prefix, tier, option), True, {"Visibility": "Hidden"})
        return box("%s%d%d" % (box_prefix, tier, option), CELL_W, CELL_H, child=node,
                   slot=hslot(pad=(CELL_GAP_X if option else 0, 0, 0, 0)))

    def link(tier, option):
        width = CELL_W + CELL_GAP_X if option else 0
        node = deco(image("%s%d%d" % (link_prefix, tier, option), LINK, size=(width, LINK_H), var=True,
                          slot=hslot(pad=(CELL_W / 2 if option == 1 else 0, 0, 0, 0))))
        return props(node, Visibility="Hidden")

    def row(tier):
        links = hbox("Links%d" % tier, [link(tier, option) for option in range(3)],
                     slot=oslot("HAlign_Left", "VAlign_Center"))
        cells = hbox("Cells%d" % tier, [cell(tier, option) for option in range(3)], slot=oslot())
        return overlay("Tier%d" % tier, [links, cells], slot=vslot(pad=(0, CELL_GAP_Y if tier else 0, 0, 0)))
    return [row(tier) for tier in range(tiers)]


def card_tree():
    """418x210: name on top (the full width); category line, silhouette and overclock left; 5x3 upgrade grid right.
    210 = rule 3 + 6 + top row 28 + 4 + main 161 (the grid's height: 5 x 29 + 4 x 4) + 8.
    Main is 394 wide: left 240 | 12 | grid 142 (3 x 44 + 2 x 5). Left: category 15 (Carbon, as the game's
    "PISTOL" under the name), silhouette 240x92, 10, overclock row 44, so the overclock row ends level with the
    last tier row."""
    name = clipped(text("NameText", "ITEM", RIFT, F_CARD_NAME, WHITE, var=True))
    name["slot"] = fit_slot(RIFT, F_CARD_NAME, CARD_TOP_H)
    top = box("TopBox", height=CARD_TOP_H, slot=vslot(pad=(12, 6, 12, 0)),
              child=button("NameBtn", name, slot=content_slot(), **TRANSPARENT))
    category = capbox("CatBox", clipped(text("CatText", "", CARBON, F_CARD_CAT, DIM, var=True, upper=True)),
                      CARBON, F_CARD_CAT, CARD_CAT_H, top=CARD_CAT_TOP, slot=vslot())
    sil = silhouette("Sil", SIL_W, SIL_H, slot=vslot(halign="HAlign_Left"))
    oc_icon = box("OcBox", OC_BOX, OC_BOX, slot=hslot(), child=overlay("OcStack", [
        deco(image("OcFrame", EMPTY_TILE, var=True, slot=oslot())),
        props(deco(image("OcIcon", WHITE, size=(OC_ICON, OC_ICON), var=True,
                         slot=oslot("HAlign_Center", "VAlign_Center"))), Visibility="Collapsed"),
    ]))
    # Name 24 + type 16 = 40, centred in the 44 row; without an overclock the type box collapses.
    oc_texts = vbox("OcTexts", [
        capbox("OcNameBox", clipped(text("OcName", "NO OVERCLOCK", RIFT, F_OC_NAME, DIM, var=True)),
               RIFT, F_OC_NAME, 24),
        props(capbox("OcTypeBox", clipped(text("OcType", "", CARBON, F_OC_TYPE, WHITE, var=True)),
                     CARBON, F_OC_TYPE, 16, var=True), Visibility="Collapsed"),
    ], slot=hslot(True, (10, 0, 0, 0)))
    oc_row = hbox("OcRow", [oc_icon, oc_texts])
    oc_row["slot"] = content_slot("HAlign_Fill", "VAlign_Center")
    # Left fills the main height, so LeftGap pushes the overclock row down, level with the last tier row.
    left = vbox("Left", [
        category,
        sil,
        w("Spacer", "LeftGap", slot=vslot(True)),
        button("OcBtn", oc_row, slot=vslot(), **TRANSPARENT),
    ], slot=fill_slot(1))
    grid = vbox("Grid", grid_rows("C", "CellBox", "L", 5), slot=hslot(pad=(12, 0, 0, 0), valign="VAlign_Top"))
    main = hbox("Main", [left, grid], slot=vslot(True, (12, 4, 12, 8)))
    body = vbox("Body", [rule("Rule"), top, main])
    assert 3 + 6 + CARD_TOP_H + 4 + (5 * CELL_H + 4 * CELL_GAP_Y) + 8 == CARD_H
    assert CARD_CAT_H + SIL_H + 10 + OC_BOX == 5 * CELL_H + 4 * CELL_GAP_Y
    assert SIL_W + 12 + GRID_W + 2 * 12 == COL_W
    return box("Root", COL_W, CARD_H, child=border("Bg", PANEL, child=body))


def card_members():
    return {"variables": [
        t("CellList", "object", cls(CELL), array=True),
        t("LinkList", "object", UMG + "Image", array=True),   # tier row lines, the same index as CellList
        t("TierOpts", "object", UPGRADE, array=True),
        t("CardItem", "object", ITEMID), t("CardOc", "object", OVERCLOCK),
        t("OcTitle", "text"), t("OcCategory", "text"), t("OcBody", "text"), t("OcIconTex", "object", TEXTURE),
        t("OcColor", "struct", LINEAR), t("OcFrameTex", "object", TEXTURE),
        t("OcShown", "object", OVERCLOCK),   # the overclock last drawn
        t("ItemTip", "object", cls(TIP)), t("ItemTipFor", "object", ITEMID),
        t("OcTip", "object", cls(TIP)), t("OcTipFor", "object", OVERCLOCK),
    ], "functions": [
        {"name": "EnsureCells"},
        {"name": "ShowOverclock"},
        {"name": "ShowGrid", "inputs": [t("GridItem", "object", ITEMID), t("GridChoices", "int", array=True)]},
    ]}


def g_card_ensure():
    """The 15 cells and their row lines as arrays (tier * 3 + option), made on the first Show."""
    g = G()
    empty = g.br(g.eq(g.length(g.v("CellList")), "0"))
    g.node("cells", "makearray", n=15)
    g.node("links", "makearray", n=15)
    for i in range(15):
        g.link(unref(g.v("C%d%d" % (i // 3, i % 3))), "cells.[%d]" % i)
        g.link(unref(g.v("L%d%d" % (i // 3, i % 3))), "links.[%d]" % i)
    g.flow("entry", empty, g.put("CellList", "@cells.Array"), g.put("LinkList", "@links.Array"))
    return g.data()


def g_card_show():
    """The contract's Digits input is not shown (the tier digits were removed)."""
    g = G()
    item, oc = "@entry.Item", "@entry.Overclock"
    # Tooltips made for another item or overclock are dropped.
    old_item = g.br(g.and_(g.valid(g.v("ItemTipFor")), g.obj_ne(g.v("ItemTipFor"), item)))
    drop_item = [g.tooltip(g.v("NameBtn")), g.put("ItemTipFor")]
    old_oc = g.br(g.and_(g.valid(g.v("OcTipFor")), g.obj_ne(g.v("OcTipFor"), oc)))
    drop_oc = [g.tooltip(g.v("OcBtn")), g.put("OcTipFor")]
    head = [g.f("EnsureCells"), g.put("CardItem", item), g.put("CardOc", oc), old_item]
    g.flow("entry", *head, *drop_item, old_oc, *drop_oc)
    g.flow(old_item + ".else", old_oc)

    known = g.br(g.and_(g.valid(item), g.valid(g.v("Data"))))
    g.flow(drop_oc[-1], known)
    g.flow(old_oc + ".else", known)

    visual = g.f(cls(DATA) + ":ItemVisual", target=g.v("Data"), Item=item)
    line = "@%s.Line" % visual
    shown = [visual,
             g.set_text("NameText", "@%s.Name" % visual), g.set_text_colour("NameText", WHITE),
             g.set_text("CatText", "@%s.Category" % visual),
             g.set_image("SilFill", "@%s.Fill" % visual, match=True), g.set_image("SilLine", line, match=True),
             g.set_vis(g.v("SilBox"), g.vis_if(g.valid(line), "HitTestInvisible", "Hidden")),
             g.set_vis(g.v("OcBtn"), "Visible"),
             g.f("ShowOverclock"),
             g.f("ShowGrid", GridItem=item, GridChoices="@entry.Choices")]
    g.flow(known + ".then", *shown)

    # Unknown slot: name UNKNOWN, no category, every cell an empty dim hexagon, no row lines.
    unknown = [g.set_text("NameText", "UNKNOWN"), g.set_text_colour("NameText", DIM), g.set_text("CatText", ""),
               g.set_vis(g.v("SilBox"), "Hidden"), g.set_vis(g.v("OcBtn"), "Hidden")]
    cell = g.loop("eachCell", unref(g.v("CellList")))
    dim = [g.put("Data", g.v("Data"), cls(CELL), cell), g.set_vis("@" + cell, "Visible"),
           g.set_vis(g.at(g.v("LinkList"), "@eachCell.Array Index"), "Hidden"),
           g.f(cls(CELL) + ":Set", target="@" + cell, Selected="false")]
    g.flow(known + ".else", *unknown, "eachCell.Exec")
    g.flow("eachCell.LoopBody", *dim)
    return g.data()


def g_card_overclock():
    """One Data.OverclockTip call draws the overclock; its texts are kept for the tooltip. The overclock drawn last
    is not fetched again while its frame is there (a missing frame is retried: it may still be loading)."""
    g = G()
    oc = g.v("CardOc")
    same = g.br(g.and_(g.obj_eq(g.v("CardOc"), g.v("OcShown")), g.valid(g.v("OcFrameTex"))))
    has = g.br(g.and_(g.valid(oc), g.valid(g.v("Data"))))
    tip = g.f(cls(DATA) + ":OverclockTip", target=g.v("Data"), Overclock=g.v("CardOc"))
    out = lambda pin: "@%s.%s" % (tip, pin)  # noqa: E731
    keep = [tip, g.put("OcTitle", out("Title")), g.put("OcCategory", out("Category")), g.put("OcBody", out("Body")),
            g.put("OcIconTex", out("Icon")), g.put("OcColor", out("Color")), g.put("OcFrameTex", out("Frame")),
            g.put("OcShown", g.v("CardOc"))]
    # With a frame texture: the frame in the type colour and a white icon; without: a plain tile and a dark icon.
    framed = g.valid(g.v("OcFrameTex"))
    shown = [g.set_text("OcName", g.v("OcTitle")), g.set_text_colour("OcName", WHITE),
             g.set_text("OcType", g.v("OcCategory")), g.set_text_colour("OcType", g.slate_colour(g.v("OcColor"))),
             g.set_vis(g.v("OcTypeBox"), "HitTestInvisible"),
             g.set_image("OcFrame", g.v("OcFrameTex")), g.tint("OcFrame", g.v("OcColor")),
             g.set_image("OcIcon", g.v("OcIconTex")),
             g.tint("OcIcon", g.pick_colour(framed, colour(WHITE), colour(INK))),
             g.set_vis(g.v("OcIcon"), g.vis_if(g.valid(g.v("OcIconTex")), "HitTestInvisible", "Collapsed"))]
    none = [g.set_text("OcName", "NO OVERCLOCK"), g.set_text_colour("OcName", DIM), g.set_text("OcType", ""),
            g.set_vis(g.v("OcTypeBox"), "Collapsed"), g.set_image("OcFrame", None), g.tint("OcFrame", EMPTY_TILE),
            g.set_vis(g.v("OcIcon"), "Collapsed"), g.put("OcShown"), g.put("OcFrameTex")]
    g.flow("entry", same)
    g.flow(same + ".else", has, *keep, *shown)
    g.flow(has + ".else", *none)
    return g.data()


def g_card_grid():
    """Cell [tier, option] and its row line: hidden when the tier or option does not exist; the cell is chosen
    when Choices[tier] = option + 1."""
    g = G()
    g.for_range("tiers", "0", "4")
    tier = "@tiers.Index"
    br_tier = g.br(g.lt(tier, g.length("@entry.GridChoices")))
    options = g.f(cls(DATA) + ":TierOptions", target=g.v("Data"), Item="@entry.GridItem", Tier=tier)
    keep = g.put("TierOpts", "@%s.Upgrades" % options)
    clear = g.f(KARR + ":Array_Clear", TargetArray=g.v("TierOpts"))
    g.for_range("options", "0", "2")
    option = "@options.Index"
    index = g.add(g.mul(tier, "3"), option)
    cell, link = g.at(g.v("CellList"), index), g.at(g.v("LinkList"), index)
    br_opt = g.br(g.lt(option, g.length(g.v("TierOpts"))))
    chosen = g.eq(g.at("@entry.GridChoices", tier), g.add(option, "1"))
    show = [g.put("Data", g.v("Data"), cls(CELL), cell), g.set_vis(cell, "Visible"),
            g.set_vis(link, "HitTestInvisible"),
            g.f(cls(CELL) + ":Set", target=cell, Upgrade=g.at(g.v("TierOpts"), option), Selected=chosen)]
    g.flow("entry", "tiers.execute")
    g.flow("tiers.LoopBody", br_tier, options, keep, "options.execute")
    g.flow(br_tier + ".else", clear, "options.execute")
    g.flow("options.LoopBody", br_opt, *show)
    g.flow(br_opt + ".else", g.set_vis(cell, "Hidden"), g.set_vis(link, "Hidden"))
    return g.data()


def item_tip_fill(g, item_var):
    """fill() for hover_tip: the item tooltip of member var item_var (no more-info box)."""
    def fill(tip_var):
        tip = g.f(cls(DATA) + ":ItemTip", target=g.v("Data"), Item=g.v(item_var))
        out = lambda pin: "@%s.%s" % (tip, pin)  # noqa: E731
        return [tip, tip_fill(g, tip_var, out("Title"), out("Category"), out("Body"), colour(ORANGE), out("Icon")),
                tip_extra(g, tip_var)]
    return fill


def g_card_events():
    """Item and overclock tooltips, made on the first hover."""
    g = G()
    g.node("nameHover", "boundevent", widget="NameBtn", name="OnHovered")
    g.hover_tip("nameHover", "CardItem", "ItemTipFor", "ItemTip", g.v("NameBtn"), item_tip_fill(g, "CardItem"))

    g.node("ocHover", "boundevent", widget="OcBtn", name="OnHovered")

    def oc_fill(tip_var):
        return [tip_fill(g, tip_var, g.v("OcTitle"), g.v("OcCategory"), g.v("OcBody"), g.v("OcColor"),
                         g.v("OcIconTex")),
                tip_extra(g, tip_var)]
    g.hover_tip("ocHover", "CardOc", "OcTipFor", "OcTip", g.v("OcBtn"), oc_fill)
    return g.data()


# ----------------------------------------------------------------------------- DB_GearRow (a gear card)

def gear_tree():
    """Gear card 206x188 (traversal, support, armor or grenade): label, item name, then the upgrade grid exactly
    like the weapon card's (up to 4 tiers x 3 options, cells 44x29, grid 142x128), all left aligned 12 px from the
    edge. An item with no tiers (grenade) shows its picture there instead (142x128, left aligned), with the item
    tooltip on hover. 188 = rule 3 + label 19 + name 24 + 2 + grid 128 + 12; 182 wide inside (12 each side)."""
    pad = GEAR_PAD
    label = capbox("LabelBox", text("LabelText", "", CARBON, F_GEAR_LABEL, DIM, var=True), CARBON, F_GEAR_LABEL,
                   GEAR_LABEL_H, top=GEAR_LABEL_TOP, slot=vslot(pad=(pad, 0, pad, 0)))
    name = capbox("NameBox", clipped(text("NameText", "", RIFT, F_GEAR_NAME, WHITE, var=True)), RIFT, F_GEAR_NAME,
                  GEAR_NAME_H, top=GEAR_NAME_TOP, slot=vslot(pad=(pad, 0, pad, 0)))
    grid = props(vbox("Grid", grid_rows("G", "GBox", "GL", GEAR_TIERS), var=True), Visibility="Hidden")
    grid["slot"] = oslot("HAlign_Left", "VAlign_Top")
    pic = silhouette("Pic", GRID_W, GEAR_BODY_H, var=False, halign="HAlign_Left")
    pic["slot"] = content_slot()
    pic_btn = props(button("PicBtn", pic, slot=oslot("HAlign_Left", "VAlign_Top"), **TRANSPARENT),
                    Visibility="Collapsed")
    body = box("BodyBox", height=GEAR_BODY_H, slot=vslot(pad=(pad, GEAR_GRID_TOP, pad, 0)),
               child=overlay("BodyStack", [grid, pic_btn]))
    rows = vbox("Rows", [rule("Rule"), label, name, body])
    assert 3 + GEAR_LABEL_H + GEAR_NAME_H + GEAR_GRID_TOP + GEAR_BODY_H + pad == GEAR_H
    assert GRID_W <= GEAR_W - 2 * pad
    return box("Root", GEAR_W, GEAR_H, child=border("Bg", PANEL, child=rows))


def gear_members():
    return {"variables": [
        t("GearCellList", "object", cls(CELL), array=True),
        t("GearLinkList", "object", UMG + "Image", array=True),   # tier row lines, the same index as GearCellList
        t("GearOpts", "object", UPGRADE, array=True),
        t("GearItem", "object", ITEMID),
        t("ItemTip", "object", cls(TIP)), t("ItemTipFor", "object", ITEMID),
    ], "functions": []}


def g_gear_show():
    """Label and name; then the tier grid (cell [tier, option] hidden when the tier or option does not exist, chosen
    when Choices[tier] = option + 1), or the picture for an item with no tiers. Unknown item: UNKNOWN, nothing else."""
    g = G()
    item = "@entry.Item"
    # The 12 cells and their row lines as arrays (tier * 3 + option), made on the first Show.
    first = g.br(g.eq(g.length(g.v("GearCellList")), "0"))
    g.node("cells", "makearray", n=GEAR_TIERS * 3)
    g.node("links", "makearray", n=GEAR_TIERS * 3)
    for i in range(GEAR_TIERS * 3):
        g.link(unref(g.v("G%d%d" % (i // 3, i % 3))), "cells.[%d]" % i)
        g.link(unref(g.v("GL%d%d" % (i // 3, i % 3))), "links.[%d]" % i)
    keep = [g.put("GearCellList", "@cells.Array"), g.put("GearLinkList", "@links.Array")]
    store = g.put("GearItem", item)
    # A tooltip made for another item is dropped.
    old = g.br(g.and_(g.valid(g.v("ItemTipFor")), g.obj_ne(g.v("ItemTipFor"), item)))
    drop = [g.tooltip(g.v("PicBtn")), g.put("ItemTipFor")]
    label = g.set_text("LabelText", g.as_text("@entry.Label"))
    g.flow("entry", first, *keep, store)
    g.flow(first + ".else", store)
    g.flow(store, old, *drop, label)
    g.flow(old + ".else", label)

    br_known = g.br(g.and_(g.valid(item), g.valid(g.v("Data"))))
    visual = g.f(cls(DATA) + ":ItemVisual", target=g.v("Data"), Item=item)
    named = [visual, g.set_text("NameText", "@%s.Name" % visual), g.set_text_colour("NameText", WHITE)]
    br_tiers = g.br(g.gt(g.length("@entry.Choices"), "0"))
    grid_on = [g.set_vis(g.v("PicBtn"), "Collapsed"), g.set_vis(g.v("Grid"), "SelfHitTestInvisible")]
    line = "@%s.Line" % visual
    pic_on = [g.set_vis(g.v("Grid"), "Hidden"),
              g.set_image("PicFill", "@%s.Fill" % visual, match=True), g.set_image("PicLine", line, match=True),
              g.set_vis(g.v("PicBtn"), g.vis_if(g.valid(line), "Visible", "Collapsed"))]
    unknown = [g.set_text("NameText", "UNKNOWN"), g.set_text_colour("NameText", DIM),
               g.set_vis(g.v("Grid"), "Hidden"), g.set_vis(g.v("PicBtn"), "Collapsed")]
    g.flow(label, br_known, *named, br_tiers, *grid_on, "tiers.execute")
    g.flow(br_tiers + ".else", *pic_on)
    g.flow(br_known + ".else", *unknown)

    g.for_range("tiers", "0", str(GEAR_TIERS - 1))
    tier = "@tiers.Index"
    br_tier = g.br(g.lt(tier, g.length("@entry.Choices")))
    options = g.f(cls(DATA) + ":TierOptions", target=g.v("Data"), Item=item, Tier=tier)
    keep_opts = g.put("GearOpts", "@%s.Upgrades" % options)
    clear = g.f(KARR + ":Array_Clear", TargetArray=g.v("GearOpts"))
    g.for_range("options", "0", "2")
    option = "@options.Index"
    index = g.add(g.mul(tier, "3"), option)
    cell, link = g.at(g.v("GearCellList"), index), g.at(g.v("GearLinkList"), index)
    br_opt = g.br(g.lt(option, g.length(g.v("GearOpts"))))
    chosen = g.eq(g.at("@entry.Choices", tier), g.add(option, "1"))
    show = [g.put("Data", g.v("Data"), cls(CELL), cell), g.set_vis(cell, "Visible"),
            g.set_vis(link, "HitTestInvisible"),
            g.f(cls(CELL) + ":Set", target=cell, Upgrade=g.at(g.v("GearOpts"), option), Selected=chosen)]
    g.flow("tiers.LoopBody", br_tier, options, keep_opts, "options.execute")
    g.flow(br_tier + ".else", clear, "options.execute")
    g.flow("options.LoopBody", br_opt, *show)
    g.flow(br_opt + ".else", g.set_vis(cell, "Hidden"), g.set_vis(link, "Hidden"))
    return g.data()


def g_gear_events():
    """Item tooltip on the picture (items with no tiers), made on the first hover."""
    g = G()
    g.node("picHover", "boundevent", widget="PicBtn", name="OnHovered")
    g.hover_tip("picHover", "GearItem", "ItemTipFor", "ItemTip", g.v("PicBtn"), item_tip_fill(g, "GearItem"))
    return g.data()


# ----------------------------------------------------------------------------- DB_Column

def panel(name, height, child, slot, rule_name=None, rule_var=False):
    """Fixed-height panel with an orange (or class colour) rule on top."""
    return box(name + "Box", height=height, slot=slot, child=border(name + "Bg", PANEL, child=vbox(name + "Rows", [
        rule(rule_name or name + "Rule", var=rule_var), child])))


def tag(name, label, fill, fg, slot=None):
    """YOU / HOST tag, TAG_H high, capitals centred."""
    pre, post = caps_pad(RIFT, F_TAG, TAG_H)
    return border(name, fill, var=True, pad=(8, pre, 8, post), slot=slot,
                  child=text(name + "Text", label, RIFT, F_TAG, fg))


def column_tree():
    gap = vslot(pad=(0, GAP, 0, 0))
    # Header 62 = class rule 3 + 59: class icon 40 | 12 | name row 34 (name, YOU/HOST tags) over the sub line 20,
    # the 54 high block centred (2.5 above and below). The sub line runs under the tags, so it has the full width.
    name = clipped(text("NameText", "", RIFT, F_HEAD_NAME, WHITE, var=True))
    name["slot"] = fit_slot(RIFT, F_HEAD_NAME, HEAD_NAME_H, fill=True)
    tags = hbox("Tags", [tag("TagYou", "YOU", ORANGE, INK),
                         tag("TagHost", "HOST", DARK, LIGHT_TEXT, slot=hslot(pad=(4, 0, 0, 0)))],
                slot=hslot(pad=(8, 0, 0, 0)))
    header_row = hbox("HeaderRow", [
        box("IconBox", CLASS_ICON, CLASS_ICON, slot=hslot(), child=deco(image("ClassIcon", WHITE, var=True))),
        vbox("Names", [
            box("NameRow", height=HEAD_NAME_H, child=hbox("NameLine", [name, tags])),
            capbox("SubBox", clipped(text("SubText", "", CARBON, F_HEAD_SUB, WHITE, var=True)), CARBON, F_HEAD_SUB,
                   HEAD_SUB_H),
        ], slot=hslot(True, (12, 0, 0, 0))),
    ], slot=vslot(True, (12, 0, 12, 0)))
    header = panel("Head", HEAD_H, header_row, None, rule_name="ClassRule", rule_var=True)

    # Gear area 418x382: 2x2 gear cards 206x188, 6 apart both ways. Code slots 2..5 = Gear1..Gear4.
    def gear_card(name, left):
        return w(cls(GEAR), name, True, slot=hslot(pad=(left, 0, 0, 0)))

    gear = box("GearArea", height=GEAR_AREA_H, slot=gap, child=vbox("GearGrid", [
        hbox("GearTop", [gear_card("Gear1", 0), gear_card("Gear2", GAP)]),
        hbox("GearBottom", [gear_card("Gear3", 0), gear_card("Gear4", GAP)], slot=vslot(pad=(0, GAP, 0, 0))),
    ]))

    def perk_tile(name, left_gap):
        return w(cls(PERK), name, True, {"Visibility": "Visible"}, hslot(pad=(left_gap, 0, 0, 0)))

    # 3 passive, a wider gap, 2 active, a wider gap, 1 proficiency: 6 x 40 + 3 x 4 + 2 x 10 = 272 of the 394 wide
    # row (the PERKS label and its gap take about 92).
    row = []
    for kind, names in enumerate(PERK_TILES):
        for k, name in enumerate(names):
            row.append(perk_tile(name, PERK_GAP if k else (KIND_GAP if kind else 0)))
    tiles = hbox("PerkTiles", row, var=True)
    assert 6 * TILE + 3 * PERK_GAP + 2 * KIND_GAP + 92 <= COL_W - 24
    tiles["slot"] = oslot("HAlign_Right", "VAlign_Center")
    note = props(text("PerkNote", "", BODY, F_NOTE, DIM, var=True, slot=oslot("HAlign_Right", "VAlign_Center"),
                      justify="Right"), WrapTextAt="320", Visibility="Collapsed")
    perk_row = hbox("PerkRow", [
        text("PerkLabel", "PERKS", RIFT, F_PERKS, WHITE, slot=fit_slot(RIFT, F_PERKS, PERK_H - 3)),
        overlay("PerkRight", [tiles, note], slot=hslot(True, (12, 0, 0, 0))),
    ], slot=vslot(True, (12, 0, 12, 0)))
    perks = panel("Perk", PERK_H, perk_row, gap)

    # The game's buttons: TAKE BUILD orange (primary), COPY CODE dark (secondary). TakeBtnSize is collapsed for
    # the local player, so COPY CODE then takes the whole row.
    take = game_button("TakeBtn", TEXT_TAKE, F_BUTTON, primary=True, height=BTN_H, slot=fill_slot(2))
    take["var"] = True
    copy = game_button("CopyBtn", TEXT_COPY, F_BUTTON, primary=False, height=BTN_H, slot=fill_slot(1))
    buttons = box("BtnRow", height=BTN_H, var=True, slot=gap, child=hbox("Buttons", [
        take, spacer("TakeGap", 8, var=True), copy]))
    # 990 = 62 + 6 + 210 + 6 + 210 + 6 + 382 + 6 + 52 + 6 + 44. Hidden until ShowPlayer or ShowCode.
    # Compact: BtnRow is collapsed (a collapsed box child takes no space, its slot padding neither) and Root is 940.
    assert HEAD_H + 2 * CARD_H + GEAR_AREA_H + PERK_H + BTN_H + 5 * GAP == COL_H
    assert 2 * GEAR_W + GAP == COL_W and 2 * GEAR_H + GAP == GEAR_AREA_H
    assert COMPACT_H == 940
    content = props(vbox("Body", [
        header,
        w(cls(CARD), "Card1", True, slot=gap),
        w(cls(CARD), "Card2", True, slot=gap),
        gear, perks, buttons,
    ], var=True), Visibility="Hidden")
    return box("Root", COL_W, COL_H, child=content, var=True)


def column_members():
    return {"variables": [
        t("LastSig", "string"), t("SigWork", "string"),
        t("TakeTitle", "string"),   # header name, passed to Window.OpenTake
        t("ColPerks", "object", PERKASSET, array=True), t("ColRanks", "int", array=True),
        # Perk tiles of each kind (0 passive P1..P3, 1 active A1..A2, 2 proficiency F1) and how many are filled.
        t("Tiles0", "object", cls(PERK), array=True), t("Tiles1", "object", cls(PERK), array=True),
        t("Tiles2", "object", cls(PERK), array=True), t("N0", "int"), t("N1", "int"), t("N2", "int"),
        t("Compact", "bool", default="false"),   # SetCompact(On)
        t("HasButtons", "bool"),   # the last Show was ShowPlayer (buttons), not ShowCode
        # SameAsLast: what the column last drew a player from (Fp...), and its working values.
        t("FpPlayer", "object", PS), t("FpClass", "object", CHARID), t("FpName", "string"), t("FpLevel", "int"),
        t("FpHost", "bool"), t("FpHex", "bool"), t("FpEarly", "bool"), t("FpLoadout", "int", default="-1"),
        t("FpRev", "int"), t("FpLink", "string"), t("FpAt", "float"), t("FpSeen", "float"),
        t("FpSels", "struct", SELECTION, array=True), t("FpPerks", "struct", PERKITEM, array=True),
        t("FpStats", "struct", PROGRESS, array=True), t("FpShareIds", "int", array=True),
        t("FpSharePerks", "object", PERKASSET, array=True), t("FpShareRanks", "int", array=True),
        t("SameTmp", "bool"), t("LoadTmp", "int"), t("LinkTmp", "string"),
    ], "functions": [
        {"name": "SameAsLast", "inputs": [t("Player", "object", PS)], "outputs": [t("Same", "bool")]},
        {"name": "PushData"},
        {"name": "ApplyButtons"},
        {"name": "ShowHeader", "inputs": [t("HeadName", "string"), t("HeadSub", "string"), t("HeadColor", "struct", LINEAR),
                                          t("HeadIcon", "object", TEXTURE), t("HeadYou", "bool"), t("HeadHost", "bool")]},
        {"name": "ShowBuild", "inputs": [t("BuildCode", "string")]},
        {"name": "ShowPerks"},
        {"name": "ShowNote", "inputs": [t("Note", "string")]},
        {"name": "CopyReset"},
    ]}


def g_column_push_data():
    """Hands Data to the weapon cards, gear cards and perk tiles."""
    g = G()
    steps = []
    perks = [(name, PERK) for names in PERK_TILES for name in names]
    for name, owner in [("Card1", CARD), ("Card2", CARD), ("Gear1", GEAR), ("Gear2", GEAR), ("Gear3", GEAR),
                        ("Gear4", GEAR)] + perks:
        steps.append(g.put("Data", g.v("Data"), cls(owner), g.v(name)))
    g.flow("entry", *steps)
    return g.data()


def g_column_header():
    g = G()
    col = "@entry.HeadColor"
    steps = [g.set_text("NameText", g.as_text("@entry.HeadName")),
             g.set_text("SubText", g.as_text("@entry.HeadSub")),
             g.set_text_colour("SubText", g.slate_colour(col)),
             g.tint("ClassRule", col),
             g.set_image("ClassIcon", "@entry.HeadIcon"), g.tint("ClassIcon", col),
             g.set_vis(g.v("ClassIcon"), g.vis_if(g.valid("@entry.HeadIcon"), "HitTestInvisible", "Hidden")),
             g.set_vis(g.v("TagYou"), g.vis_if("@entry.HeadYou", "HitTestInvisible", "Collapsed")),
             g.set_vis(g.v("TagHost"), g.vis_if("@entry.HeadHost", "HitTestInvisible", "Collapsed"))]
    g.flow("entry", *steps)
    return g.data()


def g_column_build():
    """Code slots 0 and 1 go to the weapon cards, 2 to 5 to the gear cards. An unknown slot shows as UNKNOWN.
    Slot 6 (pickaxe) is not shown: the column has no room for a fifth gear card (common.SHOWN_SLOTS)."""
    g = G()
    steps = []
    for slot in range(SHOWN_SLOTS):
        decoded = g.f(cls(DATA) + ":DecodeSlot", target=g.v("Data"), Code="@entry.BuildCode", Slot=str(slot))
        out = lambda pin: "@%s.%s" % (decoded, pin)  # noqa: E731
        item = g.pick_obj(out("Found"), out("Item"), ITEMID)
        if slot < 2:
            show = g.f(cls(CARD) + ":Show", target=g.v("Card%d" % (slot + 1)), Item=item, Choices=out("Choices"),
                       Overclock=out("Overclock"))
        else:
            show = g.f(cls(GEAR) + ":Show", target=g.v("Gear%d" % (slot - 1)), Label=GEAR_LABELS[slot - 2], Item=item,
                       Choices=out("Choices"))
        steps += [decoded, show]
    g.flow("entry", *steps)
    return g.data()


def g_column_perks():
    """Passive perks fill P1..P3, active ones A1..A2, the proficiency F1 (passive if IsUsageType Passive, active if
    Active, else proficiency), in list order; perks beyond a kind's tiles are not shown; the rest stay empty.
    One pass over ColPerks per kind."""
    g = G()
    first = g.br(g.eq(g.length(g.v("Tiles0")), "0"))
    keep = []
    for kind, names in enumerate(PERK_TILES):
        nid = "tiles%d" % kind
        g.node(nid, "makearray", n=len(names))
        for i, name in enumerate(names):
            g.link(unref(g.v(name)), "%s.[%d]" % (nid, i))
        keep.append(g.put("Tiles%d" % kind, "@%s.Array" % nid))
    g.flow("entry", first, *keep)
    tails = [keep[-1], first + ".else"]
    for kind, names in enumerate(PERK_TILES):
        count, tiles = "N%d" % kind, "Tiles%d" % kind
        reset = g.put(count, "0")
        loop = "perks%d" % kind
        perk = "@" + g.loop(loop, unref(g.v("ColPerks")))
        rank = g.at(g.v("ColRanks"), "@%s.Array Index" % loop)
        passive = g.rv(PERKASSET + ":IsUsageType", target=perk, InType="Passive")
        active = g.rv(PERKASSET + ":IsUsageType", target=perk, InType="Active")
        mine = [passive, g.and_(g.not_(passive), active),
                g.and_(g.not_(passive), g.not_(active))][kind]
        br_valid = g.br(g.valid(perk))
        br_kind = g.br(mine)
        br_room = g.br(g.lt(g.v(count), str(len(names))))
        set_tile = g.f(cls(PERK) + ":Set", target=g.at(g.v(tiles), g.v(count)), Perk=perk, Rank=rank)
        inc = g.put(count, g.add(g.v(count), "1"))
        g.after(tails, reset)
        g.flow(reset, loop + ".Exec")
        g.flow(loop + ".LoopBody", br_valid, br_kind, br_room, set_tile, inc)
        # Empty tiles after the last perk of the kind.
        rest = "rest%d" % kind
        g.for_range(rest, g.v(count), str(len(names) - 1))
        clear = g.f(cls(PERK) + ":Set", target=g.at(g.v(tiles), "@%s.Index" % rest), Rank="0")
        g.flow(loop + ".Completed", rest + ".execute")
        g.flow(rest + ".LoopBody", clear)
        tails = [rest + ".Completed"]
    shown = [g.set_vis(g.v("PerkTiles"), "SelfHitTestInvisible"), g.set_vis(g.v("PerkNote"), "Collapsed")]
    g.after(tails, shown[0])
    g.flow(*shown)
    return g.data()


def g_column_note():
    """A line of text in place of the perk tiles."""
    g = G()
    g.flow("entry", g.set_text("PerkNote", g.as_text("@entry.Note")),
           g.set_vis(g.v("PerkNote"), "HitTestInvisible"), g.set_vis(g.v("PerkTiles"), "Collapsed"))
    return g.data()


def g_column_same():
    """Whether nothing ShowPlayer shows of Player can have changed since the column last drew a player: the same
    player, class, name, level, host flag, selected loadout and Data.Revision (the local player's save), the same
    replicated selections, perks and stats, the same host perk table (DB_PerkShare_v1) and link (DB_BuildShare_v2),
    the hexagon textures loaded as before, and Data as old as before (10 s after it spawned "waiting for the host"
    becomes "not available"). Also false every FRESH_FOR seconds, for what no input here covers, and after a
    SEEN_GAP without a call. Records the inputs for the next call. Data and Player must be valid.
    ShowPlayer runs once a second per column; this is its cheap way out: the build code, header and perks are worked
    out only when one of their sources changed."""
    g = G()
    player, data = "@entry.Player", g.v("Data")

    def both(*conds):
        acc = conds[0]
        for cond in conds[1:]:
            acc = g.and_(acc, cond)
        return acc

    def still(*conds):
        return g.put("SameTmp", both(g.v("SameTmp"), *conds))

    def identical(a, b):
        return g.rv(KARR + ":Array_Identical", ArrayA=a, ArrayB=b)

    def bool_eq(a, b):
        return g.rv(KML + ":EqualEqual_BoolBool", A=a, B=b)

    def within(stamp, seconds):
        return g.rv(KML + ":Less_FloatFloat", A=g.rv(KML + ":Subtract_FloatFloat", A=now, B=g.v(stamp)), B=seconds)

    klass = g.rv(PS + ":GetSelectedCharacterID", target=player)
    name = g.rv(PLAYERSTATE + ":GetPlayerName", target=player)
    level = g.rv(PS + ":GetSelectedCharacterLevel", target=player)
    host = g.v("bIsServer", PS, player)
    hexes = g.valid(g.v("HexBg", cls(DATA), data))
    early = g.rv(KML + ":Less_FloatFloat", A=g.rv(ACTOR + ":GetGameTimeSinceCreation", target=data), B="10.0")
    rev = g.v("Revision", cls(DATA), data)
    now = g.rv(GS + ":GetRealTimeSeconds")
    # The selected loadout of the class in the local save (what the local player's column shows).
    load0 = g.put("LoadTmp", "-1")
    save = g.rv(GFL + ":GetFSDSaveGame")
    has_save = g.br(g.and_(g.valid(save), g.valid(klass)))
    load1 = g.put("LoadTmp", g.rv(SAVEGAME + ":GetSelectedLoadoutIndex", target=save, characterID=klass))
    first = g.put("SameTmp", both(
        g.obj_eq(player, g.v("FpPlayer")), g.obj_eq(klass, g.v("FpClass")), g.str_eq(name, g.v("FpName")),
        g.eq(level, g.v("FpLevel")), bool_eq(host, g.v("FpHost")), bool_eq(hexes, g.v("FpHex")),
        bool_eq(early, g.v("FpEarly")), g.eq(g.v("LoadTmp"), g.v("FpLoadout")), g.eq(rev, g.v("FpRev")),
        within("FpAt", FRESH_FOR), within("FpSeen", SEEN_GAP)))
    seen = g.put("FpSeen", now)
    # The player's replicated save state.
    comp = g.v("SaveGameStateComponent", PS, player)
    has_comp = g.br(g.valid(comp))
    sels, perks, stats = [g.v(prop, SGSC, comp) for prop in ("ItemUpgradeSelections", "EquippedPerks", "CharacterStats")]
    comp_same = still(identical(sels, g.v("FpSels")), identical(perks, g.v("FpPerks")),
                      identical(stats, g.v("FpStats")))
    comp_keep = [g.put("FpSels", sels), g.put("FpPerks", perks), g.put("FpStats", stats)]
    none_same = still(g.eq(g.length(g.v("FpSels")), "0"), g.eq(g.length(g.v("FpPerks")), "0"))
    none_keep = [g.f(KARR + ":Array_Clear", TargetArray=g.v(var)) for var in ("FpSels", "FpPerks", "FpStats")]
    # The host's 0.1.0 perk table, once this client found it.
    share = g.v("PerksOf_Share", cls(DATA), data)
    has_share = g.br(g.valid(share))
    pairs = (("Ids", "FpShareIds"), ("Perks", "FpSharePerks"), ("Ranks", "FpShareRanks"))
    share_same = still(*[identical(g.v(prop, cls(SHARE), share), g.v(var)) for prop, var in pairs])
    share_keep = [g.put(var, g.v(prop, cls(SHARE), share)) for prop, var in pairs]
    # The player's link: its code and whether its perks count.
    link = g.f(cls(DATA) + ":LinkFor", target=data, Player=player)
    found = "@%s.Link" % link
    sig0 = g.put("LinkTmp", "")
    has_link = g.br(g.valid(found))
    sig1 = g.put("LinkTmp", g.concat(g.v("Code", cls(BUILD_LINK), found),
                                     g.pick_string(g.v("PerksKnown", cls(BUILD_LINK), found), "+", "-")))
    link_same = still(g.str_eq(g.v("LinkTmp"), g.v("FpLink")))
    link_keep = g.put("FpLink", g.v("LinkTmp"))
    same = g.br(g.v("SameTmp"))
    store = [g.put("FpPlayer", player), g.put("FpClass", klass), g.put("FpName", name), g.put("FpLevel", level),
             g.put("FpHost", host), g.put("FpHex", hexes), g.put("FpEarly", early),
             g.put("FpLoadout", g.v("LoadTmp")), g.put("FpRev", rev), g.put("FpAt", now)]
    g.flow("entry", load0, has_save, load1, first)
    g.flow(has_save + ".else", first)
    g.flow(first, seen, has_comp, comp_same, *comp_keep, has_share)
    g.flow(has_comp + ".else", none_same, *none_keep, has_share)
    g.flow(has_share, share_same, *share_keep, link)
    g.flow(has_share + ".else", link)
    g.flow(link, sig0, has_link, sig1, link_same)
    g.flow(has_link + ".else", link_same)
    g.flow(link_same, link_keep, same, "result")
    g.flow(same + ".else", *store, "result")
    g.pins("result", {"Same": g.v("SameTmp")})
    return g.data()


def g_column_show_player():
    """Nothing when SameAsLast: the sources of what the column shows did not change. Else the code, header and
    perks are worked out and drawn when their signature differs from the last drawn one."""
    g = G()
    player, data = "@entry.Player", g.v("Data")
    ok = g.br(g.and_(g.valid(data), g.valid(player)))
    unchanged = g.f("SameAsLast", Player=player)
    fresh = g.br("@%s.Same" % unchanged)
    code = g.f(cls(DATA) + ":CodeOf", target=g.v("Data"), Player=player)
    head = g.f(cls(DATA) + ":HeaderOf", target=g.v("Data"), Player=player)
    perks = g.f(cls(DATA) + ":PerksOf", target=g.v("Data"), Player=player)
    hd = lambda pin: "@%s.%s" % (head, pin)  # noqa: E731
    keep = [g.put("ColPerks", "@%s.Perks" % perks), g.put("ColRanks", "@%s.Ranks" % perks)]
    # Signature of everything shown: code, header lines, tags, perk state, perks and ranks, and whether the hexagon
    # textures are loaded (they load asynchronously; a column drawn before that is redrawn once they are there).
    sig = g.concat("P|", "@%s.Code" % code, "|", hd("Name"), "|", hd("Sub"), "|",
                   g.rv(KSTR + ":Conv_BoolToString", InBool=hd("IsYou")),
                   g.rv(KSTR + ":Conv_BoolToString", InBool=hd("IsHost")), "|", g.int_str("@%s.State" % perks), "|",
                   g.rv(KSTR + ":Conv_BoolToString", InBool=g.valid(g.v("HexBg", cls(DATA), g.v("Data")))))
    start = g.put("SigWork", sig)
    perk = g.loop("sigPerks", unref(g.v("ColPerks")))
    add = g.put("SigWork", g.concat(g.v("SigWork"), "|", g.rv(KSL + ":GetObjectName", Object="@" + perk), ":",
                                    g.int_str(g.at(g.v("ColRanks"), "@sigPerks.Array Index"))))
    same = g.br(g.str_eq(g.v("SigWork"), g.v("LastSig")))
    g.flow("entry", ok, unchanged, fresh)
    g.flow(fresh + ".else", code, head, perks, *keep, start, "sigPerks.Exec")
    g.flow("sigPerks.LoopBody", add)
    g.flow("sigPerks.Completed", same)
    g.flow(ok + ".else", g.f("Clear"))

    # Changed: show it all.
    has_code = g.str_ne("@%s.Code" % code, "")
    show = [g.put("LastSig", g.v("SigWork")), g.put("Code", "@%s.Code" % code), g.put("TakeTitle", hd("Name")),
            g.f("PushData"),
            g.f("ShowHeader", HeadName=hd("Name"), HeadSub=hd("Sub"), HeadColor=hd("Color"), HeadIcon=hd("Icon"),
                HeadYou=hd("IsYou"), HeadHost=hd("IsHost")),
            g.f("ShowBuild", BuildCode="@%s.Code" % code)]
    state = "@%s.State" % perks
    known = g.br(g.eq(state, "0"))
    tiles = g.f("ShowPerks")
    note = g.f("ShowNote", Note=g.pick_string(g.eq(state, "1"), TEXT_NOT_SHARED,
                                              g.pick_string(g.eq(state, "3"), TEXT_NO_PERKS, TEXT_WAITING)))
    # Buttons: the local player can only copy; take and copy need a code.
    not_you = g.not_(hd("IsYou"))
    buttons = [g.set_vis(g.v("TakeBtnSize"), g.vis_if(not_you, "SelfHitTestInvisible", "Collapsed")),
               g.set_vis(g.v("TakeGap"), g.vis_if(not_you, "Visible", "Collapsed")),
               g.f(WIDGET + "SetIsEnabled", target=g.v("TakeBtnWrap"), bInIsEnabled=has_code),
               g.f(WIDGET + "SetIsEnabled", target=g.v("CopyBtnWrap"), bInIsEnabled=has_code),
               g.put("HasButtons", "true"), g.f("ApplyButtons"),
               g.set_vis(g.v("Body"), "SelfHitTestInvisible")]
    g.flow(same + ".else", *show, known, tiles, buttons[0])
    g.flow(known + ".else", note, buttons[0])
    g.flow(*buttons)
    return g.data()


def g_column_show_code():
    """Header, build, and the code's own perks (Data.PerksOfCode), or a note when the code has none."""
    g = G()
    sig = g.concat("C|", "@entry.NewCode", "|", "@entry.Title", "|",
                   g.rv(KSTR + ":Conv_BoolToString", InBool=g.valid(g.v("HexBg", cls(DATA), g.v("Data")))))
    ok = g.br(g.and_(g.valid(g.v("Data")), g.str_ne(sig, g.v("LastSig"))))
    head = g.f(cls(DATA) + ":HeaderOfCode", target=g.v("Data"), Code="@entry.NewCode")
    hd = lambda pin: "@%s.%s" % (head, pin)  # noqa: E731
    perks = g.f(cls(DATA) + ":PerksOfCode", target=g.v("Data"), Code="@entry.NewCode")
    steps = [g.put("LastSig", sig), g.put("FpPlayer"), g.put("Code", "@entry.NewCode"),
             g.put("TakeTitle", "@entry.Title"), g.f("PushData"), head,
             g.f("ShowHeader", HeadName="@entry.Title", HeadSub=hd("Sub"), HeadColor=hd("Color"), HeadIcon=hd("Icon"),
                 HeadYou="false", HeadHost="false"),
             g.f("ShowBuild", BuildCode="@entry.NewCode"),
             perks, g.put("ColPerks", "@%s.Perks" % perks), g.put("ColRanks", "@%s.Ranks" % perks)]
    found = g.br("@%s.Found" % perks)
    tiles = g.f("ShowPerks")
    note = g.f("ShowNote", Note=TEXT_CODE_NO_PERKS)
    tail = [g.put("HasButtons", "false"), g.f("ApplyButtons"), g.set_vis(g.v("Body"), "SelfHitTestInvisible")]
    g.flow("entry", ok, *steps, found, tiles, tail[0])
    g.flow(found + ".else", note, tail[0])
    g.flow(*tail)
    return g.data()


def g_column_apply_buttons():
    """Button row: collapsed when compact (no space, no gap); else shown for a player, hidden (space kept) for a
    pasted code."""
    g = G()
    normal = g.vis_if(g.v("HasButtons"), "SelfHitTestInvisible", "Hidden")
    g.flow("entry", g.set_vis(g.v("BtnRow"), g.vis_if(g.v("Compact"), "Collapsed", normal)))
    return g.data()


def g_column_set_compact():
    """Compact: the root is COMPACT_H high and the button row is collapsed; off: COL_H, buttons as before."""
    g = G()
    height = g.rv(KML + ":SelectFloat", A=str(COMPACT_H), B=str(COL_H), bPickA="@entry.On")
    g.flow("entry", g.put("Compact", "@entry.On"),
           g.f(UMG + "SizeBox:SetHeightOverride", target=g.v("Root"), InHeightOverride=height),
           g.f("ApplyButtons"))
    return g.data()


def g_column_clear():
    """FpPlayer goes too: the next ShowPlayer draws, whoever it shows (SameAsLast)."""
    g = G()
    g.flow("entry", g.set_vis(g.v("Body"), "Hidden"), g.put("LastSig", ""), g.put("FpPlayer"), g.put("Code", ""),
           g.put("TakeTitle", ""))
    return g.data()


def g_column_copy_reset():
    g = G()
    g.flow("entry", g.set_text("CopyBtnText", TEXT_COPY))
    return g.data()


def g_column_events():
    g = G()
    has_code = g.str_ne(g.v("Code"), "")
    g.node("take", "boundevent", widget="TakeBtn", name="OnClicked")
    # Window is None in DB_Select (compact, no buttons): the only Window call is guarded.
    can_take = g.br(g.and_(g.valid(g.v("Window")), has_code))
    g.flow("take", can_take, g.f(cls(WINDOW) + ":OpenTake", target=g.v("Window"), NewCode=g.v("Code"),
                                 Title=g.v("TakeTitle")))

    g.node("copy", "boundevent", widget="CopyBtn", name="OnClicked")
    can_copy = g.br(g.str_ne(g.v("Code"), ""))
    g.flow("copy", can_copy, g.f(FRONTEND + ":CopyStringToClipboard", toClipboard=g.v("Code")),
           g.set_text("CopyBtnText", TEXT_COPIED),
           g.f(KSL + ":K2_SetTimer", Object=g.me(), FunctionName="CopyReset", Time=COPIED_SECONDS, bLooping="false"))
    press_feedback(g, "CopyBtn")  # COPY CODE is a secondary button: orange while held down
    return g.data()


# ----------------------------------------------------------------------------- module interface

def trees():
    return {TIP: tip_tree(), CELL: cell_tree(), PERK: perk_tree(), CARD: card_tree(), GEAR: gear_tree(),
            COLUMN: column_tree()}


def members():
    return {TIP: tip_members(), CELL: cell_members(), PERK: perk_members(), CARD: card_members(),
            GEAR: gear_members(), COLUMN: column_members()}


def graphs():
    return {
        TIP: {"Set": g_tip_set(), "SetExtra": g_tip_set_extra(), "ShowExtra": g_tip_show_extra(),
              "ApplyExtra": g_tip_apply_extra()},
        CELL: {"Set": g_cell_set(), "EventGraph": g_cell_events()},
        PERK: {"Set": g_perk_set(), "EventGraph": g_perk_events()},
        CARD: {"EnsureCells": g_card_ensure(), "Show": g_card_show(), "ShowOverclock": g_card_overclock(),
               "ShowGrid": g_card_grid(), "EventGraph": g_card_events()},
        GEAR: {"Show": g_gear_show(), "EventGraph": g_gear_events()},
        COLUMN: {"PushData": g_column_push_data(), "ShowHeader": g_column_header(), "ShowBuild": g_column_build(),
                 "ShowPerks": g_column_perks(), "ShowNote": g_column_note(), "SameAsLast": g_column_same(),
                 "ShowPlayer": g_column_show_player(),
                 "ShowCode": g_column_show_code(), "Clear": g_column_clear(), "CopyReset": g_column_copy_reset(),
                 "ApplyButtons": g_column_apply_buttons(), "SetCompact": g_column_set_compact(),
                 "EventGraph": g_column_events()},
    }
