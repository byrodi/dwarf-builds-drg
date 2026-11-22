"""Shell of Dwarf Builds: the hotkey actor, the window, the take-build dialog, roster chips, slot buttons and the
overlay on the game's class selection screen.

Owns DB_Mod (and its children InitSpacerig, InitCave), DB_Window, DB_TakeDialog, DB_Chip, DB_SlotBtn and DB_Select.
Layout follows the approved mockup (Main, Copy and Code .dc.html); text and boxes were made larger after the
first in-game test. The look follows the game's own menus: the brown menu dim, translucent black panels with an
orange top rule, white Rift Soft titles, Carbon categories and the game's action button (common.game_button).
UMG font sizes are points at 96 DPI.
Nothing ticks. The window runs one 1 s timer while it is open. The actor (InitSpacerig/InitCave) waits for input
and runs a 0.5 s poll for the class selection screen for a while after BeginPlay and after a selection start; then
a mission stops it and the Space Rig slows it to 2 s until the screen is found; DB_Select sits inside that screen
and shows and hides with it.
The website (common.SITE_URL): BROWSE (the third tab) and PUBLISH MY BUILD open it in the Steam overlay, OPEN IN BROWSER in
the web browser. The clipboard is read only when the player presses PASTE FROM CLIPBOARD.
"""
from dwarfbuilds.common import press_feedback  # noqa: E402
from dwarfbuilds.common import (BLACK_TEXT, BODY, BODY_BOLD, CARBON, CHARID, CHIP, CODE_VERSION, COLUMN, CORE, DATA,
                               FRONTEND, FSD, GFL, GS, INIT_CAVE, INIT_SPACERIG, KARR, KML, KSL, KSTR, KTXT,
                               LIGHT_TEXT, ONLINE, ORANGE, ORANGE_LIGHT, PC, PS, RIFT, SAVEGAME, SELECT, SHARE, SITE_URL,
                               SLOTBTN, SLOTS, TAKE, TEXTURE, UMG, USERWIDGET, VERY_DARK, WBL, WHITE, WINDOW, WINDOWMANAGER,
                               WINDOWWIDGET, Graph, border, box, cls, colour, font, game_button, hslot, image, margin,
                               oslot, ref, slate, soft_load, t, text, vslot, w)
from dwarfbuilds.common import HUBMOD, MODHUB  # noqa: E402

ACTOR = "/Script/Engine.Actor"
CONTROLLER = "/Script/Engine.Controller"
PLAYERCONTROLLER = "/Script/Engine.PlayerController"
PLAYERSTATE = "/Script/Engine.PlayerState"
GAMEINSTANCE = FSD + "FSDGameInstance"
CAMERA_LOCATION = FSD + "ECharselectionCameraLocation"
INPUTLIB = "/Script/Engine.KismetInputLibrary"
MARGIN = "/Script/SlateCore.Margin"
SLATECOLOR = "/Script/SlateCore.SlateColor"
VISIBILITY = "/Script/UMG.ESlateVisibility"
EVENTREPLY = "/Script/UMG.EventReply"

S, I, B, F = "string", "int", "bool", "float"

ZORDER = 60
COLUMN_WIDTH = 418
COLUMN_HEIGHT = 990           # DB_Column: 62+6+210+6+210+6+382+6+52+6+44
COLUMN_GAP = 16
PAGE_PAD = 19                 # left and right: 1 px panel edge + 19 = the mockup's 20 px padding
PAGE_PAD_V = 8                # above and below the page
PAGE_SIZE = 4                 # columns per page


def panel_width(cols):
    """Panel width that holds `cols` columns: the columns, their gaps, the page padding and the 1 px edges."""
    return cols * COLUMN_WIDTH + (cols - 1) * COLUMN_GAP + 2 * PAGE_PAD + 2


# The panel width follows the player count (UpdateWidth): 4 columns (1760) with 4 or more players, else just the
# columns, but never below PANEL_MIN_WIDTH (the header and the BUILD CODE tab need it).
PANEL_WIDTH = panel_width(PAGE_SIZE)  # 1760
PANEL_MIN_WIDTH = 1000
HEADER_H = 60
ROSTER_PAD_V = 8
CHIP_H, CHIP_MAX, CHIP_GAP = 44, 180, 3
# Panel height: orange rule 3 + header + header line 1 + page + bottom edge 1 = 1071.
PANEL_HEIGHT = 3 + HEADER_H + 1 + 2 * PAGE_PAD_V + COLUMN_HEIGHT + 1
PANEL_FIT_HEIGHT = PANEL_HEIGHT + 2 * ROSTER_PAD_V + CHIP_H + 1  # 1132: with the roster strip (more than 4 players)
FIT_PAD = 8                   # screen margin kept around the panel when it is scaled down
ROSTER_WIDTH = PANEL_WIDTH - 2 - 40  # inside the edge and the 20 px roster padding (the roster needs 5+ players: 1760)
DIALOG_WIDTH = 560            # take dialog: 9 slot buttons of 48 + 4 per row, plus the padding
# Header buttons (common.game_button, 44 high). Widest header (5+ players, every part shown), measured with the
# font files: title 171 + count 114 + tabs 275 + filters 717 + paging 253 + close 143 = about 1672 of 1718. BROWSE,
# the third tab (about 132 + 6), and the logo (30 + 10) are new, the gaps before the tabs and the filters went from
# 24 to 18; the player count is hidden while the filters show (ALL shows the same number), so the widest header is
# about 1710.
LOGO_SIZE = 30
TEX_LOGO = "/Game/_DwarfBuilds/Art/T_DB_Logo.T_DB_Logo"   # Tools/dwarfbuilds/art/logo.png (Tools/dwarfbuilds_art.py)
BTN_H = 44
F_HEAD_BTN = 20               # tabs, CLOSE, paging arrows (Rift)
F_FILTER = 18                 # filter label and count (Rift)
FILTER_PAD = (10, 3, 10, 0)   # filter buttons: less side padding than the default 16
ARROW_PAD = (8, 3, 8, 0)
PAGE_TEXT_W = 124             # "13-16 / 16" at Carbon 18 is about 114
# BUILD CODE tab. The code box has its own row across the card (inside 470 at the 1000 minimum width, 442 for
# text) and wraps per character: a 60-character code at Carbon 20 is about 792 wide, so 2 lines; the box shows 3.
CODE_FONT = 20
CODE_BOX_H = 110              # outline 2 + text padding 22 + 3 lines of ~28 = 108
CODE_BTN_H, F_CODE_BTN = 48, 19
CODE_BTN_PAD = (10, 3, 10, 0)
# PASTE FROM CLIPBOARD (Rift 19, ~199) and COPY MY BUILD CODE (~174) share the row below the box; each button
# adds 36 (bars, gaps, padding). Fill weights follow those needs, so both fit 462 with a few px to spare.
PASTE_WEIGHT, COPY_WEIGHT = 235, 210
assert PANEL_WIDTH == 1760 and panel_width(3) == 1326 and PANEL_HEIGHT == 1071
SLOTS_PER_ROW = 9
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CLASS_LETTERS = "DEGS"        # filter 1..4; first letter of DrillerID, EngineerID, GunnerID, ScoutID
FILTER_LABELS = ["ALL", "DRILLER", "ENGINEER", "GUNNER", "SCOUT"]
CLASS_COLOURS = [None, (1.0, 0.70288, 0.0), (1.0, 0.0, 0.0), (0.09148, 0.40625, 0.0), (0.0, 0.1849, 1.0)]  # PCD_* HeroColor
CODE_HINT = "PASTE A CODE THAT STARTS WITH %s:" % CODE_VERSION


def hexc(h, a=1.0):
    """Linear colour of an sRGB hex colour."""
    def lin(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    h = h.lstrip("#")
    return tuple(round(lin(int(h[i:i + 2], 16)), 5) for i in (0, 2, 4)) + (a,)


# Text tones of the mockup.
MUTED = hexc("#CDBE96")
LABEL = hexc("#A3977A")
LIGHT = hexc("#F4EBD0")
GOOD = hexc("#7BC96F")
BAD = hexc("#F0705C")
CLEAR = (0.0, 0.0, 0.0, 0.0)

# The game's look. Panels and cards are translucent black over the brown menu dim, like the game's loadout cards
# (black 0.3) and gear-modification bar. A translucent fill must not sit inside an outline border (the outline
# colour would show through it), so outlined squares (slot letters, key box, inputs) use opaque colours.
BACKDROP = VERY_DARK + (0.9,)          # the whole screen behind the window
PANEL_BG = (0.0, 0.0, 0.0, 0.3)        # window panel
HEAD_BG = (0.0, 0.0, 0.0, 0.45)        # header bar, on the panel
CARD_BG = (0.0, 0.0, 0.0, 0.4)         # code card, roster strip, chips, status box
SHADE = VERY_DARK + (0.75,)            # behind the take dialog
DIALOG_BG = (0.0, 0.0, 0.0, 0.8)
SQUARE = (0.012, 0.008, 0.005)         # opaque near-black: slot letters, key box, inputs
SQUARE_HOVER = (0.022, 0.015, 0.009)
SQUARE_LINE = (0.34, 0.11, 0.0)        # dim orange outline (the game's loadout letters)


def obj(name, path, **extra):
    return t(name, "object", path, **extra)


# ----------------------------------------------------------------------------- widget-tree helpers

def brush(c, size=(32, 32)):
    """A solid brush: no texture, only a tint."""
    return ("(ImageSize=(X=%g,Y=%g),Margin=(Left=0,Top=0,Right=0,Bottom=0),TintColor=%s,ResourceObject=None,"
            "ResourceName=None,DrawAs=Image)" % (size[0], size[1], slate(c)))


# A flat button: clear, a light veil on hover and press. It lies over its content, so the veil shows on any fill.
BUTTON_STYLE = ("(Normal=%s,Hovered=%s,Pressed=%s,Disabled=%s,NormalPadding=(Left=0,Top=0,Right=0,Bottom=0),"
                "PressedPadding=(Left=0,Top=0,Right=0,Bottom=0))"
                % (brush(CLEAR), brush((1.0, 1.0, 1.0, 0.07)), brush((1.0, 1.0, 1.0, 0.14)), brush(CLEAR)))
NO_IMAGE = brush(CLEAR, (0, 0))
# The check box draws nothing itself; its content holds the box and the mark.
CHECK_STYLE = ("(CheckBoxType=CheckBox,UncheckedImage=%s,UncheckedHoveredImage=%s,UncheckedPressedImage=%s,"
               "CheckedImage=%s,CheckedHoveredImage=%s,CheckedPressedImage=%s,UndeterminedImage=%s,"
               "UndeterminedHoveredImage=%s,UndeterminedPressedImage=%s,Padding=(Left=0,Top=0,Right=0,Bottom=0))"
               % ((NO_IMAGE,) * 9))
TEXTBOX_STYLE = ("(BackgroundImageNormal=%s,BackgroundImageHovered=%s,BackgroundImageFocused=%s,"
                 "BackgroundImageReadOnly=%s,Padding=(Left=14,Top=12,Right=14,Bottom=10),Font=%s,ForegroundColor=%s,"
                 "BackgroundColor=%s,ReadOnlyForegroundColor=%s)"
                 % (brush(SQUARE), brush(SQUARE_HOVER), brush(SQUARE), brush(SQUARE), font(CARBON, CODE_FONT),
                    slate(WHITE), slate(WHITE), slate(LABEL)))


def weighted(weight, pad=(0, 0, 0, 0)):
    """HorizontalBoxSlot that fills with a weight."""
    props = hslot(True, pad, valign="VAlign_Fill")
    props["Size"] = "(Value=%g,SizeRule=Fill)" % weight
    return props


def with_slot(node, slot):
    node = dict(node)
    node["slot"] = slot
    return node


def clip(node):
    node["props"]["Clipping"] = "ClipToBounds"
    return node


def clickable(name, content, enabled=True, slot=None):
    """Content with a flat Button over it. The Button is the variable `name`."""
    props = {"WidgetStyle": BUTTON_STYLE, "IsFocusable": "False"}
    if not enabled:
        props["bIsEnabled"] = "False"
    return w("Overlay", name + "Layers", slot=slot, children=[
        with_slot(content, oslot()),
        w("Button", name, var=True, props=props, slot=oslot()),
    ])


def frame(name, line, fill, child, pad=(0, 0, 0, 0), var=False, halign="HAlign_Center", valign="VAlign_Center"):
    """1 px outline (border `name`Line) around a fill (border `name`Fill)."""
    inner = border(name + "Fill", fill, child, pad=pad, var=var, halign=halign, valign=valign)
    return border(name + "Line", line, inner, pad=(1, 1, 1, 1), var=var)


def find(node, name):
    """The node called `name` in a widget tree (None if there is none)."""
    if node.get("name") == name:
        return node
    for child in node.get("children") or []:
        found = find(child, name)
        if found:
            return found
    return None


def toggle_button(name, label, size, slot=None, icon=None, count=False, pad=(16, 3, 16, 0)):
    """A tab or filter: a WidgetSwitcher `name` with two common.game_button variants, index 0 = `name`Off
    (secondary: dark fill) and 1 = `name`On (primary: orange fill, the selected one). Bind OnClicked of both
    Buttons. icon: the colour of an 18 px image `variant`Icon before the label (black on the orange variant);
    count: a number `variant`Count after the label."""
    variants = []
    for suffix, primary in (("Off", False), ("On", True)):
        vname = name + suffix
        node = game_button(vname, label, size, primary=primary, height=BTN_H, pad=pad)
        if icon or count:
            button = find(node, vname)
            label_node = button["children"][0]
            ink = BLACK_TEXT if primary else LIGHT_TEXT   # the label colours of game_button
            row = []
            if icon:
                row.append(box(vname + "IconBox", 18, 18, slot=hslot(pad=(0, 0, 6, 0)),
                               child=image(vname + "Icon", BLACK_TEXT if primary else icon, var=True)))
            row.append(with_slot(label_node, hslot()))
            if count:
                row.append(text(vname + "Count", "0", RIFT, size, ink, var=True, slot=hslot(pad=(6, 0, 0, 0))))
            button["children"] = [w("HorizontalBox", vname + "Row", slot=label_node["slot"], children=row)]
        variants.append(node)
    return w("WidgetSwitcher", name, var=True, slot=slot, children=variants)


# ----------------------------------------------------------------------------- graph helpers

def pick(g, nid, a, b, cond):
    """SelectColor: a when cond, else b. a/b: colour tuples or colour pins."""
    pins = {"bPickA": ref(cond)}
    pins["A"] = colour(a) if isinstance(a, tuple) else ref(a)
    pins["B"] = colour(b) if isinstance(b, tuple) else ref(b)
    g.call(nid, KML + ":SelectColor", **pins)
    return nid + ".ReturnValue"


def wcall(g, nid, var, fn, **pins):
    """Calls a UMG function on a widget variable of this Blueprint."""
    return g.call(nid, UMG + fn, target=ref(g.get(nid + "W", var)), **pins)


def text_colour(g, nid, var, c):
    """TextBlock.SetColorAndOpacity; c is a colour tuple or a LinearColor pin."""
    g.node(nid + "S", "makestruct", struct=SLATECOLOR)
    if isinstance(c, tuple):
        g.defaults[nid + "S.SpecifiedColor"] = colour(c)
    else:
        g.link(c, nid + "S.SpecifiedColor")
    g.defaults[nid + "S.ColorUseRule"] = "UseColor_Specified"
    return wcall(g, nid, var, "TextBlock:SetColorAndOpacity", InColorAndOpacity=ref(nid + "S.SlateColor"))


def set_text(g, nid, var, value):
    """TextBlock.SetText from a literal or from a string pin (given with ref())."""
    if value.startswith("@"):
        g.call(nid + "T", KTXT + ":Conv_StringToText", InString=value)
        value = ref(nid + "T.ReturnValue")
    return wcall(g, nid, var, "TextBlock:SetText", InText=value)


def vis(g, nid, cond, on="Visible"):
    """ESlateVisibility: `on` when cond, else Collapsed."""
    g.node(nid, "select", index="bool", type={"type": "enum", "class": VISIBILITY})
    g.link(cond, nid + ".Index")
    g.defaults[nid + ".Option 0"] = "Collapsed"
    g.defaults[nid + ".Option 1"] = on
    return nid + ".ReturnValue"


def kml(g, nid, fn, **pins):
    g.call(nid, KML + ":" + fn, **pins)
    return nid + ".ReturnValue"


def valid(g, nid, pin):
    g.call(nid, KSL + ":IsValid", Object=ref(pin))
    return g.branch("br" + nid[0].upper() + nid[1:], nid + ".ReturnValue")


# ============================================================================= DB_Chip

def chip_tree():
    """A small card like the game's: translucent black with an orange top rule; the players of the page shown are
    filled orange with black text and icon (the game's selected tab or loadout letter)."""
    row = w("HorizontalBox", "Row", children=[
        box("IconBox", 20, 20, slot=hslot(pad=(0, 0, 8, 0)), child=image("IconImage", WHITE, var=True)),
        clip(text("NameText", "Player", BODY_BOLD, 15, LIGHT, var=True, slot=hslot(fill=True))),
    ])
    content = w("Overlay", "Layers2", children=[
        border("Bg", CARD_BG, row, pad=(8, 3, 8, 0), var=True, valign="VAlign_Center", slot=oslot()),
        image("Bar", ORANGE, size=(32, 3), var=True, slot=oslot("HAlign_Fill", "VAlign_Top")),
    ])
    root = box("Box", CHIP_MAX, CHIP_H, var=True, child=clickable("Btn", content))
    root["props"]["Clipping"] = "ClipToBounds"
    return root


def g_chip_set():
    """Runs every second per chip: name and tooltip only when the name changed (a tooltip is a new widget)."""
    g = Graph()
    g.call("shown", UMG + "TextBlock:GetText", target=ref(g.get("nameW0", "NameText")))
    g.call("shownS", KTXT + ":Conv_TextToString", InText=ref("shown.ReturnValue"))
    g.call("same", KSTR + ":EqualEqual_StrStr", A=ref("shownS.ReturnValue"), B=ref("entry.PlayerName"))
    g.branch("brSame", "same.ReturnValue")
    g.call("name", KTXT + ":Conv_StringToText", InString=ref("entry.PlayerName"))
    wcall(g, "setName", "NameText", "TextBlock:SetText", InText=ref("name.ReturnValue"))
    wcall(g, "tip", "Btn", "Widget:SetToolTipText", InToolTipText=ref("name.ReturnValue"))
    # Class colour on the dark chip, black on the orange one.
    wcall(g, "tint", "IconImage", "Image:SetColorAndOpacity",
          InColorAndOpacity=ref(pick(g, "iconC", BLACK_TEXT, "entry.Color", "entry.Selected")))
    g.flow("entry", "brSame", "tint")
    g.flow("brSame.else", "setName", "tip", "tint")
    wcall(g, "setBg", "Bg", "Border:SetBrushColor", InBrushColor=ref(pick(g, "bgC", ORANGE, CARD_BG, "entry.Selected")))
    wcall(g, "setBar", "Bar", "Image:SetColorAndOpacity",
          InColorAndOpacity=ref(pick(g, "barC", ORANGE_LIGHT, ORANGE, "entry.Selected")))
    # You: orange name on the dark chip; on the orange chip every name is black.
    fg = pick(g, "fgSel", BLACK_TEXT, pick(g, "fgYou", ORANGE, LIGHT, "entry.IsYou"), "entry.Selected")
    text_colour(g, "fg", "NameText", fg)
    g.flow("tint", "setBg", "setBar", "fg")
    return g.data()


def g_chip_set_icon():
    """No class (Texture None): the plain tinted square of a new chip, not the icon of the chip's last player."""
    g = Graph()
    valid(g, "has", "entry.Texture")
    wcall(g, "set", "IconImage", "Image:SetBrushFromTexture", Texture=ref("entry.Texture"), bMatchSize="false")
    wcall(g, "clear", "IconImage", "Image:SetBrushFromTexture", bMatchSize="false")
    g.flow("entry", "brHas", "set")
    g.flow("brHas.else", "clear")
    return g.data()


def g_chip_set_width():
    g = Graph()
    wcall(g, "set", "Box", "SizeBox:SetWidthOverride", InWidthOverride=ref("entry.Width"))
    g.flow("entry", "set")
    return g.data()


def g_chip_events():
    g = Graph()
    g.node("click", "boundevent", widget="Btn", name="OnClicked")
    win = g.get("win", "Window")
    valid(g, "ok", win)
    g.call("select", cls(WINDOW) + ":SelectPlayer", target=ref(win), PlayerIndex=ref(g.get("idx", "Index")))
    g.flow("click", "brOk", "select")
    return g.data()


# ============================================================================= DB_SlotBtn

def slotbtn_tree():
    """A loadout letter like the game's letter grid: an opaque dark square with a dim orange outline."""
    label = text("LabelText", "A", RIFT, 26, LIGHT, var=True, justify="Center")
    fill = border("Fill", SQUARE, label, pad=(0, 4, 0, 0), var=True, halign="HAlign_Center", valign="VAlign_Center")
    ring = border("Ring", SQUARE, fill, pad=(1, 1, 1, 1), var=True)
    outer = border("Outer", SQUARE_LINE, ring, pad=(1, 1, 1, 1), var=True)
    return box("Box", 48, 48, child=clickable("Btn", outer))


def g_slotbtn_set():
    """Picked: orange fill, black letter (the game's selected loadout). Current slot (equipped now): 2 px white
    outline (the game marks equipped things white). Else dark with a dim orange outline."""
    g = Graph()
    g.call("label", KTXT + ":Conv_StringToText", InString=ref("entry.Label"))
    wcall(g, "setLabel", "LabelText", "TextBlock:SetText", InText=ref("label.ReturnValue"))
    fill = pick(g, "fillC", ORANGE, SQUARE, "entry.Selected")
    line = pick(g, "lineC", WHITE, pick(g, "lineSel", ORANGE, SQUARE_LINE, "entry.Selected"), "entry.Current")
    ring = pick(g, "ringC", WHITE, fill, "entry.Current")
    wcall(g, "setOuter", "Outer", "Border:SetBrushColor", InBrushColor=ref(line))
    wcall(g, "setRing", "Ring", "Border:SetBrushColor", InBrushColor=ref(ring))
    wcall(g, "setFill", "Fill", "Border:SetBrushColor", InBrushColor=ref(fill))
    fg = pick(g, "fgC", BLACK_TEXT, pick(g, "fgCur", WHITE, LIGHT, "entry.Current"), "entry.Selected")
    text_colour(g, "fg", "LabelText", fg)
    g.flow("entry", "setLabel", "setOuter", "setRing", "setFill", "fg")
    return g.data()


def g_slotbtn_events():
    g = Graph()
    g.node("click", "boundevent", widget="Btn", name="OnClicked")
    dialog = g.get("dialog", "Dialog")
    valid(g, "ok", dialog)
    g.call("pick", cls(TAKE) + ":PickSlot", target=ref(dialog), SlotIndex=ref(g.get("idx", "Index")))
    g.flow("click", "brOk", "pick")
    return g.data()


# ============================================================================= DB_TakeDialog

def take_tree():
    slot_head = w("HorizontalBox", "SlotHead", slot=vslot(pad=(0, 18, 0, 0)), children=[
        text("SlotHeadText", "SAVE TO LOADOUT", CARBON, 16, LABEL, slot=hslot(fill=True)),
        text("NowText", "A IS EQUIPPED NOW", CARBON, 16, LABEL, var=True, slot=hslot()),
    ])
    grid = w("UniformGridPanel", "Grid", var=True, slot=vslot(pad=(0, 8, 0, 0), halign="HAlign_Left"),
             props={"SlotPadding": margin(2, 2, 2, 2), "MinDesiredSlotWidth": "48", "MinDesiredSlotHeight": "48"})
    mark = box("CheckSize", 24, 24, slot=hslot(), child=border(
        "CheckLine", SQUARE_LINE, border("CheckFill", SQUARE, image("CheckMark", ORANGE, var=True), pad=(4, 4, 4, 4)),
        pad=(1, 1, 1, 1)))
    check_row = w("HorizontalBox", "CheckRow", children=[
        mark, text("EquipText", "Equip this loadout after saving", BODY, 18, WHITE, slot=hslot(pad=(12, 0, 0, 0)))])
    check = w("CheckBox", "EquipAfter", var=True, slot=vslot(pad=(0, 16, 0, 0), halign="HAlign_Left"),
              props={"CheckedState": "Checked", "WidgetStyle": CHECK_STYLE, "IsFocusable": "False"},
              children=[check_row])
    status = border("StatusBox", CARD_BG, text("StatusText", " ", BODY, 18, LIGHT, var=True, wrap=True),
                    pad=(12, 8, 12, 8), var=True, slot=vslot(pad=(0, 14, 0, 0)))
    status["props"]["Visibility"] = "Collapsed"
    # Game buttons: SAVE primary (SaveBtnWrap is disabled when saving is not possible), CANCEL secondary.
    buttons = w("HorizontalBox", "ButtonRow", slot=vslot(pad=(0, 20, 0, 0)), children=[
        game_button("SaveBtn", "SAVE TO SLOT A", 24, primary=True, height=56, slot=weighted(2)),
        game_button("CancelBtn", "CANCEL", 24, primary=False, height=56, slot=weighted(1, (8, 0, 0, 0))),
    ])
    rows = w("VerticalBox", "Rows", children=[
        text("TitleText", "TAKE BUILD", RIFT, 36, WHITE, slot=vslot()),
        clip(text("ClassLine", "BUILD", CARBON, 16, MUTED, var=True, slot=vslot(pad=(0, 4, 0, 0)))),
        slot_head, grid,
        text("Note", "Slot A will be overwritten.", BODY, 17, LABEL, var=True, wrap=True, slot=vslot(pad=(0, 8, 0, 0))),
        check,
        text("OwnedNote", "Only items, upgrades, overclocks and perks you own are applied, perks up to your free "
                          "slots. Perk ranks stay your own.",
             BODY, 17, LABEL, wrap=True, slot=vslot(pad=(0, 12, 0, 0))),
        status, buttons,
    ])
    body = border("Body", DIALOG_BG, rows, pad=(28, 22, 28, 26), slot=vslot())
    panel = box("PanelBox", width=DIALOG_WIDTH, slot=oslot("HAlign_Center", "VAlign_Center"), child=border(
        "PanelEdge", CLEAR, w("VerticalBox", "PanelCol", children=[image("Rule", ORANGE, size=(32, 3), slot=vslot()), body]),
        pad=(1, 0, 1, 1)))
    # The height follows the slot count. Scaled down only when it is taller than the screen (many slots, a high UI
    # scale). ScaleToFit lays the dialog out twice a frame, but only while the dialog is shown.
    fit = w("ScaleBox", "DialogFit", props={"Stretch": "ScaleToFit", "StretchDirection": "DownOnly"},
            slot=oslot(pad=(FIT_PAD,) * 4), children=[panel])
    # The shade covers the window, so nothing behind the dialog takes clicks.
    return w("Overlay", "Root", children=[border("Shade", SHADE, slot=oslot()), fit])


def g_take_show():
    g = Graph()
    data = g.get("data", "Data")
    valid(g, "hasData", data)
    g.set("setCode", "Code", value="entry.NewCode")
    g.set("notSaved", "Saved", default="false")
    g.call("cls", cls(DATA) + ":ClassOfCode", target=ref(data), Code=ref("entry.NewCode"))
    g.set("setCls", "CodeClass", value="cls.Class")
    g.call("head", cls(DATA) + ":HeaderOfCode", target=ref(data), Code=ref("entry.NewCode"))
    # "Leaf_Lover · SCOUT" in the class colour; Sub is "SCOUT BUILD" ("" for a bad code: the title only).
    g.call("clsName", KSTR + ":Replace", SourceString=ref("head.Sub"), From=" BUILD", To="")
    g.call("line1", KSTR + ":Concat_StrStr", A=ref("entry.Title"), B=" · ")
    g.call("line2", KSTR + ":Concat_StrStr", A=ref("line1.ReturnValue"), B=ref("clsName.ReturnValue"))
    g.call("noCls", KSTR + ":IsEmpty", InString=ref("clsName.ReturnValue"))
    line = kml(g, "line", "SelectString", A=ref("entry.Title"), B=ref("line2.ReturnValue"),
               bPickA=ref("noCls.ReturnValue"))
    set_text(g, "setSub", "ClassLine", ref(line))
    text_colour(g, "subColour", "ClassLine", "head.Color")
    g.call("info", cls(DATA) + ":SlotInfo", target=ref(data), Class=ref("cls.Class"))
    g.set("setCount", "SlotCount", value="info.Count")
    g.set("setCur", "CurrentSlot", value="info.Current")
    g.set("setPick", "Picked", value="info.Current")
    g.call("can", cls(DATA) + ":CanTake", target=ref(data))
    has_slots = kml(g, "hasSlots", "Greater_IntInt", A=ref("info.Count"), B="0")
    ok1 = kml(g, "ok1", "BooleanAND", A=ref("can.Ok"), B=ref("cls.Valid"))
    ok2 = kml(g, "ok2", "BooleanAND", A=ref(ok1), B=ref(has_slots))
    g.set("setCan", "CanSave", value=ok2)
    wcall(g, "check", "EquipAfter", "CheckBox:SetIsChecked", InIsChecked="true")
    g.call("sync", "SyncCheck")
    set_text(g, "cancel", "CancelBtnText", "CANCEL")
    # Why saving is off: not a code, not allowed here (Reason), or no slots.
    r1 = kml(g, "r1", "SelectString", A="No loadout slots found.", B=ref("can.Reason"), bPickA=ref("can.Ok"))
    r2 = kml(g, "r2", "SelectString", A=ref(r1), B="Not a Dwarf Builds code.", bPickA=ref("cls.Valid"))
    set_text(g, "reason", "StatusText", ref(r2))
    text_colour(g, "reasonColour", "StatusText", BAD)
    no = kml(g, "cannot", "Not_PreBool", A=ref(g.get("canSave", "CanSave")))
    wcall(g, "statusVis", "StatusBox", "Widget:SetVisibility", InVisibility=ref(vis(g, "statusV", no)))
    g.call("update", "UpdateSlots")
    g.flow("entry", "brHasData", "setCode", "notSaved", "cls", "setCls", "head", "setSub", "subColour", "info",
           "setCount", "setCur", "setPick", "can", "setCan", "check", "sync", "cancel", "reason", "reasonColour",
           "statusVis", "update")
    return g.data()


def g_take_pick():
    g = Graph()
    g.branch("brSaved", g.get("saved", "Saved"))
    g.set("setPick", "Picked", value="entry.SlotIndex")
    g.call("update", "UpdateSlots")
    g.flow("entry", "brSaved")
    g.flow("brSaved.else", "setPick", "update")
    return g.data()


def g_take_slot_label():
    """A..Z, then numbers (27, 28, ...)."""
    g = Graph()
    g.call("letter", KSTR + ":GetSubstring", SourceString=LETTERS, StartIndex=ref("entry.SlotIndex"), Length="1")
    g.call("next", KML + ":Add_IntInt", A=ref("entry.SlotIndex"), B="1")
    g.call("number", KSTR + ":Conv_IntToString", InInt=ref("next.ReturnValue"))
    is_letter = kml(g, "isLetter", "Less_IntInt", A=ref("entry.SlotIndex"), B=str(len(LETTERS)))
    g.call("label", KML + ":SelectString", A=ref("letter.ReturnValue"), B=ref("number.ReturnValue"), bPickA=ref(is_letter))
    g.link("label.ReturnValue", "result.Label")
    g.flow("entry", "result")
    return g.data()


def g_take_get_button():
    """Slot button ButtonIndex; created and added to the grid on first use, then reused."""
    g = Graph()
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("btns", "Buttons")))
    missing = kml(g, "missing", "GreaterEqual_IntInt", A=ref("entry.ButtonIndex"), B=ref("n.ReturnValue"))
    g.branch("br", missing)
    g.call("owner", UMG + "Widget:GetOwningPlayer")
    g.call("create", WBL + ":Create", WidgetType=cls(SLOTBTN), OwningPlayer=ref("owner.ReturnValue"))
    g.cast("asBtn", cls(SLOTBTN), "create.ReturnValue")
    g.set("setDlg", "Dialog", cls(SLOTBTN), "asBtn.$cast", g.self_())
    g.set("setIdx", "Index", cls(SLOTBTN), "asBtn.$cast", "entry.ButtonIndex")
    row = kml(g, "row", "Divide_IntInt", A=ref("entry.ButtonIndex"), B=str(SLOTS_PER_ROW))
    col = kml(g, "col", "Percent_IntInt", A=ref("entry.ButtonIndex"), B=str(SLOTS_PER_ROW))
    g.call("add", UMG + "UniformGridPanel:AddChildToUniformGrid", target=ref(g.get("grid", "Grid")),
           Content=ref("asBtn.$cast"), InRow=ref(row), InColumn=ref(col))
    g.call("keep", KARR + ":Array_Add", TargetArray=ref(g.get("btns2", "Buttons")), NewItem=ref("asBtn.$cast"))
    g.call("get", KARR + ":Array_Get", TargetArray=ref(g.get("btns3", "Buttons")), Index=ref("entry.ButtonIndex"))
    g.link("get.Item", "result.Button")
    g.flow("entry", "br", "create", "asBtn", "setDlg", "setIdx", "add", "keep", "result")
    g.flow("br.else", "result")
    g.flow("asBtn.CastFailed", "result")
    return g.data()


