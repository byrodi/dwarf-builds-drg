"""The fixed part of the Dwarf Builds spec: every asset, its parent, its owner module, and its PUBLIC members
(the variables and functions other assets use). Modules add private members, widget trees and graphs.

Build phases (Tools/dwarfbuilds_spec.py): 1. declare every asset in DECLARE_ORDER (parent, widget tree, class
defaults); 2. "members" for every asset (public from here + private from its module); 3. "graphs".
So any asset may hold a variable of any other mod class, and a widget tree may contain mod widgets declared
before it.

BUILD CODE, version DB1 (written by DB_Data, read by DB_Data; widgets only show it). The website writes and reads the
same format (Docs/dwarfbuilds-site.md section 1; shared test vectors in Web/tests/code_vectors.json):
    DB1:<class>:<p0>:<p1>:<p2>:<p3>:<p4>:<p5>:<p6>:<perks>
  <class> = first letter of the PlayerCharacterID asset name (DrillerID -> D, EngineerID -> E, GunnerID -> G,
            ScoutID -> S).
  p0..p6 = the code slots in common.SLOTS order: primary, secondary, traversal tool, support (class) tool,
            armor, grenade, pickaxe. Each part is "<item>-<tiers>-<oc>":
    <item>  1-based index of the item in the class's inventory list for that slot
            (ActorFunctionLibrary.GetHeroInventoryList(class).<PrimaryWeapons|SecondaryWeapons|TraversalTools|
            ClassTools|Armors|Grenades|MiningTools>); 0 = unknown. The pickaxe is always item 1 (one per class),
            with two tiers and no overclocks ("1-12-0"). The flare is not in the code.
    <tiers> one digit per upgrade tier of the item (UpgradableGearComponent.GetItemUpgradeTiers(item class)):
            1..3 = the chosen option (index in FUpgradeTier.upgrades + 1), 0 = none. Empty for items with no tiers.
    <oc>    1-based index of the equipped overclock in Map_Keys(OverclockBank.Overclocks) of the item's
            UpgradableGearComponent (GetComponentFromClass on the item class, else ItemID.GetItem().UpgradableItem;
            see DB_Data.OverclocksOf), 0 = none. Not GetOverClocks(): that list is filled at run time.
  <perks> = the equipped perks joined with ".": passive ones, then active ones, then the proficiency, each in the
            order of the save. Each is its 1-based perk ID: position of the perk's asset name (GetObjectName) in
            Tools/dwarfbuilds/perk_ids.json + 1 (frozen, append-only). Unknown perks are left out. Empty = perks not
            known (a teammate whose perks nobody could tell); the code then ends with ":". Ranks are not in it.
  Example (an Engineer build): DB1:E:2-21123-2:1-21322-7:1-212-0:1-1221-0:1-1213-0:4--0:1-12-0:24.27.33.23
  Readers ignore extra digits/parts and treat missing ones as 0, so a code stays readable after a game update.
  Valid = DB1, a known class and at least one part whose item index is above 0. Characters: A-Z 0-9 : - .
"""
from dwarfbuilds.common import (CARD, CELL, CHARID, CHIP, COLUMN, CORE, DATA, GEAR, INIT_CAVE, INIT_SPACERIG, ITEMID,
                               LINEAR, OVERCLOCK, PERK, PERKASSET, PS, SHARE, SLOTBTN, TAKE, TEXTURE, TIP, UPGRADE,
                               USERWIDGET, WINDOW, WINDOWWIDGET, cls, t)
from dwarfbuilds.common import DEFAULT_KEY, HUBMOD, HUBPAGE, KEY, LINK, MODHUB, SELECT, SETTINGS

ACTOR = "/Script/Engine.Actor"

# Declaration order: a widget tree may only contain mod widgets declared before it.
# Graphs are built in this order too: DB_Data calls DB_BuildShare_v2's Server_SetCode, a custom event, which exists
# only once that asset's graphs are compiled, so LINK comes before DATA.
DECLARE_ORDER = [TIP, CELL, PERK, CARD, GEAR, COLUMN, CHIP, SLOTBTN, TAKE, WINDOW, SELECT, SETTINGS, LINK, DATA, SHARE,
                 HUBPAGE, HUBMOD, CORE, INIT_SPACERIG, INIT_CAVE]

