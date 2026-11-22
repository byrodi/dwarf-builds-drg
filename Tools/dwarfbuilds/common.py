"""Paths, game types, colours, fonts and widget-tree helpers shared by the Dwarf Builds spec modules.

Colours are the game's own (linear values read from LIB_MenuColors, LIB_PerkColors, SCAT_OC_* and PCD_*).
Fonts are the game's three UI fonts; the editor stubs in Content/Art/Fonts resolve to the real fonts in game.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bp_dsl import ACTOR, GS, KARR, KMAP, KML, KSL, KSTR, KTXT, UMG, WBL, Graph, ref, t  # noqa: F401,E402

MOD_NAME = "Dwarf Builds"
MOD_VERSION = "0.2.0"
CODE_VERSION = "DB1"  # first field of a build code
SITE_URL = "https://dwarfbuilds.pages.dev"   # the website (BROWSE, PUBLISH MY BUILD, OPEN IN BROWSER)

MOD = "/Game/_DwarfBuilds/"
UI = MOD + "UI/"


def cls(path):
    """Generated class path of a mod asset: /Game/_DwarfBuilds/UI/DB_Tip -> /Game/_DwarfBuilds/UI/DB_Tip.DB_Tip_C."""
    name = path.rsplit("/", 1)[1]
    return "%s.%s_C" % (path, name)


# Mod assets (paths). Their classes: cls(path).
DATA = MOD + "DB_Data"
SHARE = MOD + "Net/DB_PerkShare_v1"   # replicated layout is frozen: a new layout needs a new path
LINK = MOD + "Net/DB_BuildShare_v2"   # one per player: the player's build code (frozen layout too, see contract)
CORE = MOD + "DB_Mod"
INIT_SPACERIG = MOD + "InitSpacerig"
INIT_CAVE = MOD + "InitCave"
WINDOW = UI + "DB_Window"
TAKE = UI + "DB_TakeDialog"
COLUMN = UI + "DB_Column"
CARD = UI + "DB_WeaponCard"
GEAR = UI + "DB_GearRow"
CELL = UI + "DB_UpgCell"
PERK = UI + "DB_PerkTile"
TIP = UI + "DB_Tip"
CHIP = UI + "DB_Chip"
SLOTBTN = UI + "DB_SlotBtn"
SELECT = UI + "DB_Select"             # builds shown on the game's class selection screen
SETTINGS = MOD + "DB_Settings"        # the mod's own save game (save slot SAVE_SLOT)
HUBMOD = MOD + "DB_Hub"               # registers the mod with Mod Hub (spawned only when Mod Hub is installed)
HUBPAGE = UI + "DB_HubPage"           # the mod's Mod Hub page: the hotkey
MODHUB = "/Game/_ModHub/"             # Mod Hub's interfaces; never imported, only loaded by path
KEY = "/Script/InputCore.Key"
DEFAULT_KEY = "B"                     # the hotkey until the player picks another in Mod Hub
SAVE_SLOT = "DwarfBuilds"

# Game and engine types.
FSD = "/Script/FSD."
PS = FSD + "FSDPlayerState"
GAMESTATE = FSD + "FSDGameState"
PC = FSD + "FSDPlayerController"
CHARID = FSD + "PlayerCharacterID"
ITEMID = FSD + "ItemID"
ITEMDATA = FSD + "ItemData"
UPGRADE = FSD + "ItemUpgrade"
OVERCLOCK = FSD + "OverclockUpgrade"
PERKASSET = FSD + "PerkAsset"
PROFASSET = FSD + "ProficiencyPerkAsset"
PERKTYPE = FSD + "EPerkUsageType"
ONLINE = FSD + "FSDOnlineSystemUtils"
SAVEGAME = FSD + "FSDSaveGame"
SGSC = FSD + "SaveGameStateComponent"
GEARCOMP = FSD + "UpgradableGearComponent"
INVLIST = FSD + "InventoryList"
GFL = FSD + "GameFunctionLibrary"
AFL = FSD + "ActorFunctionLibrary"
PFL = FSD + "PerkFunctionLibrary"
LFL = FSD + "LoadoutFunctionLibrary"
FRONTEND = FSD + "FrontendBlueprintLibrary"
WINDOWWIDGET = FSD + "WindowWidget"
WINDOWMANAGER = FSD + "WindowManager"
LOADOUTCOPY = FSD + "LoadoutCopy"
ITEMLOADOUT = FSD + "ItemLoadout"
UPGRADELOADOUT = FSD + "UpgradeLoadout"
SELECTION = FSD + "ItemUpgradeSelection"
UPGRADETIER = FSD + "UpgradeTier"
PERKITEM = FSD + "SaveGameStatePerkItem"
CHARSAVE = FSD + "CharacterSave"
GUID = "/Script/CoreUObject.Guid"
LINEAR = "/Script/CoreUObject.LinearColor"
TEXTURE = "/Script/Engine.Texture2D"
USERWIDGET = UMG + "UserWidget"

# Code slots (order of the parts in a build code) and the game's item category of each (EItemCategory index).
# The names are FItemLoadout fields. The flare is not a code slot.
SLOTS = ["PrimaryWeapon", "SecondaryWeapon", "TraversalTool", "ClassTool", "Armor", "Grenade", "MiningTool"]
SLOT_CATEGORY = {"PrimaryWeapon": 0, "SecondaryWeapon": 1, "TraversalTool": 2, "ClassTool": 3, "Grenade": 4,
                 "MiningTool": 6, "Armor": 7}
SLOT_LIST = {"PrimaryWeapon": "PrimaryWeapons", "SecondaryWeapon": "SecondaryWeapons", "TraversalTool": "TraversalTools",
             "ClassTool": "ClassTools", "Armor": "Armors", "Grenade": "Grenades",
             "MiningTool": "MiningTools"}  # UInventoryList arrays
GEAR_LABELS = ["TRAVERSAL", "SUPPORT", "ARMOR", "GRENADE"]  # code slots 2..5 (the column's gear cards)
SHOWN_SLOTS = 6   # code slots 0..5 are shown in a column; slot 6 (pickaxe) is only in the code and TAKE BUILD

# Perk IDs of the build code: ID = position in Tools/dwarfbuilds/perk_ids.json + 1 (frozen, append-only; the website
# uses the same file). Read when the spec is made and baked into DB_Data as a literal list of asset names.
PERK_IDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perk_ids.json")


def perk_names():
    with open(PERK_IDS_FILE, encoding="utf-8") as ids:
        names = json.load(ids)
    assert names and len(set(names)) == len(names), "perk_ids.json: empty or duplicate names"
    return names


# Runtime-loaded textures (not in the project; DB_Data loads them by path asynchronously when it spawns).
TEX_HEX_BG = "/Game/UI/Menu_Loadout/Assets/Upgrade_BG.Upgrade_BG"
TEX_HEX_OUTLINE = "/Game/UI/Menu_Loadout/Assets/Upgrade_Outline.Upgrade_Outline"
TEX_OC_FRAME = {
    "Clean": "/Game/UI/Art/Icons/Icons_Overclocks/Rewards/RewardFrame_OverclockClean.RewardFrame_OverclockClean",
    "Balanced": "/Game/UI/Art/Icons/Icons_Overclocks/Rewards/RewardFrame_OverclockBalanced.RewardFrame_OverclockBalanced",
    "Unstable": "/Game/UI/Art/Icons/Icons_Overclocks/Rewards/RewardFrame_OverclockUnstable.RewardFrame_OverclockUnstable",
}


def rgba(r, g, b, a=1.0):
    return "(R=%g,G=%g,B=%g,A=%g)" % (r, g, b, a)


# The game's UI colours (linear).
ORANGE = (1.0, 0.332452, 0.0)          # Main Tint Base
ORANGE_LIGHT = (1.0, 0.645482, 0.0)    # Main Tint Light
DARK = (0.104167, 0.052518, 0.026584)  # Main Tint Dark
VERY_DARK = (0.03125, 0.019749, 0.013835)
WINDOW_BG = (0.0, 0.0, 0.0, 0.7)
SELECTED_BG = (0.098958, 0.050001, 0.024822, 0.8)
WHITE = (1.0, 1.0, 1.0)
GREY = (0.416667, 0.416667, 0.416667)
GREY_DARK = (0.03434, 0.03434, 0.03434)
WARNING = (0.838542, 0.0, 0.0)
APPROVAL = (0.089577, 0.760417, 0.0)
PERK_PASSIVE = (0.484375, 0.027751, 0.07654)
PERK_ACTIVE = (0.07053, 0.520833, 0.375543)
PERK_PROF = ORANGE                     # proficiency perks (the game's orange)
OC_COLOURS = {"Clean": (0.03819, 0.33333, 0.10949), "Balanced": (0.8125, 0.58836, 0.03809),
              "Unstable": (0.65104, 0.03653, 0.0)}


def colour(c, a=None):
    """FLinearColor import text from a tuple."""
    if a is None:
        a = c[3] if len(c) > 3 else 1.0
    return rgba(c[0], c[1], c[2], a)


def slate(c, a=None):
    """FSlateColor import text from a tuple."""
    return "(SpecifiedColor=%s,ColorUseRule=UseColor_Specified)" % colour(c, a)


# The game's fonts (FontObject, typeface).
RIFT = ("/Game/Art/Fonts/Rift_Soft.Rift_Soft", "Rift Soft Bold")             # headers, item names
CARBON = ("/Game/Art/Fonts/Carbon.Carbon", "2. Bold")                        # categories, numbers, digits
CARBON_REG = ("/Game/Art/Fonts/Carbon.Carbon", "1. Regular")
BODY = ("/Game/Art/Fonts/Acumin_Pro_Condensed.Acumin_Pro_Condensed", "Condensed Normal")  # descriptions
BODY_BOLD = ("/Game/Art/Fonts/Acumin_Pro_Condensed.Acumin_Pro_Condensed", "Condensed Bold")


def font(face, size):
    return "(FontObject=Font'%s',TypefaceFontName=\"%s\",Size=%d)" % (face[0], face[1], size)


# ----------------------------------------------------------------------------- widget-tree helpers
# A tree node: {"class", "name", "var", "props", "slot", "children"}. "slot" holds the props of the slot in the
# parent (HorizontalBoxSlot, VerticalBoxSlot, OverlaySlot, CanvasPanelSlot, ...).

def w(widget_class, name, var=False, props=None, slot=None, children=None):
    node = {"class": widget_class if widget_class.startswith("/") else UMG + widget_class, "name": name, "var": var}
    if props:
        node["props"] = props
    if slot:
        node["slot"] = slot
    if children is not None:
        node["children"] = children
    return node


def text(name, content, face, size, c=WHITE, var=False, slot=None, wrap=False, justify=None, upper=False):
    props = {"Text": content, "Font": font(face, size), "ColorAndOpacity": slate(c)}
    if wrap:
        props["AutoWrapText"] = "True"
    if justify:
        props["Justification"] = justify  # ETextJustify::Left/Center/Right
    if upper:
        props["TextTransformPolicy"] = "ToUpper"
    return w("TextBlock", name, var, props, slot)


def box(name, width=None, height=None, child=None, var=False, slot=None):
    """SizeBox with a fixed width and/or height. Fixed sizes keep every column and card the same size."""
    props = {}
    if width is not None:
        props.update({"WidthOverride": str(width), "bOverride_WidthOverride": "True"})
    if height is not None:
        props.update({"HeightOverride": str(height), "bOverride_HeightOverride": "True"})
    return w("SizeBox", name, var, props, slot, [child] if child else [])


def border(name, fill, child=None, pad=(0, 0, 0, 0), var=False, slot=None, halign=None, valign=None):
    props = {"BrushColor": colour(fill), "Padding": margin(*pad)}
    if halign:
        props["HorizontalAlignment"] = halign
    if valign:
        props["VerticalAlignment"] = valign
    return w("Border", name, var, props, slot, [child] if child else [])


def image(name, c=WHITE, size=None, var=False, slot=None):
    props = {"ColorAndOpacity": colour(c)}
    if size:
        props["Brush"] = "(ImageSize=(X=%g,Y=%g))" % size
    return w("Image", name, var, props, slot)


def margin(left=0, top=0, right=0, bottom=0):
    return "(Left=%g,Top=%g,Right=%g,Bottom=%g)" % (left, top, right, bottom)


def hslot(fill=False, pad=(0, 0, 0, 0), halign=None, valign="VAlign_Center"):
    """HorizontalBoxSlot / VerticalBoxSlot props."""
    props = {"Padding": margin(*pad)}
    if fill:
        props["Size"] = "(Value=1.0,SizeRule=Fill)"
    if halign:
        props["HorizontalAlignment"] = halign
    if valign:
        props["VerticalAlignment"] = valign
    return props


def vslot(fill=False, pad=(0, 0, 0, 0), halign=None, valign=None):
    return hslot(fill, pad, halign, valign)


def oslot(halign="HAlign_Fill", valign="VAlign_Fill", pad=(0, 0, 0, 0)):
    """OverlaySlot props."""
    return {"HorizontalAlignment": halign, "VerticalAlignment": valign, "Padding": margin(*pad)}


BLACK_TEXT = (0.01, 0.01, 0.01)
LIGHT_TEXT = (0.85, 0.76, 0.55)
BTN_BAR, BTN_GAP = 4, 4
BTN_BAR_DIM = (0.2, 0.11, 0.055)   # side bars of a secondary (inactive) button: dim brown, not orange
BTN_OFF = (0.14, 0.125, 0.11)      # fill of a disabled primary button: the grey Slate dims its orange bars to


def _btn_brush(c):
    return "(ResourceObject=None,ResourceName=None,DrawAs=Image,TintColor=%s)" % slate(c)


def game_button(name, label, size, primary=True, height=44, width=None, slot=None, enabled=True, pad=(16, 3, 16, 0)):
    """The game's action button (its CLOSE / SERVER LIST): a fill with the label in Rift Soft and, on each side, a
    4 px bar with a 4 px gap. primary: orange fill, black text; else dark fill, light text (inactive tab, secondary
    action). Variables: `name` (the Button: bind OnClicked to it) and `name`Wrap (the whole button: SetIsEnabled on
    it, so the bars dim with the fill) and `name`Text. Never takes keyboard focus (the window keeps its keys)."""
    # A secondary button turns orange while it is held down, like the game's buttons (see press_feedback).
    fill, hover, press = ((ORANGE, ORANGE_LIGHT, (0.8, 0.22, 0.0)) if primary else
                          (DARK, (0.16, 0.08, 0.04), ORANGE))
    ink = BLACK_TEXT if primary else LIGHT_TEXT
    bar_colour = ORANGE if primary else BTN_BAR_DIM
    # Only the horizontal padding comes from the caller. Vertically the label is centred on its capitals: Rift Soft
    # has capitals only, and they sit about 0.04 em below the centre of its line, so a bottom padding of about
    # 0.08 em lifts them to the middle of the button.
    pad = (pad[0], 0, pad[2], round(size * 0.08))
    # Slate draws a button's Disabled brush as it is, without dimming it (it dims the bars and the label), so a
    # disabled primary button has its own grey fill: an orange one would look enabled.
    off = BTN_OFF if primary else fill
    style = "(Normal=%s,Hovered=%s,Pressed=%s,Disabled=%s,NormalPadding=%s,PressedPadding=%s)" % (
        _btn_brush(fill), _btn_brush(hover), _btn_brush(press), _btn_brush(off), margin(*pad), margin(*pad))
    label_node = text(name + "Text", label, RIFT, size, ink, var=True, justify="Center")
    label_node["slot"] = {"HorizontalAlignment": "HAlign_Center", "VerticalAlignment": "VAlign_Center",
                          "Padding": margin()}
    button = w("Button", name, True, {"WidgetStyle": style, "IsFocusable": "False"},
               hslot(fill=True, valign="VAlign_Fill"), [label_node])

    def bar(side):
        return image(name + "Bar" + side, bar_colour, size=(BTN_BAR, height), var=True,
                     slot=hslot(valign="VAlign_Fill"))

    def gap(side):
        return w("Spacer", name + "Gap" + side, props={"Size": "(X=%d,Y=1)" % BTN_GAP}, slot=hslot())

    wrap_props = {} if enabled else {"bIsEnabled": "False"}
    row = w("HorizontalBox", name + "Wrap", True, wrap_props, children=[bar("L"), gap("L"), button, gap("R"), bar("R")])
    return box(name + "Size", width=width, height=height, slot=slot, child=row)


def press_feedback(g, name):
    """While a secondary game_button `name` is held down it looks like a primary one: the fill turns orange (its
    Pressed brush), and these two bound events in the owner's EventGraph `g` turn the side bars orange and the
    label black, and back on release (OnReleased also comes when the mouse is let go outside the button)."""
    for event, bar_colour, ink in (("OnPressed", ORANGE, BLACK_TEXT), ("OnReleased", BTN_BAR_DIM, LIGHT_TEXT)):
        steps = [g.node("pf%s%s" % (name, event), "boundevent", widget=name, name=event)]
        for side in "LR":
            nid = "pf%s%s%s" % (name, event, side)
            g.node(nid + "W", "get", var=name + "Bar" + side)
            g.call(nid, UMG + "Image:SetColorAndOpacity", target=ref(nid + "W." + name + "Bar" + side),
                   InColorAndOpacity=colour(bar_colour))
            steps.append(nid)
        nid = "pf%s%sT" % (name, event)
        g.node(nid + "W", "get", var=name + "Text")
        g.call(nid, UMG + "TextBlock:SetColorAndOpacity", target=ref(nid + "W." + name + "Text"),
               InColorAndOpacity=slate(ink))
        steps.append(nid)
        for a, b in zip(steps, steps[1:]):
            g.link(a + ".then", b + ".execute")


def soft_load(g, node_id, path, cast_to=TEXTURE):
    """Loads an asset by path at run time (no import in the cooked package). Returns the cast output pin.
    Exec chain: node_id + "Load" (call) -> node_id (cast)."""
    g.call(node_id + "Path", KSL + ":MakeSoftObjectPath", PathString=path)
    g.call(node_id + "Ref", KSL + ":Conv_SoftObjPathToSoftObjRef", SoftObjectPath=ref(node_id + "Path.ReturnValue"))
    g.call(node_id + "Load", KSL + ":LoadAsset_Blocking", Asset=ref(node_id + "Ref.ReturnValue"))
    out = g.cast(node_id, cast_to, node_id + "Load.ReturnValue")
    return out