def g_take_update():
    """Slot buttons, labels and the save button from Picked, CurrentSlot, CanSave and Saved."""
    g = Graph()
    last = kml(g, "last", "Subtract_IntInt", A=ref(g.get("count", "SlotCount")), B="1")
    i = g.for_range("eachI", "0", ref(last))
    g.call("btn", "GetButton", ButtonIndex=ref(i))
    g.call("label", "SlotLabel", SlotIndex=ref(i))
    is_pick = kml(g, "isPick", "EqualEqual_IntInt", A=ref(i), B=ref(g.get("pick", "Picked")))
    is_cur = kml(g, "isCur", "EqualEqual_IntInt", A=ref(i), B=ref(g.get("cur", "CurrentSlot")))
    g.call("set", cls(SLOTBTN) + ":Set", target=ref("btn.Button"), Label=ref("label.Label"), Selected=ref(is_pick),
           Current=ref(is_cur))
    g.call("show", UMG + "Widget:SetVisibility", target=ref("btn.Button"), InVisibility="Visible")
    g.flow("entry", "eachI")
    g.flow("eachI.LoopBody", "btn", "label", "set", "show")
    # Buttons left from a class with more slots.
    g.call("nBtn", KARR + ":Array_Length", TargetArray=ref(g.get("btns", "Buttons")))
    last_btn = kml(g, "lastBtn", "Subtract_IntInt", A=ref("nBtn.ReturnValue"), B="1")
    j = g.for_range("eachJ", ref(g.get("count2", "SlotCount")), ref(last_btn))
    g.call("spare", KARR + ":Array_Get", TargetArray=ref(g.get("btns2", "Buttons")), Index=ref(j))
    g.call("hide", UMG + "Widget:SetVisibility", target=ref("spare.Item"), InVisibility="Collapsed")
    g.flow("eachI.Completed", "eachJ")
    g.flow("eachJ.LoopBody", "hide")
    # Texts.
    g.call("pickL", "SlotLabel", SlotIndex=ref(g.get("pick2", "Picked")))
    g.call("curL", "SlotLabel", SlotIndex=ref(g.get("cur2", "CurrentSlot")))
    g.call("now", KSTR + ":Concat_StrStr", A=ref("curL.Label"), B=" IS EQUIPPED NOW")
    set_text(g, "setNow", "NowText", ref("now.ReturnValue"))
    g.call("note1", KSTR + ":Concat_StrStr", A="Slot ", B=ref("pickL.Label"))
    g.call("note", KSTR + ":Concat_StrStr", A=ref("note1.ReturnValue"), B=" will be overwritten.")
    set_text(g, "setNote", "Note", ref("note.ReturnValue"))
    g.call("save", KSTR + ":Concat_StrStr", A="SAVE TO SLOT ", B=ref("pickL.Label"))
    set_text(g, "setSave", "SaveBtnText", ref("save.ReturnValue"))
    not_saved = kml(g, "notSaved", "Not_PreBool", A=ref(g.get("saved", "Saved")))
    enabled = kml(g, "enabled", "BooleanAND", A=ref(g.get("canSave", "CanSave")), B=ref(not_saved))
    # The whole game button (bars, fill, text) is drawn dimmed while disabled.
    wcall(g, "enSave", "SaveBtnWrap", "Widget:SetIsEnabled", bInIsEnabled=ref(enabled))
    g.flow("eachJ.Completed", "pickL", "curL", "setNow", "setNote", "setSave", "enSave")
    return g.data()


def g_take_sync_check():
    g = Graph()
    g.call("on", UMG + "CheckBox:IsChecked", target=ref(g.get("chk", "EquipAfter")))
    wcall(g, "mark", "CheckMark", "Widget:SetVisibility", InVisibility=ref(vis(g, "markV", "on.ReturnValue")))
    g.flow("entry", "mark")
    return g.data()


def g_take_save():
    g = Graph()
    not_saved = kml(g, "notSaved", "Not_PreBool", A=ref(g.get("saved", "Saved")))
    can = kml(g, "can", "BooleanAND", A=ref(g.get("canSave", "CanSave")), B=ref(not_saved))
    g.branch("br", can)
    data = g.get("data", "Data")
    g.call("equip", UMG + "CheckBox:IsChecked", target=ref(g.get("chk", "EquipAfter")))
    g.call("apply", cls(DATA) + ":ApplyCode", target=ref(data), Code=ref(g.get("code", "Code")),
           Slot=ref(g.get("pick", "Picked")), EquipAfter=ref("equip.ReturnValue"))
    g.set("setSaved", "Saved", default="true")
    set_text(g, "setMsg", "StatusText", ref("apply.Message"))
    good = kml(g, "good", "Greater_IntInt", A=ref("apply.Applied"), B="0")
    text_colour(g, "msgColour", "StatusText", pick(g, "msgC", GOOD, LIGHT, good))
    wcall(g, "showMsg", "StatusBox", "Widget:SetVisibility", InVisibility="Visible")
    g.call("info", cls(DATA) + ":SlotInfo", target=ref(data), Class=ref(g.get("cc", "CodeClass")))
    g.set("setCur", "CurrentSlot", value="info.Current")
    g.call("update", "UpdateSlots")
    set_text(g, "closeText", "CancelBtnText", "CLOSE")
    g.flow("entry", "br", "apply", "setSaved", "setMsg", "msgColour", "showMsg", "info", "setCur", "update",
           "closeText")
    return g.data()


def g_take_events():
    g = Graph()
    g.node("save", "boundevent", widget="SaveBtn", name="OnClicked")
    g.call("saveNow", "SaveNow")
    g.flow("save", "saveNow")
    g.node("cancel", "boundevent", widget="CancelBtn", name="OnClicked")
    win = g.get("win", "Window")
    valid(g, "hasWin", win)
    g.call("close", cls(WINDOW) + ":CloseTake", target=ref(win))
    g.call("hide", UMG + "Widget:SetVisibility", InVisibility="Collapsed")
    g.flow("cancel", "brHasWin", "close")
    g.flow("brHasWin.else", "hide")
    g.node("check", "boundevent", widget="EquipAfter", name="OnCheckStateChanged")
    g.call("sync", "SyncCheck")
    g.flow("check", "sync")
    press_feedback(g, "CancelBtn")  # secondary button: orange while held down
    return g.data()


# ============================================================================= DB_Window

def filter_button(i):
    """Class filter: a game button with the class icon (not on ALL), the class name and the player count."""
    return toggle_button("Filter%d" % i, FILTER_LABELS[i], F_FILTER, slot=hslot(pad=(6 if i else 0, 0, 0, 0)),
                         icon=CLASS_COLOURS[i], count=True, pad=FILTER_PAD)