ASSETS = {
    # path: (kind, parent class, owner module)
    TIP: ("widget", USERWIDGET, "widgets"),
    CELL: ("widget", USERWIDGET, "widgets"),
    PERK: ("widget", USERWIDGET, "widgets"),
    CARD: ("widget", USERWIDGET, "widgets"),
    GEAR: ("widget", USERWIDGET, "widgets"),
    COLUMN: ("widget", USERWIDGET, "widgets"),
    CHIP: ("widget", USERWIDGET, "shell"),
    SLOTBTN: ("widget", USERWIDGET, "shell"),
    TAKE: ("widget", USERWIDGET, "shell"),
    WINDOW: ("widget", WINDOWWIDGET, "shell"),
    # Overlay on the game's class selection screen (mission join, Space Rig class choice): teammates' columns on the
    # left, your own on the right in place of the game's class description box (its frame is hidden),
    # scaled down; shown and hidden by InitSpacerig/InitCave. Private API only.
    SELECT: ("widget", USERWIDGET, "shell"),
    # The mod's own settings, saved in slot common.SAVE_SLOT: MoreInfo and OpenKey (see DB_Data).
    SETTINGS: ("blueprint", "/Script/Engine.SaveGame", "data"),
    DATA: ("blueprint", ACTOR, "data"),
    SHARE: ("blueprint", ACTOR, "data"),
    LINK: ("blueprint", ACTOR, "data"),
    # Mod Hub (optional mod): its page sets the hotkey. Both implement Mod Hub interfaces, so nothing else may
    # reference them: DB_Mod loads DB_Hub by path and only when Mod Hub's IHubMod exists.
    HUBPAGE: ("widget", USERWIDGET, "hub"),
    HUBMOD: ("blueprint", ACTOR, "hub"),
    CORE: ("blueprint", ACTOR, "shell"),
    INIT_SPACERIG: ("blueprint", cls(CORE), "shell"),   # spawned by the mod loader on the Space Rig
    INIT_CAVE: ("blueprint", cls(CORE), "shell"),       # spawned by the mod loader in missions
}

# Interfaces an asset implements (BPForge "interfaces").
INTERFACES = {HUBPAGE: [MODHUB + "IHubPageWidget.IHubPageWidget_C"], HUBMOD: [MODHUB + "IHubMod.IHubMod_C"]}

S, I, B, TX = "string", "int", "bool", "text"


def obj(name, path, **extra):
    return t(name, "object", path, **extra)