def window_tree():
    # Close: a key box with the hotkey (like the game's key hints; Open sets the key's name) and a CLOSE game
    # button that also closes on click. At least square, wider for a longer key name.
    key = w("SizeBox", "KeySize", props={"MinDesiredWidth": "32", "bOverride_MinDesiredWidth": "True",
                                         "HeightOverride": "32", "bOverride_HeightOverride": "True"},
            slot=hslot(), children=[frame("Key", LIGHT, SQUARE, text("KeyText", "B", CARBON, 15, WHITE, var=True),
                                          pad=(7, 0, 7, 0))])
    # The logo (the website's: an orange hexagon with a hammer cut out), imported from Tools/dwarfbuilds/art.
    # The texture is set by InitOnce; transparent until then.
    logo = box("LogoBox", LOGO_SIZE, LOGO_SIZE, slot=hslot(pad=(0, 0, 10, 0)), child=w("Image", "Logo", var=True, props={
        "Brush": "(ImageSize=(X=%d,Y=%d))" % (LOGO_SIZE, LOGO_SIZE), "ColorAndOpacity": colour((1.0, 1.0, 1.0, 0.0))}))
    header_row = w("HorizontalBox", "HeaderRow", children=[
        logo,
        text("TitleText", "DWARF BUILDS", RIFT, 30, WHITE, slot=hslot()),
        text("CountText", "0 PLAYERS", CARBON, 14, MUTED, var=True, slot=hslot(pad=(14, 6, 0, 0))),
        w("HorizontalBox", "Tabs", slot=hslot(pad=(18, 0, 0, 0)), children=[
            toggle_button("TabTeam", "TEAM", F_HEAD_BTN, slot=hslot()),
            toggle_button("TabCode", "BUILD CODE", F_HEAD_BTN, slot=hslot(pad=(6, 0, 0, 0))),
            # BROWSE: the third tab (the user's choice, 2026-11-22); it opens the website, it has no page here.
            game_button("BrowseBtn", "BROWSE", F_HEAD_BTN, primary=False, height=BTN_H,
                        slot=hslot(pad=(6, 0, 0, 0)))]),
        w("HorizontalBox", "Filters", var=True, props={"Visibility": "Collapsed"}, slot=hslot(pad=(18, 0, 0, 0)),
          children=[filter_button(i) for i in range(5)]),
        w("Spacer", "HeaderGap", slot=hslot(fill=True)),
        w("HorizontalBox", "Paging", var=True, props={"Visibility": "Collapsed"}, slot=hslot(pad=(0, 0, 20, 0)),
          children=[
              game_button("PrevBtn", "<<", F_HEAD_BTN, primary=False, height=BTN_H, slot=hslot(), pad=ARROW_PAD),
              box("PageTextSize", width=PAGE_TEXT_W, slot=hslot(), child=text(
                  "PageText", "1-4 / 4", CARBON, 18, WHITE, var=True, justify="Center")),
              game_button("NextBtn", ">>", F_HEAD_BTN, primary=False, height=BTN_H, slot=hslot(), pad=ARROW_PAD)]),
        w("HorizontalBox", "KeyHint", slot=hslot(), children=[
            key, game_button("CloseBtn", "CLOSE", F_HEAD_BTN, primary=True, height=BTN_H, slot=hslot(pad=(8, 0, 0, 0)))]),
    ])
    # Like the game's GEAR MODIFICATIONS bar: a darker translucent bar under the orange rule, white title.
    header = box("HeaderBox", height=HEADER_H, slot=vslot(), child=border(
        "Header", HEAD_BG, header_row, pad=(20, 0, 20, 0), valign="VAlign_Center"))
    roster_fill = border("RosterFill", CARD_BG, w("HorizontalBox", "Roster", var=True),
                         pad=(20, ROSTER_PAD_V, 20, ROSTER_PAD_V))
    roster_fill["props"]["Clipping"] = "ClipToBounds"
    roster = border("RosterBar", CLEAR, roster_fill, pad=(0, 0, 0, 1), var=True, slot=vslot())
    roster["props"]["Visibility"] = "Collapsed"

    page_slot = {"Padding": margin(PAGE_PAD, PAGE_PAD_V, PAGE_PAD, PAGE_PAD_V), "HorizontalAlignment": "HAlign_Fill",
                 "VerticalAlignment": "VAlign_Fill"}
    # Columns without a player are collapsed (ShowPage), so the shown ones sit centred. The panel width follows the
    # player count (UpdateWidth): 1 to 3 players fill it unless the minimum width is wider, 4 columns fill 1760.
    # The fixed height keeps the panel the same size when no column shows.
    columns = w("HorizontalBox", "TeamPage", slot={"Padding": margin(), "HorizontalAlignment": "HAlign_Center",
                                                   "VerticalAlignment": "VAlign_Fill"}, children=[
        box("ColBox%d" % k, COLUMN_WIDTH, COLUMN_HEIGHT, slot=hslot(pad=(COLUMN_GAP if k else 0, 0, 0, 0),
                                                                    valign="VAlign_Fill"),
            child=w(cls(COLUMN), "Col%d" % k, var=True))
        for k in range(PAGE_SIZE)])
    team = box("TeamBox", height=COLUMN_HEIGHT, slot=page_slot, child=columns)

    # A multi-line box that wraps per character (a code has no spaces), so a whole code is always visible.
    code_box = w("MultiLineEditableTextBox", "CodeBox", var=True, props={
        "WidgetStyle": TEXTBOX_STYLE, "HintText": CODE_VERSION + ":...", "AutoWrapText": "True",
        "WrappingPolicy": "AllowPerCharacterWrapping"})
    code_rows = w("VerticalBox", "CodeRows", children=[
        text("CodeLabel", "PASTE A BUILD CODE", CARBON, 15, LABEL, slot=vslot()),
        box("CodeBoxSize", height=CODE_BOX_H, slot=vslot(pad=(0, 10, 0, 0)),
            child=border("CodeBoxLine", SQUARE_LINE, code_box, pad=(1, 1, 1, 1))),
        w("HorizontalBox", "CodeSideRow", slot=vslot(pad=(0, 8, 0, 0)), children=[
            game_button("PasteBtn", "PASTE FROM CLIPBOARD", F_CODE_BTN, primary=False, height=CODE_BTN_H,
                        slot=weighted(PASTE_WEIGHT), pad=CODE_BTN_PAD),
            game_button("CopyMineBtn", "COPY MY BUILD CODE", F_CODE_BTN, primary=False, height=CODE_BTN_H,
                        slot=weighted(COPY_WEIGHT, (8, 0, 0, 0)), pad=CODE_BTN_PAD)]),
        text("CodeStatus", CODE_HINT, CARBON, 16, LABEL, var=True, slot=vslot(pad=(0, 16, 0, 0))),
        text("CopyNote", " ", CARBON, 15, LABEL, var=True, slot=vslot(pad=(0, 6, 0, 0))),
        text("CodeHelp", "A build code holds the items, upgrades, overclocks and perks of one class. COPY CODE "
                         "under a player copies theirs; TAKE BUILD saves a code into one of your loadouts.",
             BODY, 19, LABEL, wrap=True, slot=vslot(pad=(0, 12, 0, 0))),
        # The website: share your build, find others.
        text("SiteLabel", "DWARFBUILDS.PAGES.DEV", CARBON, 15, LABEL, slot=vslot(pad=(0, 24, 0, 0))),
        w("HorizontalBox", "SiteRow", slot=vslot(pad=(0, 10, 0, 0)), children=[
            game_button("PublishBtn", "PUBLISH MY BUILD", F_CODE_BTN, primary=False, height=CODE_BTN_H,
                        slot=weighted(1), pad=CODE_BTN_PAD),
            game_button("BrowserBtn", "OPEN IN BROWSER", F_CODE_BTN, primary=False, height=CODE_BTN_H,
                        slot=weighted(1, (8, 0, 0, 0)), pad=CODE_BTN_PAD)]),
        text("SiteHelp", "PUBLISH MY BUILD opens the website in the Steam overlay with your build filled in. Copy a "
                         "code there and press PASTE FROM CLIPBOARD here. OPEN IN BROWSER opens the website in your web browser "
                         "(also when the Steam overlay is off).",
             BODY, 17, LABEL, wrap=True, slot=vslot(pad=(0, 10, 0, 0))),
        w("Spacer", "CodeGap", slot=vslot(fill=True)),
        # Primary action, disabled (dimmed) until the code is valid.
        game_button("TakeCodeBtn", "TAKE BUILD", 24, primary=True, height=56, slot=vslot(), enabled=False),
    ])
    # A card like the game's: orange top rule over translucent black.
    code_card = w("VerticalBox", "CodeCard", slot=hslot(fill=True, valign="VAlign_Fill"), children=[
        image("CodeRule", ORANGE, size=(32, 3), slot=vslot()),
        border("CodeFill", CARD_BG, code_rows, pad=(28, 21, 28, 24), slot=vslot(fill=True))])
    code = w("HorizontalBox", "CodePage", slot=page_slot, children=[
        code_card,
        box("PreviewBox", COLUMN_WIDTH, COLUMN_HEIGHT, slot=hslot(pad=(COLUMN_GAP, 0, 0, 0), valign="VAlign_Fill"),
            child=w(cls(COLUMN), "Preview", var=True)),
    ])
    pages = w("WidgetSwitcher", "Pages", var=True, slot=vslot(), children=[team, code])

    rows = w("VerticalBox", "PanelRows", children=[
        header, image("HeaderLine", CLEAR, size=(32, 1), slot=vslot()), roster, pages])
    # The panel: orange top rule over translucent black (PanelEdge only keeps the 1 px frame size).
    panel = box("PanelBox", width=PANEL_WIDTH, var=True, slot=oslot("HAlign_Center", "VAlign_Center"), child=border(
        "PanelEdge", CLEAR, w("VerticalBox", "PanelCol", children=[
            image("TopRule", ORANGE, size=(32, 3), slot=vslot()),
            border("PanelFill", PANEL_BG, rows, slot=vslot())]),
        pad=(1, 0, 1, 1)))
    # Fit to screen: FitToScreen sets a scale below 1 when the panel does not fit (1920x1080 at 100 % UI scale: about
    # 0.98 without the roster strip, 0.93 with it). A fixed (user-specified) scale: ScaleToFit would run an extra
    # layout pass of the whole panel every frame.
    fit = w("ScaleBox", "Fit", var=True, props={"Stretch": "UserSpecified", "UserSpecifiedScale": "1.0"},
            slot=oslot(pad=(FIT_PAD,) * 4), children=[panel])
    return w("Overlay", "Root", children=[
        border("Dim", BACKDROP, slot=oslot()),
        fit,
        w(cls(TAKE), "Take", var=True, props={"Visibility": "Collapsed"}, slot=oslot()),
    ])


def g_win_open():
    """Called by DB_Mod after the window is shown and Data is set."""
    g = Graph()
    me = g.self_()
    valid(g, "hasData", g.get("data", "Data"))
    g.node("cols", "makearray", n=PAGE_SIZE)
    for k in range(PAGE_SIZE):
        g.link(g.get("col%d" % k, "Col%d" % k), "cols.[%d]" % k)
    g.set("setCols", "Columns", value="cols.Array")
    chain = ["entry", "brHasData", "setCols"]
    for name in ["Col%d" % k for k in range(PAGE_SIZE)] + ["Preview"]:
        col = g.get("w" + name, name)
        g.set("win" + name, "Window", cls(COLUMN), col, me)
        g.set("data" + name, "Data", cls(COLUMN), col, g.get("d" + name, "Data"))
        chain += ["win" + name, "data" + name]
    take = g.get("take", "Take")
    g.set("winTake", "Window", cls(TAKE), take, me)
    g.set("dataTake", "Data", cls(TAKE), take, g.get("dTake", "Data"))
    g.call("closeTake", "CloseTake")
    # A reused window starts on ALL, first page.
    g.set("noFilter", "Filter", default="0")
    g.set("firstPage", "PageStart", default="0")
    g.branch("brInit", g.get("inited", "Inited"))
    g.call("init", "InitOnce")
    g.set("setInit", "Inited", default="true")
    g.call("refresh", "Refresh")
    g.call("stop", KSL + ":K2_ClearTimer", Object=ref(me), FunctionName="TimerRefresh")
    g.call("timer", KSL + ":K2_SetTimer", Object=ref(me), FunctionName="TimerRefresh", Time="1.0", bLooping="true")
    g.call("focus", UMG + "Widget:SetKeyboardFocus")
    # The key hint: the hotkey's name (it may have been changed in Mod Hub since the last time).
    g.call("hotkey", cls(DATA) + ":OpenKey", target=ref(g.get("dKey", "Data")))
    g.call("hotkeyName", INPUTLIB + ":Key_GetDisplayName", Key=ref("hotkey.Key"))
    g.call("hotkeyUp", KTXT + ":TextToUpper", InText=ref("hotkeyName.ReturnValue"))
    wcall(g, "keyHint", "KeyText", "TextBlock:SetText", InText=ref("hotkeyUp.ReturnValue"))
    # The fit-to-screen scale is set by Refresh (UpdateHeader -> FitToScreen): it depends on the roster strip.
    chain += ["winTake", "dataTake", "closeTake", "noFilter", "firstPage", "brInit", "refresh", "stop",
              "timer", "focus", "hotkey", "keyHint"]
    g.flow(*chain)
    g.flow("brInit.else", "init", "setInit", "refresh")
    return g.data()


def g_win_fit():
    """Scale = min(1, free width / panel width, free height / panel height), in Slate units (pixels / DPI scale).
    The panel width is the current one (PanelWidth, set by UpdateWidth before this runs); the panel is taller with
    the roster strip. Runs on every refresh, so it also follows a resized viewport; the ScaleBox does nothing when
    the scale has not changed."""
    g = Graph()
    g.call("vpSize", UMG + "WidgetLayoutLibrary:GetViewportSize")
    g.call("vpScale", UMG + "WidgetLayoutLibrary:GetViewportScale")
    g.call("vpBreak", KML + ":BreakVector2D", InVec=ref("vpSize.ReturnValue"))
    g.call("dpi", KML + ":FMax", A=ref("vpScale.ReturnValue"), B="0.1")
    g.call("freeW", KML + ":Divide_FloatFloat", A=ref("vpBreak.X"), B=ref("dpi.ReturnValue"))
    g.call("freeH", KML + ":Divide_FloatFloat", A=ref("vpBreak.Y"), B=ref("dpi.ReturnValue"))
    g.call("panelR", KML + ":SelectFloat", A=str(PANEL_FIT_HEIGHT + 2 * FIT_PAD), B=str(PANEL_HEIGHT + 2 * FIT_PAD),
           bPickA=ref("entry.WithRoster"))
    panel_w = kml(g, "panelW", "Add_IntInt", A=ref(g.get("pw", "PanelWidth")), B=str(2 * FIT_PAD))
    panel_wf = kml(g, "panelWF", "Conv_IntToFloat", InInt=ref(panel_w))
    g.call("fitW", KML + ":Divide_FloatFloat", A=ref("freeW.ReturnValue"), B=ref(panel_wf))
    g.call("fitH", KML + ":Divide_FloatFloat", A=ref("freeH.ReturnValue"), B=ref("panelR.ReturnValue"))
    g.call("fitMin", KML + ":FMin", A=ref("fitW.ReturnValue"), B=ref("fitH.ReturnValue"))
    g.call("fitOne", KML + ":FMin", A=ref("fitMin.ReturnValue"), B="1.0")
    g.call("fitClamp", KML + ":FMax", A=ref("fitOne.ReturnValue"), B="0.3")
    g.call("setFit", UMG + "ScaleBox:SetUserSpecifiedScale", target=ref(g.get("fit", "Fit")),
           InUserSpecifiedScale=ref("fitClamp.ReturnValue"))
    g.flow("entry", "setFit")
    return g.data()


def g_win_init_once():
    """Class icons on the filter buttons (from a code that has only a class and one item, so it is valid), and an
    empty preview."""
    g = Graph()
    data = g.get("data", "Data")
    tails = ["entry"]  # exec outputs that lead to the next step
    for i, letter in enumerate(CLASS_LETTERS, 1):
        g.call("head%d" % i, cls(DATA) + ":HeaderOfCode", target=ref(data),
               Code="%s:%s:1--0%s:" % (CODE_VERSION, letter, ":0--0" * (len(SLOTS) - 1)))
        valid(g, "icon%dOk" % i, "head%d.Icon" % i)
        # Both variants of the filter button (Off: class colour, On: black on orange).
        for suffix in ("Off", "On"):
            wcall(g, "icon%d%s" % (i, suffix), "Filter%d%sIcon" % (i, suffix), "Image:SetBrushFromTexture",
                  Texture=ref("head%d.Icon" % i), bMatchSize="false")
        for tail in tails:
            g.flow(tail, "head%d" % i)
        g.flow("head%d" % i, "brIcon%dOk" % i, "icon%dOff" % i, "icon%dOn" % i)
        tails = ["icon%dOn" % i, "brIcon%dOk.else" % i]
    g.call("clear", cls(COLUMN) + ":Clear", target=ref(g.get("preview", "Preview")))
    for tail in tails:
        g.flow(tail, "clear")
    # The logo texture, loaded by path (a brush ResourceObject set through BPForge did not keep the reference).
    tex = soft_load(g, "logoTex", TEX_LOGO)
    wcall(g, "setLogo", "Logo", "Image:SetBrushFromTexture", Texture=ref(tex), bMatchSize="false")
    wcall(g, "showLogo", "Logo", "Image:SetOpacity", InOpacity="1.0")
    g.flow("clear", "logoTexLoad", "logoTex", "setLogo", "showLogo")
    return g.data()


def g_win_refresh():
    """UpdateWidth runs before UpdateHeader: FitToScreen (called there) uses the new width."""
    g = Graph()
    valid(g, "hasData", g.get("data", "Data"))
    for fn in ("Collect", "UpdateWidth", "ShowPage", "UpdateHeader", "UpdateRoster"):
        g.call("do" + fn, fn)
    g.flow("entry", "brHasData", "doCollect", "doUpdateWidth", "doShowPage", "doUpdateHeader", "doUpdateRoster")
    return g.data()


def g_win_update_width():
    """Panel width from the player count, the same on both tabs (the window does not jump when the tab changes):
    max(PANEL_MIN_WIDTH, the width of min(players, 4) columns). With 4 or more players it is 1760 (filters, paging
    and the roster need it). The SizeBox is set only when the width changes."""
    g = Graph()
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("pl", "Players")))
    cols = kml(g, "cols", "Min", A=ref("n.ReturnValue"), B=str(PAGE_SIZE))
    span = kml(g, "span", "Multiply_IntInt", A=ref(cols), B=str(COLUMN_WIDTH + COLUMN_GAP))
    # panel_width(c) = c * (COLUMN_WIDTH + COLUMN_GAP) + (panel_width(0) = 2 * PAGE_PAD + 2 - COLUMN_GAP)
    need = kml(g, "need", "Add_IntInt", A=ref(span), B=str(panel_width(0)))
    width = kml(g, "width", "Max", A=ref(need), B=str(PANEL_MIN_WIDTH))
    g.branch("brSame", kml(g, "same", "EqualEqual_IntInt", A=ref(width), B=ref(g.get("old", "PanelWidth"))))
    g.set("setWidth", "PanelWidth", value=width)
    wcall(g, "setBox", "PanelBox", "SizeBox:SetWidthOverride",
          InWidthOverride=ref(kml(g, "widthF", "Conv_IntToFloat", InInt=ref(width))))
    g.flow("entry", "brSame")
    g.flow("brSame.else", "setWidth", "setBox")
    return g.data()


def g_win_timer_refresh():
    """The 1 s timer: refresh while open, else stop (the game may close the window
    without telling us)."""
    g = Graph()
    g.call("open", "IsOpenNow")
    g.branch("br", "open.bOpen")
    g.call("refresh", "Refresh")
    g.call("tips", "HideAllTips")
    g.call("stop", "Stop")
    g.flow("entry", "open", "br", "refresh")
    g.flow("br.else", "tips", "stop")
    return g.data()


def g_win_collect():
    """Players, their class (filter index), counts per class, the players of the filter, a valid page start."""
    g = Graph()
    g.call("players", cls(DATA) + ":GetPlayers", target=ref(g.get("data", "Data")))
    g.set("setPlayers", "Players", value="players.Players")
    g.call("clearCls", KARR + ":Array_Clear", TargetArray=ref(g.get("pcls0", "PlayerClass")))
    g.call("clearCnt", KARR + ":Array_Clear", TargetArray=ref(g.get("cnt0", "ClassCounts")))
    g.call("sizeCnt", KARR + ":Array_Resize", TargetArray=ref(g.get("cnt1", "ClassCounts")), Size="5")
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("pl0", "Players")))
    g.call("setAll", KARR + ":Array_Set", TargetArray=ref(g.get("cnt2", "ClassCounts")), Index="0",
           Item=ref("n.ReturnValue"), bSizeToFit="false")
    element = g.loop("each", g.get("pl1", "Players"))
    g.call("ci", "ClassIndex", Player=ref(element))
    g.call("addCls", KARR + ":Array_Add", TargetArray=ref(g.get("pcls1", "PlayerClass")), NewItem=ref("ci.Index"))
    g.branch("brKnown", kml(g, "known", "Greater_IntInt", A=ref("ci.Index"), B="0"))
    g.call("old", KARR + ":Array_Get", TargetArray=ref(g.get("cnt3", "ClassCounts")), Index=ref("ci.Index"))
    inc = kml(g, "inc", "Add_IntInt", A=ref("old.Item"), B="1")
    g.call("setCnt", KARR + ":Array_Set", TargetArray=ref(g.get("cnt4", "ClassCounts")), Index=ref("ci.Index"),
           Item=ref(inc), bSizeToFit="false")
    # With 4 or fewer players the filter bar is hidden: show ALL, or a filter could hide players with no way back.
    g.branch("brSmall", kml(g, "small", "LessEqual_IntInt", A=ref("n.ReturnValue"), B=str(PAGE_SIZE)))
    g.set("filterAll", "Filter", default="0")
    g.flow("entry", "players", "setPlayers", "clearCls", "clearCnt", "sizeCnt", "setAll", "brSmall", "filterAll",
           "each.Exec")
    g.flow("brSmall.else", "each.Exec")
    g.flow("each.LoopBody", "ci", "addCls", "brKnown", "setCnt")
    # Players of the filter.
    g.call("clearShown", KARR + ":Array_Clear", TargetArray=ref(g.get("sh0", "Shown")))
    g.call("nc", KARR + ":Array_Length", TargetArray=ref(g.get("pcls2", "PlayerClass")))
    last = kml(g, "last", "Subtract_IntInt", A=ref("nc.ReturnValue"), B="1")
    i = g.for_range("eachI", "0", ref(last))
    every = kml(g, "every", "EqualEqual_IntInt", A=ref(g.get("f0", "Filter")), B="0")
    g.call("pc", KARR + ":Array_Get", TargetArray=ref(g.get("pcls3", "PlayerClass")), Index=ref(i))
    same = kml(g, "same", "EqualEqual_IntInt", A=ref("pc.Item"), B=ref(g.get("f1", "Filter")))
    g.branch("brMatch", kml(g, "match", "BooleanOR", A=ref(every), B=ref(same)))
    g.call("addShown", KARR + ":Array_Add", TargetArray=ref(g.get("sh1", "Shown")), NewItem=ref(i))
    g.flow("each.Completed", "clearShown", "eachI")
    g.flow("eachI.LoopBody", "brMatch", "addShown")
    # Page start: a multiple of 4, at most the start of the last page (players leave).
    g.call("m", KARR + ":Array_Length", TargetArray=ref(g.get("sh2", "Shown")))
    m_last = kml(g, "mLast", "Subtract_IntInt", A=ref("m.ReturnValue"), B="1")
    last_page = kml(g, "lastPage", "Divide_IntInt", A=ref(m_last), B=str(PAGE_SIZE))
    last_start = kml(g, "lastStart", "Multiply_IntInt", A=ref(last_page), B=str(PAGE_SIZE))
    last_ok = kml(g, "lastOk", "Max", A=ref(last_start), B="0")
    ps = g.get("ps0", "PageStart")
    rem = kml(g, "rem", "Percent_IntInt", A=ref(ps), B=str(PAGE_SIZE))
    aligned = kml(g, "aligned", "Subtract_IntInt", A=ref(ps), B=ref(rem))
    start = kml(g, "start", "Min", A=ref(aligned), B=ref(last_ok))
    g.set("setStart", "PageStart", value=start)
    g.flow("eachI.Completed", "setStart")
    return g.data()


def g_win_class_index():
    """Filter index of a player's class: 1..4 for D, E, G, S (first letter of the PlayerCharacterID), 0 = none."""
    g = Graph()
    g.call("id", PS + ":GetSelectedCharacterID", target=ref("entry.Player"))
    g.call("name", KSL + ":GetObjectName", Object=ref("id.ReturnValue"))
    g.call("letter", KSTR + ":GetSubstring", SourceString=ref("name.ReturnValue"), StartIndex="0", Length="1")
    g.call("pos", KSTR + ":FindSubstring", SearchIn=CLASS_LETTERS, Substring=ref("letter.ReturnValue"), bUseCase="true")
    g.link(kml(g, "index", "Add_IntInt", A=ref("pos.ReturnValue"), B="1"), "result.Index")
    g.flow("entry", "result")
    return g.data()


def g_win_show_page():
    """The 4 columns of the page; columns skip unchanged players themselves. Only on the TEAM tab.
    A column without a player is collapsed with its box (ColBox, the column's parent), so the shown columns sit
    centred on the page."""
    g = Graph()
    g.branch("brTeam", kml(g, "team", "EqualEqual_IntInt", A=ref(g.get("tab", "Tab")), B="0"))
    k = g.for_range("eachK", "0", str(PAGE_SIZE - 1))
    idx = kml(g, "idx", "Add_IntInt", A=ref(g.get("ps", "PageStart")), B=ref(k))
    g.call("m", KARR + ":Array_Length", TargetArray=ref(g.get("sh0", "Shown")))
    g.branch("brHas", kml(g, "has", "Less_IntInt", A=ref(idx), B=ref("m.ReturnValue")))
    g.call("col", KARR + ":Array_Get", TargetArray=ref(g.get("cols", "Columns")), Index=ref(k))
    g.call("pi", KARR + ":Array_Get", TargetArray=ref(g.get("sh1", "Shown")), Index=ref(idx))
    g.call("player", KARR + ":Array_Get", TargetArray=ref(g.get("pl", "Players")), Index=ref("pi.Item"))
    g.call("show", cls(COLUMN) + ":ShowPlayer", target=ref("col.Item"), Player=ref("player.Item"))
    g.call("clear", cls(COLUMN) + ":Clear", target=ref("col.Item"))
    g.call("colBox", UMG + "Widget:GetParent", target=ref("col.Item"))
    # SelfHitTestInvisible is the SizeBox default.
    g.call("showBox", UMG + "Widget:SetVisibility", target=ref("colBox.ReturnValue"), InVisibility="SelfHitTestInvisible")
    g.call("hideBox", UMG + "Widget:SetVisibility", target=ref("colBox.ReturnValue"), InVisibility="Collapsed")
    g.flow("entry", "brTeam", "eachK")
    g.flow("eachK.LoopBody", "brHas", "show", "showBox")
    g.flow("brHas.else", "clear", "hideBox")
    return g.data()


def g_win_update_header():
    g = Graph()
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("pl", "Players")))
    g.call("m", KARR + ":Array_Length", TargetArray=ref(g.get("sh", "Shown")))
    n, m = "n.ReturnValue", "m.ReturnValue"
    big = kml(g, "big", "Greater_IntInt", A=ref(n), B=str(PAGE_SIZE))
    team = kml(g, "team", "EqualEqual_IntInt", A=ref(g.get("tab", "Tab")), B="0")
    big_team = kml(g, "bigTeam", "BooleanAND", A=ref(big), B=ref(team))
    one = kml(g, "one", "EqualEqual_IntInt", A=ref(n), B="1")
    word = kml(g, "word", "SelectString", A="PLAYER", B="PLAYERS", bPickA=ref(one))
    g.node("countFmt", "formattext", format="{N} {W}")
    g.link(n, "countFmt.N")
    g.link(word, "countFmt.W")
    wcall(g, "setCount", "CountText", "TextBlock:SetText", InText=ref("countFmt.Result"))
    chain = ["entry", "setCount"]
    # Filters, paging and roster only with more than 4 players, on the TEAM tab. The count only without the
    # filters (the ALL filter shows the same number; the header needs the room for BROWSE).
    for name in ("Filters", "Paging", "RosterBar"):
        wcall(g, "vis" + name, name, "Widget:SetVisibility", InVisibility=ref(vis(g, "v" + name, big_team)))
        chain.append("vis" + name)
    small_team = kml(g, "smallTeam", "Not_PreBool", A=ref(big_team))
    wcall(g, "visCount", "CountText", "Widget:SetVisibility",
          InVisibility=ref(vis(g, "vCount", small_team, "HitTestInvisible")))
    chain.append("visCount")
    # The roster strip makes the panel taller: fit the panel to the screen again.
    g.call("fit", "FitToScreen", WithRoster=ref(big_team))
    chain.append("fit")
    # "5-8 / 16"
    ps = g.get("ps", "PageStart")
    first = kml(g, "first", "Add_IntInt", A=ref(ps), B="1")
    some = kml(g, "some", "Greater_IntInt", A=ref(m), B="0")
    first_shown = kml(g, "firstShown", "SelectInt", A=ref(first), B="0", bPickA=ref(some))
    end = kml(g, "end", "Add_IntInt", A=ref(ps), B=str(PAGE_SIZE))
    last = kml(g, "last", "Min", A=ref(end), B=ref(m))
    g.node("pageFmt", "formattext", format="{A}-{B} / {C}")
    g.link(first_shown, "pageFmt.A")
    g.link(last, "pageFmt.B")
    g.link(m, "pageFmt.C")
    wcall(g, "setPage", "PageText", "TextBlock:SetText", InText=ref("pageFmt.Result"))
    chain.append("setPage")
    can_prev = kml(g, "canPrev", "Greater_IntInt", A=ref(ps), B="0")
    can_next = kml(g, "canNext", "Less_IntInt", A=ref(end), B=ref(m))
    # A disabled game button is drawn dimmed as a whole.
    for name, cond in (("PrevBtn", can_prev), ("NextBtn", can_next)):
        wcall(g, "en" + name, name + "Wrap", "Widget:SetIsEnabled", bInIsEnabled=ref(cond))
        chain.append("en" + name)
    # Filter counts and the selected filter (WidgetSwitcher index 1 = the orange variant).
    for i in range(5):
        g.call("cnt%d" % i, KARR + ":Array_Get", TargetArray=ref(g.get("cnts%d" % i, "ClassCounts")), Index=str(i))
        g.call("cntT%d" % i, KTXT + ":Conv_IntToText", Value=ref("cnt%d.Item" % i))
        for suffix in ("Off", "On"):
            wcall(g, "setCnt%d%s" % (i, suffix), "Filter%d%sCount" % (i, suffix), "TextBlock:SetText",
                  InText=ref("cntT%d.ReturnValue" % i))
        sel = kml(g, "sel%d" % i, "EqualEqual_IntInt", A=ref(g.get("flt%d" % i, "Filter")), B=str(i))
        on = kml(g, "on%d" % i, "SelectInt", A="1", B="0", bPickA=ref(sel))
        wcall(g, "pickF%d" % i, "Filter%d" % i, "WidgetSwitcher:SetActiveWidgetIndex", Index=ref(on))
        chain += ["setCnt%dOff" % i, "setCnt%dOn" % i, "pickF%d" % i]
    # Tabs: the selected one is the orange (primary) game button.
    for k, name in enumerate(("TabTeam", "TabCode")):
        sel = kml(g, "tsel%d" % k, "EqualEqual_IntInt", A=ref(g.get("tabk%d" % k, "Tab")), B=str(k))
        on = kml(g, "ton%d" % k, "SelectInt", A="1", B="0", bPickA=ref(sel))
        wcall(g, "pickT%d" % k, name, "WidgetSwitcher:SetActiveWidgetIndex", Index=ref(on))
        chain.append("pickT%d" % k)
    g.flow(*chain)
    return g.data()


def g_win_roster_same():
    """Whether the chips already show what UpdateRoster would draw: the same players in the same order, each with
    the same class and name, and the same filter (Shown) and page. Records them for the next call."""
    g = Graph()
    g.call("clearC", KARR + ":Array_Clear", TargetArray=ref(g.get("c0", "RsClasses")))
    g.call("clearN", KARR + ":Array_Clear", TargetArray=ref(g.get("n0", "RsNames")))
    player = g.loop("each", g.get("pl0", "Players"))
    valid(g, "player", player)
    g.call("cls", PS + ":GetSelectedCharacterID", target=ref(player))
    g.call("name", PLAYERSTATE + ":GetPlayerName", target=ref(player))
    g.call("addC", KARR + ":Array_Add", TargetArray=ref(g.get("c1", "RsClasses")), NewItem=ref("cls.ReturnValue"))
    g.call("addN", KARR + ":Array_Add", TargetArray=ref(g.get("n1", "RsNames")), NewItem=ref("name.ReturnValue"))
    g.flow("entry", "clearC", "clearN", "each.Exec")
    g.flow("each.LoopBody", "brPlayer", "addC", "addN")
    same = kml(g, "samePage", "EqualEqual_IntInt", A=ref(g.get("ps", "PageStart")), B=ref(g.get("rpPage", "RpPage")))
    for k, (now, last) in enumerate((("Players", "RpPlayers"), ("Shown", "RpShown"), ("RsClasses", "RpClasses"),
                                     ("RsNames", "RpNames"))):
        g.call("same%d" % k, KARR + ":Array_Identical", ArrayA=ref(g.get("a%d" % k, now)),
               ArrayB=ref(g.get("b%d" % k, last)))
        same = kml(g, "and%d" % k, "BooleanAND", A=ref(same), B=ref("same%d.ReturnValue" % k))
        g.set("keep%d" % k, last, value=g.get("k%d" % k, now))
    g.set("setSame", "RsSame", value=same)
    g.set("keepPage", "RpPage", value=g.get("ps2", "PageStart"))
    g.flow("each.Completed", "setSame", "keep0", "keep1", "keep2", "keep3", "keepPage", "result")
    g.link(g.get("out", "RsSame"), "result.Same")
    return g.data()


def g_win_update_roster():
    """One chip per player. Chips are created once and reused. Nothing to do while the roster is hidden
    (4 or fewer players, or the BUILD CODE tab): SelectPlayer and SetTab refresh it when it shows again. Nothing
    to do either while it shows what it showed (RosterSame): the 1 s refresh then sets no chip."""
    g = Graph()
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("pl", "Players")))
    n = "n.ReturnValue"
    big = kml(g, "big", "Greater_IntInt", A=ref(n), B=str(PAGE_SIZE))
    team = kml(g, "team", "EqualEqual_IntInt", A=ref(g.get("tab", "Tab")), B="0")
    g.branch("brBig", kml(g, "rosterOn", "BooleanAND", A=ref(big), B=ref(team)))
    # Chip width = min(150, (roster width - gaps) / n).
    gaps = kml(g, "gaps", "Subtract_IntInt", A=ref(n), B="1")
    gap_w = kml(g, "gapW", "Multiply_IntInt", A=ref(gaps), B=str(CHIP_GAP))
    free = kml(g, "free", "Subtract_IntInt", A=str(ROSTER_WIDTH), B=ref(gap_w))
    each = kml(g, "each", "Divide_IntInt", A=ref(free), B=ref(n))
    cap = kml(g, "cap", "Min", A=ref(each), B=str(CHIP_MAX))
    g.set("setW", "ChipWidth", value=kml(g, "capF", "Conv_IntToFloat", InInt=ref(cap)))
    last = kml(g, "last", "Subtract_IntInt", A=ref(n), B="1")
    i = g.for_range("eachI", "0", ref(last))
    g.call("chip", "GetChip", ChipIndex=ref(i))
    g.call("player", KARR + ":Array_Get", TargetArray=ref(g.get("pl2", "Players")), Index=ref(i))
    g.call("head", cls(DATA) + ":HeaderOf", target=ref(g.get("data", "Data")), Player=ref("player.Item"))
    g.call("pos", KARR + ":Array_Find", TargetArray=ref(g.get("sh", "Shown")), ItemToFind=ref(i))
    ps = g.get("ps", "PageStart")
    from_ok = kml(g, "fromOk", "GreaterEqual_IntInt", A=ref("pos.ReturnValue"), B=ref(ps))
    end = kml(g, "end", "Add_IntInt", A=ref(ps), B=str(PAGE_SIZE))
    to_ok = kml(g, "toOk", "Less_IntInt", A=ref("pos.ReturnValue"), B=ref(end))
    on_page = kml(g, "onPage", "BooleanAND", A=ref(from_ok), B=ref(to_ok))
    chip = "chip.Chip"
    g.call("set", cls(CHIP) + ":Set", target=ref(chip), PlayerName=ref("head.Name"), Color=ref("head.Color"),
           Selected=ref(on_page), IsYou=ref("head.IsYou"))
    g.call("icon", cls(CHIP) + ":SetIcon", target=ref(chip), Texture=ref("head.Icon"))
    g.call("width", cls(CHIP) + ":SetWidth", target=ref(chip), Width=ref(g.get("cw", "ChipWidth")))
    g.call("show", UMG + "Widget:SetVisibility", target=ref(chip), InVisibility="Visible")
    g.call("drawn", "RosterSame")
    g.branch("brDrawn", "drawn.Same")
    g.flow("entry", "brBig", "drawn", "brDrawn")
    g.flow("brDrawn.else", "setW", "eachI")
    g.flow("eachI.LoopBody", "chip", "head", "set", "icon", "width", "show")
    # Chips of players who left.
    g.call("nChips", KARR + ":Array_Length", TargetArray=ref(g.get("chips", "Chips")))
    last_chip = kml(g, "lastChip", "Subtract_IntInt", A=ref("nChips.ReturnValue"), B="1")
    j = g.for_range("eachJ", ref(n), ref(last_chip))
    g.call("spare", KARR + ":Array_Get", TargetArray=ref(g.get("chips2", "Chips")), Index=ref(j))
    g.call("hide", UMG + "Widget:SetVisibility", target=ref("spare.Item"), InVisibility="Collapsed")
    g.flow("eachI.Completed", "eachJ")
    g.flow("eachJ.LoopBody", "hide")
    return g.data()


def g_win_get_chip():
    g = Graph()
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("chips", "Chips")))
    g.branch("br", kml(g, "missing", "GreaterEqual_IntInt", A=ref("entry.ChipIndex"), B=ref("n.ReturnValue")))
    g.call("owner", UMG + "Widget:GetOwningPlayer")
    g.call("create", WBL + ":Create", WidgetType=cls(CHIP), OwningPlayer=ref("owner.ReturnValue"))
    g.cast("asChip", cls(CHIP), "create.ReturnValue")
    g.set("setWin", "Window", cls(CHIP), "asChip.$cast", g.self_())
    g.set("setIdx", "Index", cls(CHIP), "asChip.$cast", "entry.ChipIndex")
    g.call("add", UMG + "HorizontalBox:AddChildToHorizontalBox", target=ref(g.get("roster", "Roster")),
           Content=ref("asChip.$cast"))
    g.node("pad", "makestruct", struct=MARGIN)
    g.defaults["pad.Right"] = str(CHIP_GAP)
    g.call("setPad", UMG + "HorizontalBoxSlot:SetPadding", target=ref("add.ReturnValue"), InPadding=ref("pad.Margin"))
    g.call("keep", KARR + ":Array_Add", TargetArray=ref(g.get("chips2", "Chips")), NewItem=ref("asChip.$cast"))
    g.call("get", KARR + ":Array_Get", TargetArray=ref(g.get("chips3", "Chips")), Index=ref("entry.ChipIndex"))
    g.link("get.Item", "result.Chip")
    g.flow("entry", "br", "create", "asChip", "setWin", "setIdx", "add", "setPad", "keep", "result")
    g.flow("br.else", "result")
    g.flow("asChip.CastFailed", "result")
    return g.data()


def g_win_select_player():
    """From a roster chip: filter ALL, the page with that player, TEAM tab."""
    g = Graph()
    g.set("all", "Filter", default="0")
    rem = kml(g, "rem", "Percent_IntInt", A=ref("entry.PlayerIndex"), B=str(PAGE_SIZE))
    g.set("page", "PageStart", value=kml(g, "start", "Subtract_IntInt", A=ref("entry.PlayerIndex"), B=ref(rem)))
    g.call("tab", "SetTab", NewTab="0")
    g.flow("entry", "all", "page", "tab")
    return g.data()


def g_win_set_filter():
    g = Graph()
    g.set("filter", "Filter", value="entry.NewFilter")
    g.set("page", "PageStart", default="0")
    g.call("refresh", "Refresh")
    g.flow("entry", "filter", "page", "refresh")
    return g.data()


def g_win_set_tab():
    g = Graph()
    g.set("tab", "Tab", value="entry.NewTab")
    wcall(g, "switch", "Pages", "WidgetSwitcher:SetActiveWidgetIndex", Index=ref("entry.NewTab"))
    g.call("refresh", "Refresh")
    g.flow("entry", "tab", "switch", "refresh")
    return g.data()


def g_win_page_by():
    g = Graph()
    start = kml(g, "start", "Add_IntInt", A=ref(g.get("ps", "PageStart")), B=ref("entry.Step"))
    g.call("m", KARR + ":Array_Length", TargetArray=ref(g.get("sh", "Shown")))
    low = kml(g, "low", "GreaterEqual_IntInt", A=ref(start), B="0")
    high = kml(g, "high", "Less_IntInt", A=ref(start), B=ref("m.ReturnValue"))
    g.branch("br", kml(g, "ok", "BooleanAND", A=ref(low), B=ref(high)))
    g.set("setStart", "PageStart", value=start)
    g.call("refresh", "Refresh")
    g.flow("entry", "br", "setStart", "refresh")
    return g.data()


def g_win_open_take():
    g = Graph()
    take = g.get("take", "Take")
    g.call("show", cls(TAKE) + ":Show", target=ref(take), NewCode=ref("entry.NewCode"), Title=ref("entry.Title"))
    g.call("visible", UMG + "Widget:SetVisibility", target=ref(take), InVisibility="Visible")
    g.set("open", "TakeOpen", default="true")
    g.flow("entry", "show", "visible", "open")
    return g.data()


def g_win_close_take():
    g = Graph()
    wcall(g, "hide", "Take", "Widget:SetVisibility", InVisibility="Collapsed")
    g.set("closed", "TakeOpen", default="false")
    g.call("focus", UMG + "Widget:SetKeyboardFocus")
    g.flow("entry", "hide", "closed", "focus")
    return g.data()


def g_win_dismiss():
    """Closes the window: through the window manager, or by hand when DB_Mod opened it by hand. A tooltip shown at
    that moment is hidden first, or it could stay on screen."""
    g = Graph()
    g.call("tips", "HideAllTips")
    g.branch("br", g.get("manual", "Manual"))
    g.call("owner", UMG + "Widget:GetOwningPlayer")
    g.call("game", WBL + ":SetInputMode_GameOnly", PlayerController=ref("owner.ReturnValue"))
    g.set("cursor", "bShowMouseCursor", PLAYERCONTROLLER, "owner.ReturnValue", default="false")
    g.call("remove", UMG + "Widget:RemoveFromParent")
    g.call("stop", "Stop")
    g.call("close", WINDOWWIDGET + ":CloseThisWindow")
    g.call("stop2", "Stop")
    g.flow("entry", "tips", "br", "game", "cursor", "remove", "stop")
    g.flow("br.else", "close", "stop2")
    return g.data()


def g_win_hide_tips():
    """Data.HideTips: collapses every tooltip of the mod (a cell shows its tip again on the next hover)."""
    g = Graph()
    data = g.get("data", "Data")
    valid(g, "hasData", data)
    g.call("hide", cls(DATA) + ":HideTips", target=ref(data))
    g.flow("entry", "brHasData", "hide")
    return g.data()


def g_win_stop():
    g = Graph()
    g.call("clear", KSL + ":K2_ClearTimer", Object=ref(g.self_()), FunctionName="TimerRefresh")
    g.flow("entry", "clear")
    return g.data()