PUBLIC = {
    DATA: {
        # Hexagon textures (common.TEX_HEX_BG / TEX_HEX_OUTLINE), loaded asynchronously when DB_Data spawns.
        # None until loaded (or if they cannot be loaded): widgets then draw plain shapes.
        # PerksOf_Share: the host's DB_PerkShare_v1 once a client found it (None on the host and before that).
        # Revision: counts the builds ApplyCode wrote into the save. A column compares both with what it last drew.
        "variables": [obj("HexBg", TEXTURE), obj("HexOutline", TEXTURE), obj("PerksOf_Share", cls(SHARE)),
                      t("Revision", I)],
        "functions": [
            # The local player's FSDPlayerState, or None.
            {"name": "LocalPS", "outputs": [obj("PS", PS)]},
            # Players in lobby order (AFSDGameState.GetNetworkSortedPlayerArray).
            {"name": "GetPlayers", "outputs": [obj("Players", PS, array=True)]},
            # Build code of a player; "" when the player has no class yet. Local player: from the save
            # (GetCurrentLoadout), worked out again only when the save's loadout or perks changed; others: their
            # DB_BuildShare_v2 (LinkFor), else the replicated SaveGameStateComponent.ItemUpgradeSelections.
            {"name": "CodeOf", "inputs": [obj("Player", PS)], "outputs": [t("Code", S)]},
            # The local player's current build code ("" if none).
            {"name": "LocalCode", "outputs": [t("Code", S)]},
            # Column header. Sub = "SCOUT · LV 25 · 2 PROMOTIONS" (upper case). Color/Icon = class colour and small
            # class image (ActorFunctionLibrary GetHeroColor / GetHeroImageSmall).
            {"name": "HeaderOf", "inputs": [obj("Player", PS)],
             "outputs": [t("Name", S), t("Sub", S), t("Color", "struct", LINEAR), obj("Icon", TEXTURE),
                         t("IsYou", B), t("IsHost", B)]},
            # Header for a pasted code: Sub = "SCOUT BUILD".
            {"name": "HeaderOfCode", "inputs": [t("Code", S)],
             "outputs": [t("Sub", S), t("Color", "struct", LINEAR), obj("Icon", TEXTURE)]},
            # Equipped perks of a player: passive ones, then active ones, then the proficiency. State: 0 = known; 1 = not available (the host does not
            # run this mod: no share actor 10 s after DB_Data spawned); 2 = not received yet (share actor not there
            # yet in the first 10 s, no data for this player/class yet, or the player's link is still young and
            # may get their build); 3 = not available: the game gave this player's perks to nobody who could pass
            # them on (no perks known is "unknown", not "no perks").
            {"name": "PerksOf", "inputs": [obj("Player", PS)],
             "outputs": [obj("Perks", PERKASSET, array=True), t("Ranks", I, array=True), t("State", I)]},
            # Another player's DB_BuildShare_v2 when it holds their build: a link with a code (on the host only a
            # code the player's own mod sent; a host of another build may fill links itself). None for the local
            # player (the save is the source), for an empty link (a player without the mod) and when there is none.
            {"name": "LinkFor", "inputs": [obj("Player", PS)], "outputs": [obj("Link", cls(LINK))]},
            # Class of a code; Valid = false for anything that is not a DB1 code of a known class with at least one
            # part whose item index is above 0.
            {"name": "ClassOfCode", "inputs": [t("Code", S)], "outputs": [obj("Class", CHARID), t("Valid", B)]},
            # One code slot (0..6, common.SLOTS). Choices: one entry per tier of the item, 0 = none, 1..3 = option,
            # -1 = an option this game does not have. UnknownOc: the code names an overclock this game does not
            # have (Overclock is then None). Both show as nothing chosen; TAKE BUILD keeps the slot's own.
            # Digits = the tier digits with spaces ("2 1 3 2 1"). Found = false when the slot is unknown (item 0).
            {"name": "DecodeSlot", "inputs": [t("Code", S), t("Slot", I)],
             "outputs": [obj("Item", ITEMID), t("Choices", I, array=True), obj("Overclock", OVERCLOCK), t("Digits", S),
                         t("Found", B), t("UnknownOc", B)]},
            # Perks of a code (its perks part), in code order. Ranks: the local player's rank of each perk, or its
            # highest rank when not owned (for the tooltips). Found = at least one perk of the code is known here.
            {"name": "PerksOfCode", "inputs": [t("Code", S)],
             "outputs": [obj("Perks", PERKASSET, array=True), t("Ranks", I, array=True), t("Found", B)]},
            # The options of one upgrade tier of an item (0-based tier), in game order.
            {"name": "TierOptions", "inputs": [obj("Item", ITEMID), t("Tier", I)],
             "outputs": [obj("Upgrades", UPGRADE, array=True)]},
            # Name ("Deepcore GK2"), category ("ASSAULT RIFLE"), outline and fill images of an item.
            {"name": "ItemVisual", "inputs": [obj("Item", ITEMID)],
             "outputs": [t("Name", TX), t("Category", TX), obj("Line", TEXTURE), obj("Fill", TEXTURE)]},
            # Tooltip texts. Body: description, then the stat lines ("+ ..." advantageous, "- ..." not).
            {"name": "ItemTip", "inputs": [obj("Item", ITEMID)],
             "outputs": [t("Title", TX), t("Category", TX), t("Body", TX), obj("Icon", TEXTURE)]},
            # ExtraTitle / Extra: the "more info" box of the game's upgrade tooltip: the upgrade category's name (upper
            # case, e.g. "TOTAL AMMO") and its CategoryDescription; empty when the category has no description.
            {"name": "UpgradeTip", "inputs": [obj("Upgrade", UPGRADE)],
             "outputs": [t("Title", TX), t("Category", TX), t("Body", TX), obj("Icon", TEXTURE), t("ExtraTitle", TX),
                         t("Extra", TX)]},
            # Overclock: Category = "CLEAN OVERCLOCK" etc.; Color = the type colour (common.OC_COLOURS); Frame = the
            # type's frame texture (may be None if it cannot be loaded).
            {"name": "OverclockTip", "inputs": [obj("Overclock", OVERCLOCK)],
             "outputs": [t("Title", TX), t("Category", TX), t("Body", TX), obj("Icon", TEXTURE),
                         t("Color", "struct", LINEAR), obj("Frame", TEXTURE)]},
            # Perk: Category = "PASSIVE PERK" / "ACTIVE PERK" / "PROFICIENCY"; Body = rank description (older game
            # versions without proficiency perks: the additional rank description, often empty) without
            # rich-text tags; Color = common.PERK_PASSIVE / PERK_ACTIVE / PERK_PROF.
            {"name": "PerkTip", "inputs": [obj("Perk", PERKASSET), t("Rank", I)],
             "outputs": [t("Title", TX), t("Category", TX), t("Body", TX), obj("Icon", TEXTURE),
                         t("Color", "struct", LINEAR)]},
            # "More info" in tooltips (E): the mod's own setting DB_Settings.MoreInfo, kept in save slot
            # common.SAVE_SLOT (loaded or created when DB_Data spawns), so it stays on after a restart. Not the game's
            # bShowUpgradeExtraDetails: that one is transient and the equipment terminal turns it off.
            {"name": "MoreInfo", "outputs": [t("On", B)]},
            # Flips the setting, saves it (SaveGameToSlot), then calls ShowExtra(On) on every registered tip.
            {"name": "ToggleMoreInfo"},
            # The key that opens and closes the window: DB_Settings.OpenKey (common.DEFAULT_KEY until changed on the
            # Mod Hub page). No settings yet: loads them first.
            {"name": "OpenKey", "outputs": [t("Key", "struct", KEY)]},
            # Sets it and saves the slot (SaveGameToSlot).
            {"name": "SetOpenKey", "inputs": [t("Key", "struct", KEY)]},
            # Every DB_Tip created registers itself here (once), so a toggle reaches tips already made and HideTips
            # can hide them all.
            {"name": "RegisterTip", "inputs": [obj("Tip", cls(TIP))]},
            # Collapses every registered tip. Called when the window closes, is destroyed or loses focus (Alt+Tab):
            # a tooltip shown at that moment would otherwise stay on screen (engine behaviour). A cell makes its tip
            # visible again on the next hover.
            {"name": "HideTips"},
            # Taking a build is allowed only on the Space Rig. Reason is shown when not Ok.
            {"name": "CanTake", "outputs": [t("Ok", B), t("Reason", S)]},
            # Loadout slots of the local player for a class: Count (at least 7; more with More Loadout Slots) and
            # the selected slot.
            {"name": "SlotInfo", "inputs": [obj("Class", CHARID)], "outputs": [t("Count", I), t("Current", I)]},
            # Writes a code into loadout slot Slot of its class, only what the player owns (items, upgrades in
            # unlocked tiers, forged overclocks); the rest keeps the slot's current choice. Perks of the code: only
            # owned ones, at most the class's free slots per type, the proficiency only when unlocked; free slots keep
            # the slot's own perks; no perks in the code = perks unchanged. EquipAfter: the slot stays selected
            # afterwards (else the previous slot is selected again). Message: one line for the user (names the perks
            # that were not taken and why). Applied / Skipped count gear parts and perks.
            {"name": "ApplyCode", "inputs": [t("Code", S), t("Slot", I), t("EquipAfter", B)],
             "outputs": [t("Applied", I), t("Skipped", I), t("Message", S)]},
        ],
    },
    SHARE: {
        # FROZEN replicated layout (see common.SHARE). Flat arrays: entry k = player Ids[k] with class Classes[k];
        # its perks are Counts[k] items of Perks/Ranks, after the items of the entries before it.
        "variables": [
            t("Ids", I, array=True, replicated=True),
            obj("Classes", CHARID, array=True, replicated=True),
            obj("Perks", PERKASSET, array=True, replicated=True),
            t("Ranks", I, array=True, replicated=True),
            t("Counts", I, array=True, replicated=True),
        ],
        "functions": [
            {"name": "Find", "inputs": [t("PlayerId", I), obj("Class", CHARID)],
             "outputs": [obj("Perks", PERKASSET, array=True), t("Ranks", I, array=True), t("Found", B)]},
        ],
    },
    LINK: {
        # FROZEN replicated layout, in this order (see common.LINK). Player: whose build (RepNotify: a client may get
        # the link before the player state). Code: a DB1 build code, empty until the player's mod sends one; its
        # perks part counts only when PerksKnown. FromPlayer: the player's own mod sent it (Server_SetCode, a reliable
        # server RPC in the event graph: data.g_link_events). This mod sets both with the code; they stay for hosts
        # of other builds that fill links from what the host sees.
        "variables": [
            obj("Player", PS, replicated=True, repnotify=True),
            t("Code", S, replicated=True),
            t("PerksKnown", B, replicated=True),
            t("FromPlayer", B, replicated=True),
        ],
        "functions": [],
    },
    TIP: {"variables": [], "functions": [
        {"name": "Set", "inputs": [t("Title", TX), t("Category", TX), t("Body", TX), t("Accent", "struct", LINEAR),
                                   obj("Icon", TEXTURE)]},
        # The "more info" box (as in the game's upgrade tooltip): a dark inner panel with ExtraTitle (Carbon, upper
        # case) and Extra (body font), and a footer "MORE INFO [E]" / "LESS INFO [E]". Empty Extra: no box, no footer.
        {"name": "SetExtra", "inputs": [t("ExtraTitle", TX), t("Extra", TX)]},
        # Shows (On) or hides the box; the footer text follows.
        {"name": "ShowExtra", "inputs": [t("On", B)]}]},
    CELL: {"variables": [obj("Data", cls(DATA))], "functions": [
        # Upgrade None = empty cell (dim, no tooltip). Tooltip (DB_Tip) is created on first hover only.
        {"name": "Set", "inputs": [obj("Upgrade", UPGRADE), t("Selected", B)]}]},
    PERK: {"variables": [obj("Data", cls(DATA))], "functions": [
        # Perk None = empty slot.
        {"name": "Set", "inputs": [obj("Perk", PERKASSET), t("Rank", I)]}]},
    CARD: {"variables": [obj("Data", cls(DATA))], "functions": [
        # UnknownOc (DecodeSlot): the overclock tile says UNKNOWN OVERCLOCK instead of NO OVERCLOCK.
        {"name": "Show", "inputs": [obj("Item", ITEMID), t("Choices", I, array=True), obj("Overclock", OVERCLOCK),
                                    t("Digits", S), t("UnknownOc", B)]}]},
    GEAR: {"variables": [obj("Data", cls(DATA))], "functions": [
        {"name": "Show", "inputs": [t("Label", S), obj("Item", ITEMID), t("Choices", I, array=True)]}]},
    COLUMN: {"variables": [obj("Window", cls(WINDOW)), obj("Data", cls(DATA)), t("Code", S)], "functions": [
        # Shows a player (header, build, perks, buttons). Cheap when nothing changed since the last call.
        {"name": "ShowPlayer", "inputs": [obj("Player", PS)]},
        # Shows a pasted code (its perks from the code, no buttons). Title = the header name line.
        {"name": "ShowCode", "inputs": [t("NewCode", S), t("Title", S)]},
        # Hides the content and keeps the column's size.
        {"name": "Clear"},
        # Compact (On): no button row (TAKE BUILD / COPY CODE) and its gap: the column is 418 x 940 instead of 990.
        # Used by DB_Select, where there is no Window (Window stays None: nothing may call it then).
        {"name": "SetCompact", "inputs": [t("On", B)]}]},
    CHIP: {"variables": [obj("Window", cls(WINDOW)), t("Index", I)], "functions": [
        {"name": "Set", "inputs": [t("PlayerName", S), t("Color", "struct", LINEAR), t("Selected", B), t("IsYou", B)]}]},
    SLOTBTN: {"variables": [obj("Dialog", cls(TAKE)), t("Index", I)], "functions": [
        {"name": "Set", "inputs": [t("Label", S), t("Selected", B), t("Current", B)]}]},
    TAKE: {"variables": [obj("Window", cls(WINDOW)), obj("Data", cls(DATA))], "functions": [
        # Title: whose build it is (the player name, or "PASTED BUILD").
        {"name": "Show", "inputs": [t("NewCode", S), t("Title", S)]},
        {"name": "PickSlot", "inputs": [t("SlotIndex", I)]}]},
    WINDOW: {"variables": [obj("Data", cls(DATA))], "functions": [
        # Called by DB_Mod once after the window is opened and Data is set.
        {"name": "Open"},
        # From a column's TAKE BUILD button (Title = the player name) and the code tab (Title = "PASTED BUILD").
        {"name": "OpenTake", "inputs": [t("NewCode", S), t("Title", S)]},
        # From a roster chip: show the page with this player (index in Data.GetPlayers()).
        {"name": "SelectPlayer", "inputs": [t("PlayerIndex", I)]},
        # From the take dialog when it closes.
        {"name": "CloseTake"}]},
    SETTINGS: {"variables": [t("MoreInfo", B, default="false"), t("OpenKey", "struct", KEY, default=DEFAULT_KEY)],
               "functions": []},
    HUBPAGE: {"variables": [], "functions": []},
    HUBMOD: {"variables": [], "functions": []},
    SELECT: {"variables": [], "functions": []},
    CORE: {"variables": [], "functions": []},
    INIT_SPACERIG: {"variables": [], "functions": []},
    INIT_CAVE: {"variables": [], "functions": []},
}