def g_win_is_open():
    g = Graph()
    g.branch("brManual", g.get("manual", "Manual"))
    g.call("inVp", UMG + "UserWidget:IsInViewport")
    g.set("setVp", "OpenTmp", value="inVp.ReturnValue")
    g.call("wm", GFL + ":GetWindowManager")
    valid(g, "wmOk", "wm.ReturnValue")
    g.call("isOpen", WINDOWMANAGER + ":IsWindowOpen", target=ref("wm.ReturnValue"), Window=ref(g.self_()))
    g.set("setWm", "OpenTmp", value="isOpen.ReturnValue")
    g.set("setNo", "OpenTmp", default="false")
    g.link(g.get("tmp", "OpenTmp"), "result.bOpen")
    g.flow("entry", "brManual", "setVp", "result")
    g.flow("brManual.else", "brWmOk", "setWm", "result")
    g.flow("brWmOk.else", "setNo", "result")
    return g.data()


def g_win_update_code():
    """Code tab: checks the pasted code, shows it in the preview column, enables TAKE BUILD.
    Both ends are trimmed: the multi-line box takes Enter as a new line."""
    g = Graph()
    data = g.get("data", "Data")
    valid(g, "hasData", data)
    g.call("trimStart", KSTR + ":Trim", SourceString=ref("entry.NewText"))
    g.call("trim", KSTR + ":TrimTrailing", SourceString=ref("trimStart.ReturnValue"))
    g.call("same", KSTR + ":EqualEqual_StrStr", A=ref("trim.ReturnValue"), B=ref(g.get("old", "CodeText")))
    g.branch("brSame", "same.ReturnValue")
    g.set("setCode", "CodeText", value="trim.ReturnValue")
    code = g.get("code", "CodeText")
    g.call("cls", cls(DATA) + ":ClassOfCode", target=ref(data), Code=ref(code))
    g.set("setValid", "CodeValid", value="cls.Valid")
    g.branch("brValid", "cls.Valid")
    preview = g.get("preview", "Preview")
    g.call("show", cls(COLUMN) + ":ShowCode", target=ref(preview), NewCode=ref(code), Title="PASTED BUILD")
    g.call("head", cls(DATA) + ":HeaderOfCode", target=ref(data), Code=ref(code))
    g.call("okMsg", KSTR + ":Concat_StrStr", A="VALID CODE - ", B=ref("head.Sub"))
    set_text(g, "setOk", "CodeStatus", ref("okMsg.ReturnValue"))
    text_colour(g, "okColour", "CodeStatus", GOOD)
    g.call("clear", cls(COLUMN) + ":Clear", target=ref(preview))
    g.call("empty", KSTR + ":IsEmpty", InString=ref(code))
    bad = kml(g, "badMsg", "SelectString", A=CODE_HINT, B="NOT A DWARF BUILDS CODE", bPickA=ref("empty.ReturnValue"))
    set_text(g, "setBad", "CodeStatus", ref(bad))
    text_colour(g, "badColour", "CodeStatus", pick(g, "badC", LABEL, BAD, "empty.ReturnValue"))
    # The whole game button dims while disabled.
    wcall(g, "enTake", "TakeCodeBtnWrap", "Widget:SetIsEnabled", bInIsEnabled=ref(g.get("ok", "CodeValid")))
    g.flow("entry", "brHasData", "brSame")
    g.flow("brSame.else", "setCode", "cls", "setValid", "brValid", "show", "head", "setOk", "okColour", "enTake")
    g.flow("brValid.else", "clear", "setBad", "badColour", "enTake")
    return g.data()


def g_win_paste_code():
    g = Graph()
    g.call("clip", FRONTEND + ":GetStringFromClipboard")
    g.call("trimStart", KSTR + ":Trim", SourceString=ref("clip.fromClipboard"))
    g.call("trim", KSTR + ":TrimTrailing", SourceString=ref("trimStart.ReturnValue"))
    g.call("txt", KTXT + ":Conv_StringToText", InString=ref("trim.ReturnValue"))
    wcall(g, "setBox", "CodeBox", "MultiLineEditableTextBox:SetText", InText=ref("txt.ReturnValue"))
    g.call("update", "UpdateCode", NewText=ref("trim.ReturnValue"))
    g.flow("entry", "clip", "setBox", "update")
    return g.data()


def g_win_copy_mine():
    g = Graph()
    data = g.get("data", "Data")
    valid(g, "hasData", data)
    g.call("mine", cls(DATA) + ":LocalCode", target=ref(data))
    g.call("empty", KSTR + ":IsEmpty", InString=ref("mine.Code"))
    g.branch("brEmpty", "empty.ReturnValue")
    set_text(g, "none", "CopyNote", "YOU HAVE NO BUILD YET.")
    g.call("copy", FRONTEND + ":CopyStringToClipboard", toClipboard=ref("mine.Code"))
    set_text(g, "done", "CopyNote", "YOUR BUILD CODE IS IN THE CLIPBOARD.")
    g.flow("entry", "brHasData", "mine", "brEmpty", "none")
    g.flow("brEmpty.else", "copy", "done")
    return g.data()


def g_win_open_site():
    """URL in the Steam overlay; OnOverlayClosed (EventGraph) runs when the overlay closes. No overlay (off in
    Steam): nothing opens, OPEN IN BROWSER is the way then."""
    g = Graph()
    g.node("closed", "createdelegate", fn="OnOverlayClosed")
    g.call("open", ONLINE + ":OpenURLInOverlay", URL=ref("entry.URL"), OnOverlayClosed=ref("closed.OutputDelegate"))
    g.flow("entry", "open")
    return g.data()


def g_win_publish():
    """PUBLISH MY BUILD: the site's editor with your current code (/new?code=DB1:...; the code needs no URL
    encoding)."""
    g = Graph()
    data = g.get("data", "Data")
    valid(g, "hasData", data)
    g.call("mine", cls(DATA) + ":LocalCode", target=ref(data))
    g.call("empty", KSTR + ":IsEmpty", InString=ref("mine.Code"))
    g.branch("brEmpty", "empty.ReturnValue")
    set_text(g, "none", "CopyNote", "YOU HAVE NO BUILD YET.")
    g.call("url", KSTR + ":Concat_StrStr", A=SITE_URL + "/new?code=", B=ref("mine.Code"))
    g.call("open", "OpenSite", URL=ref("url.ReturnValue"))
    g.flow("entry", "brHasData", "mine", "brEmpty", "none")
    g.flow("brEmpty.else", "open")
    return g.data()










def typing(g):
    """Pin: the code text box has the keyboard focus (the focus sits on its inner text widget)."""
    code_box = g.get("box", "CodeBox")
    g.call("f1", UMG + "Widget:HasKeyboardFocus", target=ref(code_box))
    g.call("f2", UMG + "Widget:HasFocusedDescendants", target=ref(code_box))
    return kml(g, "typing", "BooleanOR", A=ref("f1.ReturnValue"), B=ref("f2.ReturnValue"))


def reply(g, handled):
    """result.ReturnValue = Handled when the pin `handled` is true, else Unhandled."""
    g.call("yes", WBL + ":Handled")
    g.call("no", WBL + ":Unhandled")
    g.node("reply", "select", index="bool", type={"type": "struct", "class": EVENTREPLY})
    g.link(handled, "reply.Index")
    g.link("no.ReturnValue", "reply.Option 0")
    g.link("yes.ReturnValue", "reply.Option 1")
    g.link("reply.ReturnValue", "result.ReturnValue")


def g_win_on_key_up():
    """The hotkey (DB_Data.OpenKey, B by default) closes (not while typing in the code box), Escape closes the dialog first, then the window, E switches
    the tooltips' "more info" box (not while typing), as in the game's own upgrade tooltip.
    Key up, not down: the release of a key that closed the window must not reach the game (escape menu).
    While typing, every key stays here (in a GameAndUI input mode it would reach the game)."""
    g = Graph()
    g.call("key", INPUTLIB + ":GetKey", Input=ref("entry.InKeyEvent"))
    g.call("hotkey", cls(DATA) + ":OpenKey", target=ref(g.get("dKey", "Data")))
    g.call("keyB", INPUTLIB + ":EqualEqual_KeyKey", A=ref("key.ReturnValue"), B=ref("hotkey.Key"))
    g.call("keyEsc", INPUTLIB + ":EqualEqual_KeyKey", A=ref("key.ReturnValue"), B="Escape")
    g.call("keyE", INPUTLIB + ":EqualEqual_KeyKey", A=ref("key.ReturnValue"), B="E")
    close_keys = kml(g, "closeKeys", "BooleanOR", A=ref("keyB.ReturnValue"), B=ref("keyEsc.ReturnValue"))
    ours = kml(g, "ours", "BooleanOR", A=ref(close_keys), B=ref("keyE.ReturnValue"))
    in_box = typing(g)
    reply(g, kml(g, "handled", "BooleanOR", A=ref(ours), B=ref(in_box)))
    g.branch("brB", "keyB.ReturnValue")
    g.branch("brTyping", in_box)
    g.call("closeB", "Dismiss")
    g.branch("brEsc", "keyEsc.ReturnValue")
    g.branch("brDialog", g.get("dialog", "TakeOpen"))
    g.call("closeDialog", "CloseTake")
    g.call("closeEsc", "Dismiss")
    g.branch("brE", "keyE.ReturnValue")
    g.branch("brTypingE", in_box)
    data = g.get("data", "Data")
    valid(g, "hasData", data)
    g.call("more", cls(DATA) + ":ToggleMoreInfo", target=ref(data))
    g.flow("entry", "hotkey", "brB", "brTyping", "result")
    g.flow("brTyping.else", "closeB", "result")
    g.flow("brB.else", "brEsc", "brDialog", "closeDialog", "result")
    g.flow("brDialog.else", "closeEsc", "result")
    g.flow("brEsc.else", "brE", "brTypingE", "result")
    g.flow("brTypingE.else", "brHasData", "more", "result")
    g.flow("brHasData.else", "result")
    g.flow("brE.else", "result")
    return g.data()


def g_win_on_key_down():
    """While typing in the code box, keys the box does not use (letters, digits) do not reach the game. E is ours
    (OnKeyUp): its press does not reach the game either (E is the game's Use key)."""
    g = Graph()
    g.call("key", INPUTLIB + ":GetKey", Input=ref("entry.InKeyEvent"))
    g.call("keyE", INPUTLIB + ":EqualEqual_KeyKey", A=ref("key.ReturnValue"), B="E")
    reply(g, kml(g, "handled", "BooleanOR", A=ref(typing(g)), B=ref("keyE.ReturnValue")))
    g.flow("entry", "result")
    return g.data()


def g_win_on_mouse_down():
    """A click on the background keeps the keyboard focus here (B and Escape keep working)."""
    g = Graph()
    g.call("focus", UMG + "Widget:SetKeyboardFocus")
    g.call("yes", WBL + ":Handled")
    g.link("yes.ReturnValue", "result.ReturnValue")
    g.flow("entry", "focus", "result")
    return g.data()


def g_win_can_close():
    """The game's close command: not while the take dialog is open (Escape then closes only the dialog)."""
    g = Graph()
    g.link(kml(g, "no", "Not_PreBool", A=ref(g.get("dialog", "TakeOpen"))), "result.ReturnValue")
    g.flow("entry", "result")
    return g.data()


def g_win_events():
    g = Graph()
    g.node("destruct", "event", name="Destruct", **{"class": USERWIDGET})
    g.call("tips1", "HideAllTips")
    g.call("stop1", "Stop")
    # Opened by hand and removed another way than Dismiss (level travel, RemoveFromParent): give input back.
    g.branch("brManual", g.get("manual", "Manual"))
    g.call("owner", UMG + "Widget:GetOwningPlayer")
    valid(g, "ownerOk", "owner.ReturnValue")
    g.call("game", WBL + ":SetInputMode_GameOnly", PlayerController=ref("owner.ReturnValue"))
    g.set("cursor", "bShowMouseCursor", PLAYERCONTROLLER, "owner.ReturnValue", default="false")
    g.flow("destruct", "tips1", "stop1", "brManual", "brOwnerOk", "game", "cursor")
    g.node("closed", "event", name="OnClosed", **{"class": WINDOWWIDGET})
    g.call("tips2", "HideAllTips")
    g.call("stop2", "Stop")
    wcall(g, "hideTake", "Take", "Widget:SetVisibility", InVisibility="Collapsed")
    g.set("noTake", "TakeOpen", default="false")
    g.flow("closed", "tips2", "stop2", "hideTake", "noTake")
    # Focus leaves the window (Alt+Tab, another menu): hide the tooltips, or one shown now could stay on screen.
    for k, event in enumerate(("OnFocusLost", "OnRemovedFromFocusPath")):
        g.node("focus%d" % k, "event", name=event, **{"class": USERWIDGET})
        g.call("focusTips%d" % k, "HideAllTips")
        g.flow("focus%d" % k, "focusTips%d" % k)
    g.node("evClose", "boundevent", widget="CloseBtn", name="OnClicked")
    g.call("doClose", "Dismiss")
    g.flow("evClose", "doClose")
    # Tabs and filters: both variants of each (see toggle_button).
    for k, name in enumerate(("TabTeam", "TabCode")):
        for suffix in ("Off", "On"):
            g.node("ev" + name + suffix, "boundevent", widget=name + suffix, name="OnClicked")
            g.call("do" + name + suffix, "SetTab", NewTab=str(k))
            g.flow("ev" + name + suffix, "do" + name + suffix)
    for i in range(5):
        for suffix in ("Off", "On"):
            g.node("evFilter%d%s" % (i, suffix), "boundevent", widget="Filter%d%s" % (i, suffix), name="OnClicked")
            g.call("doFilter%d%s" % (i, suffix), "SetFilter", NewFilter=str(i))
            g.flow("evFilter%d%s" % (i, suffix), "doFilter%d%s" % (i, suffix))
    for name, step in (("PrevBtn", -PAGE_SIZE), ("NextBtn", PAGE_SIZE)):
        g.node("ev" + name, "boundevent", widget=name, name="OnClicked")
        g.call("do" + name, "PageBy", Step=str(step))
        g.flow("ev" + name, "do" + name)
    for name, fn in (("PasteBtn", "PasteCode"), ("CopyMineBtn", "CopyMine")):
        g.node("ev" + name, "boundevent", widget=name, name="OnClicked")
        g.call("do" + name, fn)
        g.flow("ev" + name, "do" + name)
    g.node("evTake", "boundevent", widget="TakeCodeBtn", name="OnClicked")
    g.branch("brTake", g.get("valid", "CodeValid"))
    g.call("doTake", "OpenTake", NewCode=ref(g.get("code", "CodeText")), Title="PASTED BUILD")
    g.flow("evTake", "brTake", "doTake")
    g.node("evText", "boundevent", widget="CodeBox", name="OnTextChanged")
    g.call("text", KTXT + ":Conv_TextToString", InText=ref("evText.Text"))
    g.call("doText", "UpdateCode", NewText=ref("text.ReturnValue"))
    g.flow("evText", "doText")
    # The website.
    g.node("evBrowse", "boundevent", widget="BrowseBtn", name="OnClicked")
    g.call("doBrowse", "OpenSite", URL=SITE_URL)
    g.flow("evBrowse", "doBrowse")
    g.node("evPublish", "boundevent", widget="PublishBtn", name="OnClicked")
    g.call("doPublish", "PublishMine")
    g.flow("evPublish", "doPublish")
    g.node("evBrowser", "boundevent", widget="BrowserBtn", name="OnClicked")
    g.call("doBrowser", FRONTEND + ":OpenURLInExternalBrowser", URL=SITE_URL)
    g.flow("evBrowser", "doBrowser")
    # The overlay closed: the keys come back to the window.
    g.node("overlayClosed", "customevent", name="OnOverlayClosed", signature=ONLINE + ":OpenURLInOverlay:OnOverlayClosed")
    g.call("closedFocus", UMG + "Widget:SetKeyboardFocus")
    g.flow("overlayClosed", "closedFocus")
    # Secondary (dark) buttons turn orange while held down, like the game's.
    for name in (["TabTeamOff", "TabCodeOff"] + ["Filter%dOff" % i for i in range(5)] +
                 ["PrevBtn", "NextBtn", "PasteBtn", "CopyMineBtn", "BrowseBtn", "PublishBtn", "BrowserBtn"]):
        press_feedback(g, name)
    return g.data()


# ============================================================================= DB_Select

# The overlay on the game's class selection screen (mission join, Space Rig class choice): the teammates' columns
# on the left, your own on the right in place of the game's class description box (hidden while the overlay is up,
# DESC_NAME), compact (no button row) and scaled down into the screen's free areas (select.md section 2). Numbers
# are Slate units at 1920x1080; the free areas follow the screen size (FitScale).
REF_W, REF_H = 1920, 1080
TEAM_POS = (24, 292)          # top-left of the team columns
TEAM_FREE = (666, 640)        # free area there at 1080p: it ends 270 before the screen centre (the dwarf) and 148
                              # above the bottom (the mission name and the SEASON CHALLENGES button)
OWN_POS = (-296, 166)         # top centre of your own column: over the middle of the loadout letters, under the
                              # player card and the resources row
OWN_FREE_H = 608              # it ends 306 above the bottom, over the loadout letters
SEL_COLS = 3                  # teammates shown; more are counted in the "+N MORE" label
SEL_GAP = 8
COMPACT_H = 940               # DB_Column in compact mode: 418 x 940
SEL_MIN, SEL_MAX = 0.45, 0.8
SEL_HEAD_GAP = 6              # the DWARF BUILDS label ends this far above the team columns
SEL_NAMES = ["Team%d" % k for k in range(SEL_COLS)] + ["Own"]
# The game's class description box: DescriptionWindow (a Basic_Menu_SmallWindowWithHeader) of
# SCREEN_CharacterSelection_Clean, above the loadout letters. The screen shows the window again (SetVisibility and
# a move-in) on every class change, so the window itself is left alone: its frame Brackets (window root > WindowButton
# > Brackets > blur > everything drawn), which nothing in the game touches, is made Hidden. Hidden keeps its size, so
# the loadout letters stay where they are. Brackets is reached from the window's bottom colour bar (DESC_BAR, a
# UserWidget, so GetAllWidgetsOfClass finds it): bar > VerticalBox_0 > BackgroundBlur_2 > Brackets (DESC_UP parents).
# Build Inspector removes the same part (it climbs from the screen's ClassDescription text).
DESC_BAR_CLASS = "/Game/UI/Art/WidgetParts/Basic_Menu_ColorBar.Basic_Menu_ColorBar_C"
DESC_BAR = "Basic_Menu_ColorBar_1"
DESC_NAME = "DescriptionWindow"
DESC_UP = 3
SCREEN_CLASS = "/Game/UI/CharacterSelectionMK2/SCREEN_CharacterSelection_Base.SCREEN_CharacterSelection_Base_C"
# A widget that sits directly in the screen's full-screen canvas (CanvasPanel_1, under its safe zone). The overlay
# is added to that canvas at SEL_ZORDER, as the original Build Inspector does: it then shows and hides with the
# screen, whatever the game's window manager does.
ANCHOR_CLASS = "/Game/UI/CharacterSelectionMK2/Lobby_BarTop_Countdown.Lobby_BarTop_Countdown_C"
SEL_ZORDER = 9999             # the screen's own children there are at 0
ZORDER_RIG, ZORDER_MISSION = 13, 100   # fallback without the canvas: viewport layers just above the screen
POLL_SECONDS = "0.5"          # InitSpacerig/InitCave poll for the screen (SelectPoll)
POLL_WINDOW = 60.0            # the poll runs at POLL_SECONDS this long after BeginPlay and after each selection start
SLOW_POLL = "2.0"             # the Space Rig's poll after that, while the screen is not found
CANVAS = UMG + "CanvasPanel"
CANVASSLOT = UMG + "CanvasPanelSlot"
ANCHORS = "/Script/Slate.Anchors"
MORE_BG = (0.0, 0.0, 0.0, 0.6)


def canvas(pos, anchor, align=None):
    """CanvasPanelSlot at a point anchor (0..1 per axis), sized to its content; align defaults to the anchor."""
    ax, ay = anchor
    lx, ly = align or anchor
    return {"LayoutData": "(Offsets=(Left=%g,Top=%g,Right=0,Bottom=0),Anchors=(Minimum=(X=%g,Y=%g),"
                          "Maximum=(X=%g,Y=%g)),Alignment=(X=%g,Y=%g))" % (pos[0], pos[1], ax, ay, ax, ay, lx, ly),
            "bAutoSize": "True"}


def select_tree():
    """Root and boxes are SelfHitTestInvisible: clicks outside our columns reach the screen. The columns are
    Visible (hover tooltips; a click on them must not fall through to the screen)."""
    def column(name, slot=None):
        return w(cls(COLUMN), name, var=True, props={"Visibility": "Visible"}, slot=slot)

    def fit(name, child, slot):
        # A fixed (user-specified) scale, set by FitScale: ScaleToFit would lay the columns out twice a frame.
        return w("ScaleBox", name, var=True, slot=slot, children=[child], props={
            "Stretch": "UserSpecified", "UserSpecifiedScale": "0.5", "Visibility": "SelfHitTestInvisible"})

    team = w("HorizontalBox", "TeamRow", props={"Visibility": "SelfHitTestInvisible"}, children=[
        column("Team%d" % k, hslot(pad=(SEL_GAP if k else 0, 0, 0, 0), valign="VAlign_Top")) for k in range(SEL_COLS)])
    # The label of the team side, at scale 1 so it reads as the mod's panel (like the game's white Rift labels).
    title = text("HeadText", "DWARF BUILDS", RIFT, 22, WHITE, slot=hslot())
    title["props"].update(ShadowOffset="(X=2,Y=2)", ShadowColorAndOpacity=colour((0.0, 0.0, 0.0, 0.6)))
    more = w("VerticalBox", "MoreBox", var=True, props={"Visibility": "Collapsed"}, slot=hslot(pad=(12, 0, 0, 0)),
             children=[image("MoreRule", ORANGE, size=(32, 2), slot=vslot()),
                       border("MoreFill", MORE_BG, text("MoreText", "+1 MORE", CARBON, 14, LIGHT, var=True),
                              pad=(8, 3, 8, 2), slot=vslot())])
    head = w("HorizontalBox", "TeamHead", var=True, props={"Visibility": "Collapsed"},
             slot=canvas((TEAM_POS[0], TEAM_POS[1] - SEL_HEAD_GAP), (0, 0), (0, 1)), children=[title, more])
    return w("CanvasPanel", "Root", props={"Visibility": "SelfHitTestInvisible"}, children=[
        fit("TeamFit", team, canvas(TEAM_POS, (0, 0))),
        fit("OwnFit", column("Own"), canvas(OWN_POS, (1, 0), (0.5, 0))),
        head,
    ])


def g_sel_attach():
    """Called by InitSpacerig/InitCave when they find the selection screen (open or not). With NewCanvas (the
    screen's full-screen canvas) the overlay becomes its child at SEL_ZORDER, so it is drawn exactly while the screen
    is; without it (fallback) it goes to the viewport at Layer and Update shows and hides it. Then it fills itself."""
    g = Graph()
    me = g.self_()
    g.set("setScreen", "Screen", value="entry.NewScreen")
    g.set("setCanvas", "Canvas", value="entry.NewCanvas")
    g.set("setData", "Data", value="entry.NewData")
    chain = ["entry", "setScreen", "setCanvas", "setData"]
    for name in SEL_NAMES:
        g.set("data" + name, "Data", cls(COLUMN), g.get("w" + name, name), g.get("d" + name, "Data"))
        chain.append("data" + name)
    g.branch("brInit", g.get("inited", "Inited"))
    g.flow(*(chain + ["brInit"]))
    # Once: the team column list and compact mode (no button row; Window stays None).
    g.node("cols", "makearray", n=SEL_COLS)
    for k in range(SEL_COLS):
        g.link(g.get("col%d" % k, "Team%d" % k), "cols.[%d]" % k)
    g.set("setCols", "TeamCols", value="cols.Array")
    once = ["brInit.else", "setCols"]
    for name in SEL_NAMES:
        g.call("compact" + name, cls(COLUMN) + ":SetCompact", target=ref(g.get("c" + name, name)), On="true")
        once.append("compact" + name)
    g.set("setInit", "Inited", default="true")
    g.flow(*(once + ["setInit", "brCan"]))
    g.flow("brInit", "brCan")
    # Into the screen's canvas, stretched over it (AddChildToCanvas takes the widget from any old parent or the
    # viewport first).
    valid(g, "can", "entry.NewCanvas")
    g.call("parent", UMG + "Widget:GetParent")
    g.branch("brIn", kml(g, "inCan", "EqualEqual_ObjectObject", A=ref("parent.ReturnValue"), B=ref("entry.NewCanvas")))
    g.call("addC", CANVAS + ":AddChildToCanvas", target=ref("entry.NewCanvas"), Content=ref(me))
    g.call("zC", CANVASSLOT + ":SetZOrder", target=ref("addC.ReturnValue"), InZOrder=str(SEL_ZORDER))
    g.node("anchors", "makestruct", struct=ANCHORS)
    g.defaults["anchors.Minimum"] = "(X=0,Y=0)"
    g.defaults["anchors.Maximum"] = "(X=1,Y=1)"
    g.call("anC", CANVASSLOT + ":SetAnchors", target=ref("addC.ReturnValue"), InAnchors=ref("anchors.Anchors"))
    g.node("offsets", "makestruct", struct=MARGIN)
    g.call("offC", CANVASSLOT + ":SetOffsets", target=ref("addC.ReturnValue"), InOffset=ref("offsets.Margin"))
    g.flow("brCan", "brIn", "vis")
    g.flow("brIn.else", "addC", "zC", "anC", "offC", "vis")
    # Fallback: the viewport, just above the screen (13 on the Space Rig, 100 in missions).
    g.call("inVp", UMG + "UserWidget:IsInViewport")
    g.branch("brVp", "inVp.ReturnValue")
    g.call("unparent", UMG + "Widget:RemoveFromParent")
    g.call("add", UMG + "UserWidget:AddToViewport", ZOrder=ref("entry.Layer"))
    g.flow("brCan.else", "brVp", "vis")
    g.flow("brVp.else", "unparent", "add", "vis")
    g.call("vis", UMG + "Widget:SetVisibility", InVisibility="SelfHitTestInvisible")
    g.set("notUp", "WasUp", default="false")   # the next Update fits and fills again when the screen is up
    g.call("refresh", "Refresh")
    g.flow("vis", "notUp", "refresh")
    return g.data()


def g_sel_is_attached():
    """Up: the screen is still part of the UI (in the viewport or in a parent) and the overlay still sits in its
    canvas (or, in the fallback, in the viewport). A mission's screen leaves the viewport after the class choice."""
    g = Graph()
    valid(g, "has", g.get("scr0", "Screen"))
    g.call("scrVp", UMG + "UserWidget:IsInViewport", target=ref(g.get("scr1", "Screen")))
    g.call("scrPar", UMG + "Widget:GetParent", target=ref(g.get("scr2", "Screen")))
    g.call("scrParOk", KSL + ":IsValid", Object=ref("scrPar.ReturnValue"))
    live = kml(g, "live", "BooleanOR", A=ref("scrVp.ReturnValue"), B=ref("scrParOk.ReturnValue"))
    valid(g, "can", g.get("can0", "Canvas"))
    g.call("parent", UMG + "Widget:GetParent")
    in_can = kml(g, "inCan", "EqualEqual_ObjectObject", A=ref("parent.ReturnValue"), B=ref(g.get("can1", "Canvas")))
    g.call("inVp", UMG + "UserWidget:IsInViewport")
    g.set("upCan", "UpTmp", value=kml(g, "okCan", "BooleanAND", A=ref(live), B=ref(in_can)))
    g.set("upVp", "UpTmp", value=kml(g, "okVp", "BooleanAND", A=ref(live), B=ref("inVp.ReturnValue")))
    g.set("upNo", "UpTmp", default="false")
    g.link(g.get("tmp", "UpTmp"), "result.Up")
    g.flow("entry", "brHas", "brCan", "upCan", "result")
    g.flow("brCan.else", "upVp", "result")
    g.flow("brHas.else", "upNo", "result")
    return g.data()


def g_sel_update():
    """The poll (0.5 s) while attached. Up: the screen is shown. Became: it was just shown (then the overlay fits and
    fills at once); while it stays shown, every second call refreshes (1 s). In the fallback the overlay's own
    visibility follows the screen. When the screen goes, the tooltips are hidden once."""
    g = Graph()
    g.set("noBec", "BecTmp", default="false")
    g.set("noUp", "UpTmp", default="false")
    valid(g, "has", g.get("scr0", "Screen"))
    g.call("shown", UMG + "Widget:IsVisible", target=ref(g.get("scr1", "Screen")))
    g.set("setUp", "UpTmp", value="shown.ReturnValue")
    valid(g, "can", g.get("can0", "Canvas"))
    g.call("selfVis", UMG + "Widget:SetVisibility",
           InVisibility=ref(vis(g, "visSel", g.get("up0", "UpTmp"), "SelfHitTestInvisible")))
    g.branch("brUp", g.get("up1", "UpTmp"))
    g.flow("entry", "noBec", "noUp", "brHas", "setUp", "brCan", "brUp")
    g.flow("brCan.else", "selfVis", "brUp")
    # Just shown: fit and fill.
    g.branch("brWas", g.get("was0", "WasUp"))
    g.set("setBec", "BecTmp", default="true")
    g.set("wasOn", "WasUp", default="true")
    g.call("refresh", "Refresh")
    g.flow("brUp", "brWas")
    g.call("findDesc", "FindDesc")
    g.call("hideDesc", "HideDesc")
    g.flow("brWas.else", "setBec", "wasOn", "refresh", "findDesc", "hideDesc", "result")
    # Still shown: refresh every second call; the description box is hidden again (the screen may show it).
    g.set("flip", "Odd", value=kml(g, "notOdd", "Not_PreBool", A=ref(g.get("odd0", "Odd"))))
    g.branch("brOdd", g.get("odd1", "Odd"))
    g.call("refresh2", "Refresh")
    g.call("hideDesc2", "HideDesc")
    g.flow("brWas", "flip", "brOdd", "refresh2", "hideDesc2", "result")
    g.flow("brOdd.else", "result")
    # Hidden: hide the tooltips once (one shown now could stay on screen).
    g.branch("brWasH", g.get("was1", "WasUp"))
    valid(g, "data", g.get("data0", "Data"))
    g.call("tips", cls(DATA) + ":HideTips", target=ref(g.get("data1", "Data")))
    g.set("wasOff", "WasUp", default="false")
    g.flow("brUp.else", "brWasH", "brData", "tips", "wasOff", "result")
    g.flow("brData.else", "wasOff")
    g.flow("brWasH.else", "result")
    g.flow("brHas.else", "result")
    g.link(g.get("upOut", "UpTmp"), "result.Up")
    g.link(g.get("becOut", "BecTmp"), "result.Became")
    return g.data()


def g_sel_detach():
    """The screen went away (or the mod actor ends): leave its canvas or the viewport and drop the references, so the
    old screen can be freed. RemoveFromParent does nothing when the overlay is nowhere."""
    g = Graph()
    valid(g, "has", g.get("scr0", "Screen"))
    valid(g, "data", g.get("data0", "Data"))
    g.call("tips", cls(DATA) + ":HideTips", target=ref(g.get("data1", "Data")))
    g.call("remove", UMG + "Widget:RemoveFromParent")
    g.set("noScreen", "Screen")
    g.set("noCanvas", "Canvas")
    g.set("noDesc", "Desc")
    g.set("wasOff", "WasUp", default="false")
    g.flow("entry", "brHas", "brData", "tips", "remove", "noScreen", "noCanvas", "noDesc", "wasOff")
    g.flow("brData.else", "remove")
    g.flow("brHas.else", "remove")
    return g.data()


def g_sel_on_stop():
    """The game's selection stop: only the tooltips go. The overlay stays in the screen's canvas and shows and hides
    with it (a Stop right after a Start must not remove it, as it did before)."""
    g = Graph()
    valid(g, "data", g.get("data0", "Data"))
    g.call("tips", cls(DATA) + ":HideTips", target=ref(g.get("data1", "Data")))
    g.flow("entry", "brData", "tips")
    return g.data()


def g_sel_find_desc():
    """Desc: the frame (Brackets) of the screen's class description box, or None. The bar DESC_BAR whose window
    (outer of its widget tree) is DESC_NAME and whose window's owner is Screen; Desc is its DESC_UP-th parent. Run
    when the screen comes up; one scan of the world's DESC_BAR_CLASS widgets."""
    g = Graph()
    g.set("noDesc", "Desc")
    first, tails = load_class(g, "ldD", DESC_BAR_CLASS, "DescClass")
    g.flow("entry", "noDesc", first)
    for tail in tails:
        g.flow(tail, "brHas")
    g.call("has", KSL + ":IsValidClass", Class=ref(g.get("dc0", "DescClass")))
    g.branch("brHas", "has.ReturnValue")
    g.call("find", WBL + ":GetAllWidgetsOfClass", WidgetClass=ref(g.get("dc1", "DescClass")), TopLevelOnly="false")
    el = g.loop("each", "find.FoundWidgets")
    g.flow("brHas", "find", "each.Exec")
    # bar > its widget tree > the window > the window's tree > the screen.
    g.call("tree", KSL + ":GetOuterObject", Object=ref(el))
    g.call("win", KSL + ":GetOuterObject", Object=ref("tree.ReturnValue"))
    g.call("winTree", KSL + ":GetOuterObject", Object=ref("win.ReturnValue"))
    g.call("owner", KSL + ":GetOuterObject", Object=ref("winTree.ReturnValue"))
    same = kml(g, "same", "EqualEqual_ObjectObject", A=ref("owner.ReturnValue"), B=ref(g.get("scr", "Screen")))
    g.call("winName", KSL + ":GetObjectName", Object=ref("win.ReturnValue"))
    g.call("isWin", KSTR + ":EqualEqual_StrStr", A=ref("winName.ReturnValue"), B=DESC_NAME)
    g.call("barName", KSL + ":GetObjectName", Object=ref(el))
    g.call("isBar", KSTR + ":EqualEqual_StrStr", A=ref("barName.ReturnValue"), B=DESC_BAR)
    names = kml(g, "names", "BooleanAND", A=ref("isWin.ReturnValue"), B=ref("isBar.ReturnValue"))
    g.branch("brIt", kml(g, "it", "BooleanAND", A=ref(same), B=ref(names)))
    up = el
    for k in range(DESC_UP):
        g.call("up%d" % k, UMG + "Widget:GetParent", target=ref(up))
        up = "up%d.ReturnValue" % k
    g.set("keep", "Desc", value=up)
    g.flow("each.LoopBody", "brIt", "keep")
    return g.data()


def g_sel_hide_desc():
    """The class description box goes: its frame Desc is Hidden (it keeps its space); your column is drawn there.
    The screen never sets this part's visibility, so it stays hidden through class changes."""
    g = Graph()
    valid(g, "has", g.get("d0", "Desc"))
    g.call("hide", UMG + "Widget:SetVisibility", target=ref(g.get("d1", "Desc")), InVisibility="Hidden")
    g.flow("entry", "brHas", "hide")
    return g.data()


def g_sel_refresh():
    """Teammates (every player but you, lobby order, the first SEL_COLS) on the left, you on the right. Columns
    skip players who did not change. The scale is fitted on every refresh (1 s): when the screen first comes up the
    viewport size may not be final yet, and a scale fitted once then stayed at the minimum."""
    g = Graph()
    valid(g, "hasData", g.get("data0", "Data"))
    g.call("players", cls(DATA) + ":GetPlayers", target=ref(g.get("data1", "Data")))
    g.call("owner", UMG + "Widget:GetOwningPlayer")
    you = g.get("you", "PlayerState", CONTROLLER, "owner.ReturnValue")
    g.call("clear", KARR + ":Array_Clear", TargetArray=ref(g.get("m0", "Mates")))
    el = g.loop("each", "players.Players")
    g.branch("brOther", kml(g, "other", "NotEqual_ObjectObject", A=ref(el), B=ref(you)))
    g.call("add", KARR + ":Array_Add", TargetArray=ref(g.get("m1", "Mates")), NewItem=ref(el))
    g.flow("entry", "brHasData", "players", "clear", "each.Exec")
    g.flow("each.LoopBody", "brOther", "add")
    # Scale for the number of team columns.
    g.call("n", KARR + ":Array_Length", TargetArray=ref(g.get("m2", "Mates")))
    n = "n.ReturnValue"
    cols = kml(g, "cols", "Min", A=ref(n), B=str(SEL_COLS))
    g.set("keepCount", "TeamCount", value=cols)
    g.call("fit", "FitScale", Count=ref(cols))
    g.flow("each.Completed", "keepCount", "fit", "eachK")
    # Team columns: a player each, the rest cleared and collapsed (with their gap).
    k = g.for_range("eachK", "0", str(SEL_COLS - 1))
    g.call("col", KARR + ":Array_Get", TargetArray=ref(g.get("tc", "TeamCols")), Index=ref(k))
    g.branch("brHas", kml(g, "has", "Less_IntInt", A=ref(k), B=ref(n)))
    g.call("mate", KARR + ":Array_Get", TargetArray=ref(g.get("m3", "Mates")), Index=ref(k))
    g.call("show", cls(COLUMN) + ":ShowPlayer", target=ref("col.Item"), Player=ref("mate.Item"))
    g.call("on", UMG + "Widget:SetVisibility", target=ref("col.Item"), InVisibility="Visible")
    g.call("wasOn", UMG + "Widget:IsVisible", target=ref("col.Item"))
    g.branch("brWasOn", "wasOn.ReturnValue")
    g.call("empty", cls(COLUMN) + ":Clear", target=ref("col.Item"))
    g.call("off", UMG + "Widget:SetVisibility", target=ref("col.Item"), InVisibility="Collapsed")
    g.flow("eachK.LoopBody", "brHas", "show", "on")
    g.flow("brHas.else", "brWasOn", "empty", "off")
    # Label: only with teammates; "+N MORE" with more than SEL_COLS of them.
    wcall(g, "headVis", "TeamHead", "Widget:SetVisibility",
          InVisibility=ref(vis(g, "headV", kml(g, "anyMate", "Greater_IntInt", A=ref(n), B="0"), "HitTestInvisible")))
    extra = kml(g, "extra", "Subtract_IntInt", A=ref(n), B=str(SEL_COLS))
    more = kml(g, "more", "Greater_IntInt", A=ref(extra), B="0")
    wcall(g, "moreVis", "MoreBox", "Widget:SetVisibility",
          InVisibility=ref(vis(g, "moreV", more, "HitTestInvisible")))
    g.branch("brMore", more)
    g.node("moreFmt", "formattext", format="+{N} MORE")
    g.link(extra, "moreFmt.N")
    wcall(g, "moreText", "MoreText", "TextBlock:SetText", InText=ref("moreFmt.Result"))
    # Your own column.
    g.cast("asYou", PS, you)
    g.call("showOwn", cls(COLUMN) + ":ShowPlayer", target=ref(g.get("own0", "Own")), Player=ref("asYou.$cast"))
    g.call("ownOn", UMG + "Widget:SetVisibility", target=ref(g.get("own1", "Own")), InVisibility="Visible")
    g.call("clearOwn", cls(COLUMN) + ":Clear", target=ref(g.get("own2", "Own")))
    g.call("ownOff", UMG + "Widget:SetVisibility", target=ref(g.get("own3", "Own")), InVisibility="Collapsed")
    g.flow("eachK.Completed", "headVis", "moreVis", "brMore", "moreText", "asYou", "showOwn", "ownOn")
    g.flow("brMore.else", "asYou")
    g.flow("asYou.CastFailed", "clearOwn", "ownOff")
    return g.data()


def g_sel_fit():
    """Scales from the overlay's own size W x H (ViewW/ViewH, set by Tick from its geometry: the screen's canvas
    in the screen's own units, 1920 x 1080 at 16:9). Not the viewport size: on the Space Rig GetViewportSize gave a
    far too small size, so the overlay stayed at its smallest scale.
    team = clamp(min((W/2 - 294) / (n*418 + (n-1)*8), (H - 440) / 940), 0.45, 0.8), n = Count (at least 1);
    own = clamp((H - 472) / 940, 0.45, 0.8). At 1080p: team 0.52 with 3 teammates, 0.68 with 1 or 2; own 0.65.
    Nothing changes before the first Tick (H under 400)."""
    g = Graph()
    width = g.get("vw", "ViewW")
    height = g.get("vh", "ViewH")
    half = kml(g, "half", "Multiply_FloatFloat", A=ref(width), B="0.5")
    free_w = kml(g, "freeW", "Subtract_FloatFloat", A=ref(half), B=str(REF_W // 2 - TEAM_FREE[0]))
    free_h = kml(g, "freeH", "Subtract_FloatFloat", A=ref(height), B=str(REF_H - TEAM_FREE[1]))
    count = kml(g, "count", "Max", A=ref("entry.Count"), B="1")
    span = kml(g, "span", "Multiply_IntInt", A=ref(count), B=str(COLUMN_WIDTH + SEL_GAP))
    row = kml(g, "row", "Conv_IntToFloat", InInt=ref(kml(g, "rowW", "Subtract_IntInt", A=ref(span), B=str(SEL_GAP))))
    fit_w = kml(g, "fitW", "Divide_FloatFloat", A=ref(free_w), B=ref(row))
    fit_h = kml(g, "fitH", "Divide_FloatFloat", A=ref(free_h), B=str(COMPACT_H))
    team = kml(g, "team", "FClamp", Value=ref(kml(g, "fitMin", "FMin", A=ref(fit_w), B=ref(fit_h))),
               Min=str(SEL_MIN), Max=str(SEL_MAX))
    g.branch("brReady", kml(g, "ready", "Greater_FloatFloat", A=ref(height), B="400"))
    wcall(g, "setTeam", "TeamFit", "ScaleBox:SetUserSpecifiedScale", InUserSpecifiedScale=ref(team))
    own_h = kml(g, "ownH", "Subtract_FloatFloat", A=ref(height), B=str(REF_H - OWN_FREE_H))
    own = kml(g, "own", "FClamp", Value=ref(kml(g, "fitOwn", "Divide_FloatFloat", A=ref(own_h), B=str(COMPACT_H))),
              Min=str(SEL_MIN), Max=str(SEL_MAX))
    wcall(g, "setOwn", "OwnFit", "ScaleBox:SetUserSpecifiedScale", InUserSpecifiedScale=ref(own))
    g.flow("entry", "brReady", "setTeam", "setOwn")
    return g.data()


def g_sel_events():
    """Tick (it runs only while the overlay is drawn, so only on the selection screen): your column follows a class
    or loadout change at once instead of at the next 1 s refresh. A cheap check each frame: your class
    (GetSelectedCharacterID, what the column shows) and the save's selected loadout of that class; when either
    changed, your column is shown again (ShowPlayer, which redraws only what changed). Build Inspector does the same
    check in its Tick."""
    g = Graph()
    g.node("tick", "event", name="Tick", **{"class": USERWIDGET})
    # The overlay's size (it fills the screen's canvas): a new size fits the scale again.
    g.call("size", UMG + "SlateBlueprintLibrary:GetLocalSize", Geometry=ref("tick.MyGeometry"))
    g.call("sizeXY", KML + ":BreakVector2D", InVec=ref("size.ReturnValue"))
    same_w = kml(g, "sameW", "NearlyEqual_FloatFloat", A=ref("sizeXY.X"), B=ref(g.get("vw", "ViewW")),
                 ErrorTolerance="0.5")
    same_h = kml(g, "sameH", "NearlyEqual_FloatFloat", A=ref("sizeXY.Y"), B=ref(g.get("vh", "ViewH")),
                 ErrorTolerance="0.5")
    g.branch("brSize", kml(g, "sameSize", "BooleanAND", A=ref(same_w), B=ref(same_h)))
    g.set("setW", "ViewW", value="sizeXY.X")
    g.set("setH", "ViewH", value="sizeXY.Y")
    g.call("fit", "FitScale", Count=ref(g.get("tc", "TeamCount")))
    g.flow("tick", "brSize", "asPs")
    g.flow("brSize.else", "setW", "setH", "fit", "asPs")
    # Your column.
    g.call("owner", UMG + "Widget:GetOwningPlayer")
    g.cast("asPs", PS, g.get("ps", "PlayerState", CONTROLLER, "owner.ReturnValue"))
    g.call("cls", PS + ":GetSelectedCharacterID", target=ref("asPs.$cast"))
    g.call("save", GFL + ":GetFSDSaveGame")
    valid(g, "hasSave", "save.ReturnValue")
    g.call("idx", SAVEGAME + ":GetSelectedLoadoutIndex", target=ref("save.ReturnValue"),
           characterID=ref("cls.ReturnValue"))
    same_cls = kml(g, "sameCls", "EqualEqual_ObjectObject", A=ref("cls.ReturnValue"), B=ref(g.get("oc", "OwnClass")))
    same_idx = kml(g, "sameIdx", "EqualEqual_IntInt", A=ref("idx.ReturnValue"), B=ref(g.get("ol", "OwnLoadout")))
    g.branch("brSame", kml(g, "same", "BooleanAND", A=ref(same_cls), B=ref(same_idx)))
    g.set("setCls", "OwnClass", value="cls.ReturnValue")
    g.set("setIdx", "OwnLoadout", value="idx.ReturnValue")
    g.call("show", cls(COLUMN) + ":ShowPlayer", target=ref(g.get("own", "Own")), Player=ref("asPs.$cast"))
    g.flow("asPs", "brHasSave", "brSame")
    g.flow("brSame.else", "setCls", "setIdx", "show")
    return g.data()


def g_sel_mouse_down():
    """A click on our columns gives the keyboard focus back to the selection screen: else Slate moves it to the
    game viewport and Escape, Q/E and the gamepad stop working there. The tunnel (preview) event: the cards' hover
    buttons take the normal mouse-down themselves, so it would not bubble up from them. Nothing in a compact
    column reacts to clicks."""
    g = Graph()
    g.call("has", KSL + ":IsValid", Object=ref(g.get("scr0", "Screen")))
    g.call("yes", WBL + ":Handled")
    g.call("focus", WBL + ":SetUserFocus", Reply=ref("yes.ReturnValue"), FocusWidget=ref(g.get("scr1", "Screen")))
    g.call("no", WBL + ":Unhandled")
    g.node("reply", "select", index="bool", type={"type": "struct", "class": EVENTREPLY})
    g.link("has.ReturnValue", "reply.Index")
    g.link("no.ReturnValue", "reply.Option 0")
    g.link("focus.ReturnValue", "reply.Option 1")
    g.link("reply.ReturnValue", "result.ReturnValue")
    g.flow("entry", "result")
    return g.data()


# ============================================================================= DB_Mod

def load_class(g, nid, path, var):
    """Loads a widget class by path into var (None when it fails). Returns the first exec node and the tails."""
    g.call(nid + "Path", KSL + ":MakeSoftClassPath", PathString=path)
    g.call(nid + "Soft", KSL + ":Conv_SoftClassPathToSoftClassRef", SoftClassPath=ref(nid + "Path.ReturnValue"))
    g.call(nid + "Load", KSL + ":LoadClassAsset_Blocking", AssetClass=ref(nid + "Soft.ReturnValue"))
    g.node(nid + "Cast", "classcast", **{"class": USERWIDGET})
    g.link(nid + "Load.ReturnValue", nid + "Cast.Class")
    g.set(nid + "Set", var, value=nid + "Cast.$cast")
    g.flow(nid + "Load", nid + "Cast", nid + "Set")
    return nid + "Load", [nid + "Set", nid + "Cast.CastFailed"]


def g_init_try_show():
    """Run by the poll (SelectPoll, 0.5 s), by the game's selection start and once when the actor is ready. While
    DB_Select sits in a live screen it only updates it (Update). Else it looks for the screen (FindScreen): found,
    DB_Select (created once per level, owned by the local player controller) attaches to it, open or not. Nothing
    depends on the moment an event comes. The classes are loaded by path once (they are in memory already)."""
    g = Graph()
    g.branch("brTried", g.get("tried", "ClassesTried"))
    g.set("setTried", "ClassesTried", default="true")
    s_first, s_tails = load_class(g, "ldS", SCREEN_CLASS, "ScreenClass")
    a_first, a_tails = load_class(g, "ldA", ANCHOR_CLASS, "AnchorClass")
    g.flow("entry", "brTried", "brHasSel")
    g.flow("brTried.else", "setTried", s_first)
    for tail in s_tails:
        g.flow(tail, a_first)
    for tail in a_tails:
        g.flow(tail, "brHasSel")
    # Attached to a live screen: only update.
    valid(g, "hasSel", g.get("sel0", "SelectUI"))
    g.call("att", cls(SELECT) + ":IsAttached", target=ref(g.get("sel1", "SelectUI")))
    g.branch("brAtt", "att.Up")
    g.call("detach", cls(SELECT) + ":Detach", target=ref(g.get("sel2", "SelectUI")))
    g.call("find", "FindScreen")
    g.flow("brHasSel", "att", "brAtt", "update")
    g.flow("brHasSel.else", "find")
    g.flow("brAtt.else", "detach", "find")
    # Found: create the overlay on first use and attach it.
    valid(g, "found", g.get("scr0", "ScreenTmp"))
    valid(g, "hasSel2", g.get("sel3", "SelectUI"))
    g.call("pc", GS + ":GetPlayerController", PlayerIndex="0")
    g.call("create", WBL + ":Create", WidgetType=cls(SELECT), OwningPlayer=ref("pc.ReturnValue"))
    g.cast("asSel", cls(SELECT), "create.ReturnValue")
    g.set("setSel", "SelectUI", value="asSel.$cast")
    g.flow("find", "brFound", "brHasSel2", "asPc")
    g.flow("brHasSel2.else", "create", "asSel", "setSel", "asPc")
    # Viewport layer for the fallback: just above the screen (13 on the Space Rig, 100 in missions).
    g.cast("asPc", PC, "pc.ReturnValue")
    rig = g.get("rig", "IsOnSpaceRig", PC, "asPc.$cast")
    g.set("zRig", "ZTmp", value=kml(g, "z", "SelectInt", A=str(ZORDER_RIG), B=str(ZORDER_MISSION), bPickA=ref(rig)))
    g.set("zMission", "ZTmp", default=str(ZORDER_MISSION))
    g.call("data", GS + ":GetActorOfClass", ActorClass=cls(DATA))
    g.call("attach", cls(SELECT) + ":AttachTo", target=ref(g.get("sel4", "SelectUI")),
           NewScreen=ref(g.get("scr1", "ScreenTmp")), NewCanvas=ref(g.get("can0", "CanvasTmp")),
           NewData=ref("data.ReturnValue"), Layer=ref(g.get("zt", "ZTmp")))
    g.flow("asPc", "zRig", "data", "attach", "update")
    g.flow("asPc.CastFailed", "zMission", "data")
    g.call("update", cls(SELECT) + ":Update", target=ref(g.get("sel5", "SelectUI")))
    return g.data()


def g_init_find_screen():
    """ScreenTmp, CanvasTmp: the class selection screen and its full-screen canvas, or None.
    0. No selection screen widget in this world at all: nothing to find, and only this one scan is made (the
       usual case while the poll waits for the screen).
    1. Every AnchorClass widget whose owner (outer of its widget tree) is a selection screen that is still part of
       the UI (in the viewport or in a parent); its parent is the canvas. A shown screen wins over a hidden one.
    2. No canvas found: a selection screen in the viewport (shown first), for the viewport fallback.
    Both scans walk the widgets of the world once; the poll runs them only while nothing is attached."""
    g = Graph()
    g.set("noScr", "ScreenTmp")
    g.set("noCan", "CanvasTmp")
    g.call("hasA", KSL + ":IsValidClass", Class=ref(g.get("aCls0", "AnchorClass")))
    g.branch("brA", "hasA.ReturnValue")
    g.call("findA", WBL + ":GetAllWidgetsOfClass", WidgetClass=ref(g.get("aCls1", "AnchorClass")), TopLevelOnly="false")
    el = g.loop("eachA", "findA.FoundWidgets")
    g.call("hasProbe", KSL + ":IsValidClass", Class=ref(g.get("sClsP", "ScreenClass")))
    g.branch("brProbe", "hasProbe.ReturnValue")
    g.call("probe", WBL + ":GetAllWidgetsOfClass", WidgetClass=ref(g.get("sClsQ", "ScreenClass")), TopLevelOnly="false")
    g.call("probeN", KARR + ":Array_Length", TargetArray=ref("probe.FoundWidgets"))
    g.branch("brAny", kml(g, "anyScreen", "Greater_IntInt", A=ref("probeN.ReturnValue"), B="0"))
    g.flow("entry", "noScr", "noCan", "brProbe", "probe", "brAny", "brA")
    g.flow("brProbe.else", "brA")
    g.flow("brA", "findA", "eachA.Exec")
    g.call("tree", KSL + ":GetOuterObject", Object=ref(el))
    g.call("owner", KSL + ":GetOuterObject", Object=ref("tree.ReturnValue"))
    g.call("ownerCls", GS + ":GetObjectClass", Object=ref("owner.ReturnValue"))
    g.branch("brOwner", kml(g, "isScreen", "ClassIsChildOf", TestClass=ref("ownerCls.ReturnValue"),
                            ParentClass=ref(g.get("sCls0", "ScreenClass"))))
    g.cast("asScr", USERWIDGET, "owner.ReturnValue")
    scr = "asScr.$cast"
    g.call("scrVp", UMG + "UserWidget:IsInViewport", target=ref(scr))
    g.call("scrPar", UMG + "Widget:GetParent", target=ref(scr))
    g.call("scrParOk", KSL + ":IsValid", Object=ref("scrPar.ReturnValue"))
    live = kml(g, "live", "BooleanOR", A=ref("scrVp.ReturnValue"), B=ref("scrParOk.ReturnValue"))
    g.call("hadOne", KSL + ":IsValid", Object=ref(g.get("scrT0", "ScreenTmp")))
    g.call("scrShown", UMG + "Widget:IsVisible", target=ref(scr))
    better = kml(g, "better", "BooleanOR", A=ref(kml(g, "noneYet", "Not_PreBool", A=ref("hadOne.ReturnValue"))),
                 B=ref("scrShown.ReturnValue"))
    g.branch("brTake", kml(g, "take", "BooleanAND", A=ref(live), B=ref(better)))
    g.call("elPar", UMG + "Widget:GetParent", target=ref(el))
    g.cast("asCan", CANVAS, "elPar.ReturnValue")
    g.set("keepScr", "ScreenTmp", value=scr)
    g.set("keepCan", "CanvasTmp", value="asCan.$cast")
    g.flow("eachA.LoopBody", "brOwner", "asScr", "brTake", "asCan", "keepScr", "keepCan")
    # Fallback: the screen alone.
    valid(g, "found", g.get("scrT1", "ScreenTmp"))
    g.flow("eachA.Completed", "brFound")
    g.flow("brA.else", "brFound")
    g.call("hasS", KSL + ":IsValidClass", Class=ref(g.get("sCls1", "ScreenClass")))
    g.branch("brS", "hasS.ReturnValue")
    g.call("findS", WBL + ":GetAllWidgetsOfClass", WidgetClass=ref(g.get("sCls2", "ScreenClass")), TopLevelOnly="true")
    s = g.loop("eachS", "findS.FoundWidgets")
    g.call("hadS", KSL + ":IsValid", Object=ref(g.get("scrT2", "ScreenTmp")))
    g.call("sShown", UMG + "Widget:IsVisible", target=ref(s))
    g.branch("brPick", kml(g, "pick", "BooleanOR", A=ref(kml(g, "noneS", "Not_PreBool", A=ref("hadS.ReturnValue"))),
                           B=ref("sShown.ReturnValue")))
    g.set("keepS", "ScreenTmp", value=s)
    g.flow("brFound.else", "brS", "findS", "eachS.Exec")
    g.flow("eachS.LoopBody", "brPick", "keepS")
    return g.data()


def g_init_poll(rig):
    """The poll, every POLL_SECONDS until POLL_WINDOW seconds after BeginPlay or the last selection start, and on
    while the overlay sits in a live screen (a call then costs a few checks). After that, while no screen is found
    (each call then looks through the widgets twice: FindScreen): a mission stops the poll (its screen only comes
    with a selection start, which starts the poll again); the Space Rig, where the screen can open at any time,
    slows it to SLOW_POLL (PollSlow), and goes back to POLL_SECONDS once the overlay is attached. So the overlay
    still does not depend on the game's selection events: without them it shows at most SLOW_POLL late."""
    g = Graph()
    me = g.self_()
    g.call("try", "TryShow")
    valid(g, "hasSel", g.get("sel0", "SelectUI"))
    g.call("att", cls(SELECT) + ":IsAttached", target=ref(g.get("sel1", "SelectUI")))
    g.branch("brAtt", "att.Up")
    g.call("now", GS + ":GetRealTimeSeconds")
    g.branch("brTime", kml(g, "early", "Less_FloatFloat", A=ref("now.ReturnValue"), B=ref(g.get("until", "PollUntil"))))
    g.flow("entry", "try", "brHasSel", "att", "brAtt")
    g.flow("brAtt.else", "brTime")
    g.flow("brHasSel.else", "brTime")
    if not rig:
        g.call("stop", KSL + ":K2_ClearTimer", Object=ref(me), FunctionName="SelectPoll")
        g.flow("brTime.else", "stop")
        return g.data()
    # Attached: back to the fast poll (Update follows the screen at that rate).
    g.branch("brFast", g.get("slow0", "PollSlow"))
    g.call("faster", KSL + ":K2_SetTimer", Object=ref(me), FunctionName="SelectPoll", Time=POLL_SECONDS,
           bLooping="true")
    g.set("fastOn", "PollSlow", default="false")
    g.flow("brAtt", "brFast", "faster", "fastOn")
    # Not found and the window is over: the slow poll.
    g.branch("brSlow", g.get("slow1", "PollSlow"))
    g.call("slower", KSL + ":K2_SetTimer", Object=ref(me), FunctionName="SelectPoll", Time=SLOW_POLL,
           bLooping="true")
    g.set("slowOn", "PollSlow", default="true")
    g.flow("brTime.else", "brSlow")
    g.flow("brSlow.else", "slower", "slowOn")
    return g.data()


def g_init_hide_select():
    g = Graph()
    valid(g, "has", g.get("sel0", "SelectUI"))
    g.call("detach", cls(SELECT) + ":Detach", target=ref(g.get("sel1", "SelectUI")))
    g.flow("entry", "brHas", "detach")
    return g.data()


def start_poll(g, nid, rig):
    """(Re)starts SelectPoll at POLL_SECONDS, for POLL_WINDOW seconds from now (g_init_poll says what follows).
    Returns first, last node."""
    g.call(nid + "Now", GS + ":GetRealTimeSeconds")
    g.set(nid + "Until", "PollUntil",
          value=kml(g, nid + "Add", "Add_FloatFloat", A=ref(nid + "Now.ReturnValue"), B=str(POLL_WINDOW)))
    steps = [nid + "Until"]
    if rig:
        g.set(nid + "Fast", "PollSlow", default="false")
        steps.append(nid + "Fast")
    me = g.self_()
    g.call(nid + "Clear", KSL + ":K2_ClearTimer", Object=ref(me), FunctionName="SelectPoll")
    g.call(nid + "Set", KSL + ":K2_SetTimer", Object=ref(me), FunctionName="SelectPoll", Time=POLL_SECONDS,
           bLooping="true")
    steps += [nid + "Clear", nid + "Set"]
    g.flow(*steps)
    return steps[0], steps[-1]


def select_events(g, after, rig):
    """Class selection overlay: after `after` (the local player controller is valid) bind the game instance's
    selection start/stop, start the poll and try once. The poll finds the screen even when the events do not come
    or come too early. EndPlay unbinds (the game instance outlives the level), stops the poll and detaches."""
    g.node("selStart", "customevent", name="DB_SelectionStart", signature=GAMEINSTANCE + ":OnCharacterSelectionStart")
    g.node("selStop", "customevent", name="DB_SelectionStop", signature=GAMEINSTANCE + ":OnCharacterSelectionStop")
    events = (("Start", "selStart", "OnCharacterSelectionStart"), ("Stop", "selStop", "OnCharacterSelectionStop"))
    g.call("gi", GFL + ":GetFSDGameInstance")
    valid(g, "giOk", "gi.ReturnValue")
    for suffix, event, prop in events:
        g.node("bind" + suffix, "adddelegate", name=prop, **{"class": GAMEINSTANCE})
        g.link("gi.ReturnValue", "bind%s.self" % suffix)
        g.link(event + ".OutputDelegate", "bind%s.Delegate" % suffix)
    first, last = start_poll(g, "pollA", rig)
    g.call("tryNow", "TryShow")
    g.flow(after, "brGiOk", "bindStart", "bindStop", first)
    g.flow("brGiOk.else", first)
    g.flow(last, "tryNow")
    # Start: only the class choice (Selection) restarts the poll and tries at once; the other camera spots are
    # customization, forge, end screen, ...
    g.node("isSel", "select", index=CAMERA_LOCATION, type={"type": "bool"})
    g.link("selStart.selectionLocation", "isSel.Index")
    g.defaults["isSel.Selection"] = "true"
    g.branch("brSel", "isSel.ReturnValue")
    first, last = start_poll(g, "pollB", rig)
    g.call("tryStart", "TryShow")
    g.flow("selStart", "brSel", first)
    g.flow(last, "tryStart")
    # Stop: hide the tooltips; the overlay stays with the screen.
    valid(g, "stopSel", g.get("selS0", "SelectUI"))
    g.call("pause", cls(SELECT) + ":OnStop", target=ref(g.get("selS1", "SelectUI")))
    g.flow("selStop", "brStopSel", "pause")
    g.node("end", "event", name="ReceiveEndPlay", **{"class": ACTOR})
    g.call("gi2", GFL + ":GetFSDGameInstance")
    valid(g, "gi2Ok", "gi2.ReturnValue")
    for suffix, event, prop in events:
        g.node("unbind" + suffix, "removedelegate", name=prop, **{"class": GAMEINSTANCE})
        g.link("gi2.ReturnValue", "unbind%s.self" % suffix)
        g.link(event + ".OutputDelegate", "unbind%s.Delegate" % suffix)
    g.call("endClear", KSL + ":K2_ClearTimer", Object=ref(g.self_()), FunctionName="SelectPoll")
    g.call("hideEnd", "HideSelect")
    g.flow("end", "brGi2Ok", "unbindStart", "unbindStop", "endClear", "hideEnd")
    g.flow("brGi2Ok.else", "endClear")


def g_mod_events(rig):
    """BeginPlay: one DB_Mod only; find or spawn DB_Data; on the host spawn DB_PerkShare_v1; wait for the
    local player controller, then take input and hook the class selection overlay (select_events; rig: InitSpacerig).
    B toggles the window on release, after a press the game saw."""
    g = Graph()
    g.node("begin", "event", name="ReceiveBeginPlay", **{"class": ACTOR})
    me = g.self_()
    g.call("all", GS + ":GetAllActorsOfClass", ActorClass=cls(CORE))
    g.call("count", KARR + ":Array_Length", TargetArray=ref("all.OutActors"))
    many = kml(g, "many", "Greater_IntInt", A=ref("count.ReturnValue"), B="1")
    g.call("first", KARR + ":Array_Get", TargetArray=ref("all.OutActors"), Index="0")
    not_me = kml(g, "notMe", "NotEqual_ObjectObject", A=ref("first.Item"), B=ref(me))
    g.branch("brDup", kml(g, "dup", "BooleanAND", A=ref(many), B=ref(not_me)))
    g.call("destroy", ACTOR + ":K2_DestroyActor")
    g.flow("begin", "all", "brDup", "destroy")
    # DB_Data: one per world, client side. No reference is kept: the toggle finds it again on each key press.
    g.call("findData", GS + ":GetActorOfClass", ActorClass=cls(DATA))
    valid(g, "hasData", "findData.ReturnValue")
    g.call("xform", KML + ":MakeTransform")
    g.call("spawnData", GS + ":BeginDeferredActorSpawnFromClass", ActorClass=cls(DATA),
           SpawnTransform=ref("xform.ReturnValue"), CollisionHandlingOverride="AlwaysSpawn", Owner=ref(me))
    g.call("finishData", GS + ":FinishSpawningActor", Actor=ref("spawnData.ReturnValue"),
           SpawnTransform=ref("xform.ReturnValue"))
    g.flow("brDup.else", "hubApi")
    # Mod Hub: DB_Hub gives it the hotkey page. Loaded by path and only when Mod Hub's IHubMod loads, so the mod
    # has no reference to Mod Hub and works without it.
    g.call("hubApiPath", KSL + ":MakeSoftClassPath", PathString=MODHUB + "IHubMod.IHubMod_C")
    g.call("hubApiSoft", KSL + ":Conv_SoftClassPathToSoftClassRef", SoftClassPath=ref("hubApiPath.ReturnValue"))
    g.call("hubApi", KSL + ":LoadClassAsset_Blocking", AssetClass=ref("hubApiSoft.ReturnValue"))
    g.call("hubApiOk", KSL + ":IsValidClass", Class=ref("hubApi.ReturnValue"))
    g.branch("brHub", "hubApiOk.ReturnValue")
    g.call("hubPath", KSL + ":MakeSoftClassPath", PathString=cls(HUBMOD))
    g.call("hubSoft", KSL + ":Conv_SoftClassPathToSoftClassRef", SoftClassPath=ref("hubPath.ReturnValue"))
    g.call("hubLoad", KSL + ":LoadClassAsset_Blocking", AssetClass=ref("hubSoft.ReturnValue"))
    g.node("hubCast", "classcast", **{"class": ACTOR})
    g.link("hubLoad.ReturnValue", "hubCast.Class")
    g.call("hubXform", KML + ":MakeTransform")
    g.call("hubSpawn", GS + ":BeginDeferredActorSpawnFromClass", ActorClass=ref("hubCast.$cast"),
           SpawnTransform=ref("hubXform.ReturnValue"), CollisionHandlingOverride="AlwaysSpawn", Owner=ref(me))
    g.call("hubFinish", GS + ":FinishSpawningActor", Actor=ref("hubSpawn.ReturnValue"),
           SpawnTransform=ref("hubXform.ReturnValue"))
    g.flow("hubApi", "brHub", "hubLoad", "hubCast", "hubSpawn", "hubFinish", "findData")
    g.flow("brHub.else", "findData")
    g.flow("hubCast.CastFailed", "findData")
    g.flow("findData", "brHasData", "brServer")
    g.flow("brHasData.else", "spawnData", "finishData", "brServer")
    # Perk share: the host only, once.
    g.call("server", KSL + ":IsServer")
    g.branch("brServer", "server.ReturnValue")
    g.call("findShare", GS + ":GetActorOfClass", ActorClass=cls(SHARE))
    valid(g, "hasShare", "findShare.ReturnValue")
    g.call("spawnShare", GS + ":BeginDeferredActorSpawnFromClass", ActorClass=cls(SHARE),
           SpawnTransform=ref("xform.ReturnValue"), CollisionHandlingOverride="AlwaysSpawn")
    g.call("finishShare", GS + ":FinishSpawningActor", Actor=ref("spawnShare.ReturnValue"),
           SpawnTransform=ref("xform.ReturnValue"))
    g.flow("brServer", "findShare", "brHasShare", "brPC")
    g.flow("brHasShare.else", "spawnShare", "finishShare", "brPC")
    g.flow("brServer.else", "brPC")
    # Wait for the local player controller (late join), then take input.
    g.call("pcGet", GS + ":GetPlayerController", PlayerIndex="0")
    g.call("pcOk", KSL + ":IsValid", Object=ref("pcGet.ReturnValue"))
    g.branch("brPC", "pcOk.ReturnValue")
    g.call("input", ACTOR + ":EnableInput", PlayerController=ref("pcGet.ReturnValue"))
    g.call("delay", KSL + ":Delay", Duration="0.5")
    g.flow("brPC", "input")
    g.flow("brPC.else", "delay", "brPC")
    select_events(g, "input", rig)
    # The hotkey (on release, see DB_Window.OnKeyUp): DB_Data.OpenKey, B unless changed in Mod Hub, so the event
    # is AnyKey and each press and release is compared with it. Not consumed: the key keeps working for anything
    # else bound to it. The press arms it: a release whose press went to chat or another UI does not open the
    # window. A press while our window is on top does not arm (the window closes itself on that key up).
    g.node("key", "inputkey", key="AnyKey", consume=False)
    for p in ("p", "r"):
        g.call(p + "Data", GS + ":GetActorOfClass", ActorClass=cls(DATA))
        valid(g, p + "HasData", p + "Data.ReturnValue")
        g.call(p + "Hotkey", cls(DATA) + ":OpenKey", target=ref(p + "Data.ReturnValue"))
        g.call(p + "Is", INPUTLIB + ":EqualEqual_KeyKey", A=ref("key.Key"), B=ref(p + "Hotkey.Key"))
        g.branch("br" + p.upper() + "Key", p + "Is.ReturnValue")
        g.flow(p + "Data", "br" + p.upper() + "HasData", p + "Hotkey", "br" + p.upper() + "Key")
    g.call("pTop", GFL + ":GetTopWindow")
    g.cast("pAsTop", cls(WINDOW), "pTop.ReturnValue")
    g.set("pDisarm", "KeyArmed", default="false")
    g.set("pArm", "KeyArmed", default="true")
    g.call("pNow", GS + ":GetRealTimeSeconds")
    g.set("pAt", "KeyArmedAt", value="pNow.ReturnValue")
    g.flow("key.Pressed", "pData")
    g.flow("brPKey", "pAsTop", "pDisarm")
    g.flow("pAsTop.CastFailed", "pArm", "pAt")
    g.flow("key.Released", "rData")
    toggle(g, "brRKey")
    return g.data()


def toggle(g, start):
    """Opens the window, or closes it when it is the top game window. Opens only when no game window is open
    (terminals, escape menu, end screen). While the window is open it has the input, so B usually reaches
    DB_Window.OnKeyUp instead. DB_Mod keeps no variables (see members()); KeyArmed is on the children.
    Closing needs no armed press; opening does, and every release disarms."""
    win_cls = cls(WINDOW)
    g.call("top", GFL + ":GetTopWindow")
    g.cast("asTop", win_cls, "top.ReturnValue")
    g.call("dismiss", win_cls + ":Dismiss", target=ref("asTop.$cast"))
    g.set("disarmTop", "KeyArmed", default="false")
    g.flow(start, "asTop", "dismiss", "disarmTop")
    # Armed, and pressed at most 1.5 s ago: a press whose release went to chat does not stay armed for later.
    g.call("rNow", GS + ":GetRealTimeSeconds")
    g.call("held", KML + ":Subtract_FloatFloat", A=ref("rNow.ReturnValue"), B=ref(g.get("armedAt", "KeyArmedAt")))
    g.call("recent", KML + ":Less_FloatFloat", A=ref("held.ReturnValue"), B="1.5")
    g.call("armedNow", KML + ":BooleanAND", A=ref(g.get("armed", "KeyArmed")), B=ref("recent.ReturnValue"))
    g.branch("brArmed", "armedNow.ReturnValue")
    g.set("disarm", "KeyArmed", default="false")
    g.flow("asTop.CastFailed", "brArmed", "disarm", "dataNow")
    # Through the game's window manager: it handles cursor, input mode and the close command.
    g.call("dataNow", GS + ":GetActorOfClass", ActorClass=cls(DATA))
    data = "dataNow.ReturnValue"
    g.call("wm", GFL + ":GetWindowManager")
    wm = "wm.ReturnValue"
    valid(g, "hasWm", wm)
    g.call("any", WINDOWMANAGER + ":AnyWindowsOpen", target=ref(wm))
    g.branch("brAny", "any.ReturnValue")
    g.call("open", WINDOWMANAGER + ":OpenWindowFromClass", target=ref(wm), WindowClass=win_cls, ZOrder=str(ZORDER),
           ShowCursor="true")
    g.cast("asWin", win_cls, "open.ReturnValue")
    g.set("wmMode", "Manual", win_cls, "asWin.$cast", default="false")
    g.set("wmData", "Data", win_cls, "asWin.$cast", data)
    g.call("wmOpen", win_cls + ":Open", target=ref("asWin.$cast"))
    g.flow("dataNow", "brHasWm", "brAny")
    g.flow("brAny.else", "open", "asWin", "wmMode", "wmData", "wmOpen")
    # By hand, when there is no window manager or it did not open the window. A window opened by hand that is
    # still open is closed instead (normally its own OnKeyUp does that).
    g.flow("brHasWm.else", "shown")
    g.flow("asWin.CastFailed", "shown")
    g.call("shown", WBL + ":GetAllWidgetsOfClass", WidgetClass=win_cls, TopLevelOnly="true")
    g.call("nShown", KARR + ":Array_Length", TargetArray=ref("shown.FoundWidgets"))
    g.branch("brShown", kml(g, "anyShown", "Greater_IntInt", A=ref("nShown.ReturnValue"), B="0"))
    g.call("old", KARR + ":Array_Get", TargetArray=ref("shown.FoundWidgets"), Index="0")
    g.call("closeOld", win_cls + ":Dismiss", target=ref("old.Item"))
    g.flow("shown", "brShown", "closeOld")
    g.call("pc", GS + ":GetPlayerController", PlayerIndex="0")
    pc = "pc.ReturnValue"
    g.call("create", WBL + ":Create", WidgetType=win_cls, OwningPlayer=ref(pc))
    g.cast("asNew", win_cls, "create.ReturnValue")
    win = "asNew.$cast"
    g.set("byHand", "Manual", win_cls, win, default="true")
    g.call("add", UMG + "UserWidget:AddToViewport", target=ref(win), ZOrder=str(ZORDER))
    g.set("handData", "Data", win_cls, win, data)
    g.call("uiOnly", WBL + ":SetInputMode_UIOnlyEx", PlayerController=ref(pc), InWidgetToFocus=ref(win),
           InMouseLockMode="DoNotLock")
    g.set("cursor", "bShowMouseCursor", PLAYERCONTROLLER, pc, default="true")
    g.call("handOpen", win_cls + ":Open", target=ref(win))
    g.flow("brShown.else", "create", "asNew", "byHand", "add", "handData", "uiOnly", "cursor", "handOpen")


# ============================================================================= module interface

def trees():
    return {CHIP: chip_tree(), SLOTBTN: slotbtn_tree(), TAKE: take_tree(), WINDOW: window_tree(),
            SELECT: select_tree()}


def init_members():
    """InitSpacerig / InitCave. KeyArmed: B was pressed while the game had the input (the release may open the
    window). SelectUI: the class selection overlay of this level; ScreenClass, AnchorClass (loaded once,
    ClassesTried), ScreenTmp, CanvasTmp, ZTmp: TryShow's working values; PollUntil: end of the fast poll;
    PollSlow: the Space Rig's poll runs at SLOW_POLL."""
    return {"variables": [t("KeyArmed", B), t("KeyArmedAt", F), obj("SelectUI", cls(SELECT)),
                          t("ScreenClass", "class", USERWIDGET), t("AnchorClass", "class", USERWIDGET),
                          t("ClassesTried", B), obj("ScreenTmp", USERWIDGET), obj("CanvasTmp", CANVAS),
                          t("ZTmp", I, default=str(ZORDER_MISSION)), t("PollUntil", F), t("PollSlow", B)],
            "functions": [{"name": "TryShow"}, {"name": "FindScreen"}, {"name": "SelectPoll"},
                          {"name": "HideSelect"}]}


def members():
    return {
        CHIP: {"variables": [], "functions": [
            {"name": "SetIcon", "inputs": [obj("Texture", TEXTURE)]},
            {"name": "SetWidth", "inputs": [t("Width", F)]},
        ]},
        TAKE: {"variables": [
            t("Code", S), obj("CodeClass", CHARID), t("SlotCount", I, default="0"), t("CurrentSlot", I, default="0"),
            t("Picked", I, default="0"), t("CanSave", B), t("Saved", B), obj("Buttons", cls(SLOTBTN), array=True),
        ], "functions": [
            {"name": "UpdateSlots"},
            {"name": "SlotLabel", "inputs": [t("SlotIndex", I)], "outputs": [t("Label", S)]},
            {"name": "GetButton", "inputs": [t("ButtonIndex", I)], "outputs": [obj("Button", cls(SLOTBTN))]},
            {"name": "SyncCheck"},
            {"name": "SaveNow"},
        ]},
        WINDOW: {"variables": [
            obj("Players", PS, array=True), t("PlayerClass", I, array=True), t("Shown", I, array=True),
            t("ClassCounts", I, array=True), t("Filter", I, default="0"), t("PageStart", I, default="0"),
            t("Tab", I, default="0"), obj("Columns", cls(COLUMN), array=True), obj("Chips", cls(CHIP), array=True),
            t("ChipWidth", F, default=str(float(CHIP_MAX))), t("Manual", B), t("Inited", B), t("TakeOpen", B),
            t("OpenTmp", B), t("CodeText", S), t("CodeValid", B), t("PanelWidth", I, default=str(PANEL_WIDTH)),
            # RosterSame: what the chips were last drawn from (Rp...), and its working values (Rs...).
            obj("RpPlayers", PS, array=True), t("RpShown", I, array=True), obj("RpClasses", CHARID, array=True),
            t("RpNames", S, array=True), t("RpPage", I, default="-1"), obj("RsClasses", CHARID, array=True),
            t("RsNames", S, array=True), t("RsSame", B),
        ], "functions": [
            {"name": "Refresh"}, {"name": "TimerRefresh"}, {"name": "Collect"}, {"name": "UpdateWidth"},
            {"name": "RosterSame", "outputs": [t("Same", B)]},
            {"name": "ClassIndex", "inputs": [obj("Player", PS)], "outputs": [t("Index", I)]},
            {"name": "ShowPage"}, {"name": "UpdateHeader"}, {"name": "UpdateRoster"},
            {"name": "FitToScreen", "inputs": [t("WithRoster", B)]},
            {"name": "GetChip", "inputs": [t("ChipIndex", I)], "outputs": [obj("Chip", cls(CHIP))]},
            {"name": "SetFilter", "inputs": [t("NewFilter", I)]},
            {"name": "SetTab", "inputs": [t("NewTab", I)]},
            {"name": "PageBy", "inputs": [t("Step", I)]},
            {"name": "Dismiss"}, {"name": "Stop"}, {"name": "HideAllTips"},
            {"name": "IsOpenNow", "outputs": [t("bOpen", B)]},
            {"name": "InitOnce"},
            {"name": "UpdateCode", "inputs": [t("NewText", S)]},
            {"name": "PasteCode"}, {"name": "CopyMine"},
            {"name": "OpenSite", "inputs": [t("URL", S)]}, {"name": "PublishMine"},
            {"name": "OnKeyUp", "override": True},
            {"name": "OnKeyDown", "override": True},
            {"name": "OnMouseButtonDown", "override": True},
            {"name": "ReceiveCanCloseWindow", "override": True},
        ]},
        SELECT: {"variables": [
            obj("Data", cls(DATA)), obj("Screen", USERWIDGET), obj("Canvas", CANVAS), obj("Mates", PS, array=True),
            obj("TeamCols", cls(COLUMN), array=True), t("Inited", B), t("UpTmp", B),
            t("BecTmp", B), t("WasUp", B), t("Odd", B), obj("Desc", UMG + "Widget"),
            # Tick's check of your column: the class and loadout it last showed.
            obj("OwnClass", CHARID), t("OwnLoadout", I, default="-1"),
            # FitScale's inputs: the overlay's size (from Tick) and the team column count (from Refresh).
            t("ViewW", F), t("ViewH", F), t("TeamCount", I, default="0"),
            t("DescClass", "class", USERWIDGET),
        ], "functions": [
            {"name": "AttachTo", "inputs": [obj("NewScreen", USERWIDGET), obj("NewCanvas", CANVAS),
                                            obj("NewData", cls(DATA)), t("Layer", I)]},
            {"name": "IsAttached", "outputs": [t("Up", B)]},
            {"name": "Update", "outputs": [t("Up", B), t("Became", B)]},
            {"name": "Detach"}, {"name": "OnStop"}, {"name": "Refresh"},
            {"name": "FitScale", "inputs": [t("Count", I)]},
            {"name": "FindDesc"}, {"name": "HideDesc"},
            {"name": "OnPreviewMouseButtonDown", "override": True},
        ]},
        # DB_Mod gets no members and no graphs: compiling it after its children (InitSpacerig, InitCave) exist
        # trips an engine ensure in the reinstancer (a REINST class parented to a REINST class) and fails the
        # build. Its logic is generated into both children instead (graphs()), and so are its variables.
        INIT_SPACERIG: init_members(),
        INIT_CAVE: init_members(),
    }


def init_graphs(rig):
    return {"EventGraph": g_mod_events(rig), "TryShow": g_init_try_show(), "FindScreen": g_init_find_screen(),
            "SelectPoll": g_init_poll(rig), "HideSelect": g_init_hide_select()}


def graphs():
    return {
        CHIP: {"Set": g_chip_set(), "SetIcon": g_chip_set_icon(), "SetWidth": g_chip_set_width(),
               "EventGraph": g_chip_events()},
        SLOTBTN: {"Set": g_slotbtn_set(), "EventGraph": g_slotbtn_events()},
        TAKE: {"Show": g_take_show(), "PickSlot": g_take_pick(), "UpdateSlots": g_take_update(),
               "SlotLabel": g_take_slot_label(), "GetButton": g_take_get_button(), "SyncCheck": g_take_sync_check(),
               "SaveNow": g_take_save(), "EventGraph": g_take_events()},
        WINDOW: {"Open": g_win_open(), "OpenTake": g_win_open_take(), "SelectPlayer": g_win_select_player(),
                 "CloseTake": g_win_close_take(), "Refresh": g_win_refresh(), "TimerRefresh": g_win_timer_refresh(),
                 "Collect": g_win_collect(), "UpdateWidth": g_win_update_width(),
                 "ClassIndex": g_win_class_index(), "ShowPage": g_win_show_page(),
                 "UpdateHeader": g_win_update_header(), "UpdateRoster": g_win_update_roster(),
                 "RosterSame": g_win_roster_same(),
                 "FitToScreen": g_win_fit(),
                 "GetChip": g_win_get_chip(), "SetFilter": g_win_set_filter(), "SetTab": g_win_set_tab(),
                 "PageBy": g_win_page_by(), "Dismiss": g_win_dismiss(), "Stop": g_win_stop(),
                 "HideAllTips": g_win_hide_tips(),
                 "IsOpenNow": g_win_is_open(), "InitOnce": g_win_init_once(), "UpdateCode": g_win_update_code(),
                 "PasteCode": g_win_paste_code(), "CopyMine": g_win_copy_mine(), "OnKeyUp": g_win_on_key_up(),
                 "OpenSite": g_win_open_site(), "PublishMine": g_win_publish(),
                 "OnKeyDown": g_win_on_key_down(), "OnMouseButtonDown": g_win_on_mouse_down(),
                 "ReceiveCanCloseWindow": g_win_can_close(), "EventGraph": g_win_events()},
        SELECT: {"AttachTo": g_sel_attach(), "IsAttached": g_sel_is_attached(), "Update": g_sel_update(),
                 "Detach": g_sel_detach(), "OnStop": g_sel_on_stop(), "Refresh": g_sel_refresh(),
                 "FitScale": g_sel_fit(), "FindDesc": g_sel_find_desc(), "HideDesc": g_sel_hide_desc(),
                 "OnPreviewMouseButtonDown": g_sel_mouse_down(), "EventGraph": g_sel_events()},
        # The same graphs in both children (but the poll); DB_Mod stays an empty parent (see members()).
        INIT_SPACERIG: init_graphs(True),
        INIT_CAVE: init_graphs(False),
    }


def class_defaults():
    # Focusable so B and Escape reach OnKeyUp. The game's close-command handling keeps its default.
    return {WINDOW: {"bIsFocusable": "True"}}
