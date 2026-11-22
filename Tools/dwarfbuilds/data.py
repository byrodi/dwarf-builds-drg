"""Data module of Dwarf Builds: DB_Data, DB_Settings, Net/DB_PerkShare_v1 and Net/DB_BuildShare_v2.

DB_Data: all data logic. DB_Mod spawns it once per world; widgets call its functions. No Tick. It shares the local
player's build when it changes (game events, see DB_BuildShare_v2 below); one 10 s timer (ShareCheck) is the safety
net behind those events and works nothing out again while its inputs are the same.
BeginPlay loads the mod's settings (DB_Settings, save slot SAVE_SLOT) and starts async loads of the hexagon and
overclock frame textures (no hitch). It also keeps the list of tooltips (RegisterTip) for the "more info" toggle
and HideTips.
DB_Settings: the mod's SaveGame. Only its public MoreInfo and OpenKey (contract); nothing is added here.
DB_PerkShare_v1: replicated perk table. Spawned on the server only; every 3 s it collects the equipped perks of
all players, so clients can show them (the game replicates no perks to clients). Solo: no work. Kept exactly as
0.1.0 shipped it, for clients on 0.1.0.
DB_BuildShare_v2: one replicated actor per player ("link"), spawned by the host's DB_Data (HostSync) and owned by
that player's controller. The player's own mod sends its full build code through it (Server_SetCode) once, and
again only when the build changes (SendOwn); the host replicates them all. So every client gets the build and
perks of every player who runs the mod, which the game alone does not give it. A player without the mod has an
empty link: readers then use the game's own replicated data and the 0.1.0 perk table, as before. A machine without
the class (0.1.0, or no mod) drops the actor's channel and plays on. Solo: none are made.
Nothing here runs on a schedule except ShareCheck. What calls what:
  SendOwn  <- the local player's own link arrived (LinkChanged), the game's events for a changed loadout, perks or
              class, the last game window closed (every loadout change is made in one), the class selection
              ended, ApplyCode, ShareCheck. The code is worked out again only when the save's loadout or perks
              differ from the last time (SaveCode and CodeOf remember their inputs).
  HostSync <- a player joined or left (the host), ShareCheck.

BPForge has no local variables: each function keeps its temporaries in private member variables named
<Function>_<Name>. Pure nodes run again at every use (also inside loops), so arrays that loops read are stored in a
variable first. Object inputs are checked before native code gets them.
"""
from dwarfbuilds.common import DEFAULT_KEY, KEY  # noqa: E402
from dwarfbuilds.common import (ACTOR, CHARID, CHARSAVE, CODE_VERSION, DATA, FSD, GAMESTATE, GEARCOMP, GFL, GS, GUID,
                               INVLIST, ITEMDATA, ITEMID, ITEMLOADOUT, KARR, KMAP, KML, KSL, KSTR, KTXT, LFL, LINEAR,
                               LINK,
                               LOADOUTCOPY, OC_COLOURS, ORANGE, OVERCLOCK, PC, PERK_ACTIVE, PERK_PASSIVE, PERK_PROF,
                               PERKASSET, PERKITEM, PFL, PROFASSET, PS, SAVE_SLOT, SAVEGAME, SELECTION, SETTINGS, SGSC,
                               SHARE, SLOT_LIST, SLOTS, TEX_HEX_BG, TEX_HEX_OUTLINE, TEX_OC_FRAME, TEXTURE, TIP, UMG,
                               UPGRADE, UPGRADELOADOUT, UPGRADETIER, AFL, WINDOWMANAGER, Graph, cls, colour,
                               perk_names, t)

SAVABLE = FSD + "SavableDataAsset"
GAMEDATA = FSD + "GameData"
CHARSETTINGS = FSD + "CharacterSettings"
ITEM = FSD + "Item"
PLAYERCHAR = FSD + "PlayerCharacter"
UPGCAT = FSD + "ItemUpgradeCategory"
SCHEMCAT = FSD + "SchematicCategory"
SCHEMLIB = FSD + "SchematicBlueprintLibrary"
STATTEXT = FSD + "ItemUpgradeStatText"
PROGRESS = FSD + "CharacterProgress"
OCBANK = FSD + "OverclockBank"
STATUS = FSD + "EItemUpgradeStatus"
PLAYERSTATE = "/Script/Engine.PlayerState"
CONTROLLER = "/Script/Engine.Controller"
GSBASE = "/Script/Engine.GameStateBase"
KGUID = "/Script/Engine.KismetGuidLibrary"
OBJECT = "/Script/CoreUObject.Object"
SHARE_C = cls(SHARE)
LINK_C = cls(LINK)
DATA_C = cls(DATA)
GAMEINSTANCE = FSD + "FSDGameInstance"
SHARE_SECONDS = "10.0"  # ShareCheck: the safety net behind the events
EVENT_DELAY = "0.3"     # from a game event to SendOwn / HostSync (share_events)
LINK_YOUNG = "6.0"      # a link this young may still get its player's code: "waiting", not "not available"
CODE_MAX = "600"        # Server_SetCode ignores anything longer (a build code is under 100 characters)
CODE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:-."   # every character of a build code (contract)
TIP_C = cls(TIP)
SETTINGS_C = cls(SETTINGS)

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # loadout slot labels, as the game and More Loadout Slots show them
DOT = " · "
LAST_SLOT = str(len(SLOTS) - 1)
PERKS_PART = str(2 + len(SLOTS))   # index of the perks part in a code (after version, class and the seven slots)
KINDS = ("Passive", "Active", "Proficiency")   # EPerkUsageType; PerkKind 0, 1, 2
S, I, B, TX = "string", "int", "bool", "text"


def raw(value):
    return value[1:] if value.startswith("@") else value


class D(Graph):
    """Graph with shortcuts. A value is "@node.pin" (a link) or a literal pin default, as in Graph.call.
    Helpers that make a pure node return its output as such a value."""

    def val(self, fn, out="ReturnValue", **pins):
        nid = self.uid("f")
        self.call(nid, fn, **pins)
        return "@%s.%s" % (nid, out)

    def do(self, nid, fn, **pins):
        self.call(nid, fn, **pins)
        return nid

    def var(self, name, owner=None, target=None):
        nid = self.uid("g")
        self.node(nid, "get", var=name, **({"class": owner} if owner else {}))
        if target:
            self.link(raw(target), nid + ".self")
        return "@%s.%s" % (nid, name)

    def put(self, nid, name, value=None):
        """Sets an own variable; no value sets None / empty."""
        self.node(nid, "set", var=name)
        self.pins(nid, {name: value})
        return nid

    def out(self, name, value):
        self.pins("result", {name: value})

    def br(self, nid, cond):
        self.node(nid, "branch")
        self.pins(nid, {"Condition": cond})
        return nid

    def each(self, nid, array, brk=False):
        """ForEachLoop (pins Exec, LoopBody, Completed; with brk also Break). Returns element and index."""
        self.node(nid, "macro", name="ForEachLoopWithBreak" if brk else "ForEachLoop")
        self.pins(nid, {"Array": array})
        return "@%s.Array Element" % nid, "@%s.Array Index" % nid

    def fori(self, nid, first, last):
        """ForLoop (pins execute, LoopBody, Completed). Returns the index."""
        self.node(nid, "macro", name="ForLoop")
        self.pins(nid, {"FirstIndex": first, "LastIndex": last})
        return "@%s.Index" % nid

    def brk(self, struct, src):
        nid = self.uid("b")
        self.node(nid, "breakstruct", struct=struct)
        self.pins(nid, {struct.rsplit(".", 1)[1]: src})
        return lambda member: "@%s.%s" % (nid, member)

    def make(self, nid, struct, **members):
        self.node(nid, "makestruct", struct=struct)
        self.pins(nid, members)
        return "@%s.%s" % (nid, struct.rsplit(".", 1)[1])

    def cast_(self, nid, target_class, obj):
        self.node(nid, "cast", **{"class": target_class})
        self.link(raw(obj), nid + ".Object")
        return "@%s.$cast" % nid

    # pure helpers
    def valid(self, obj):
        return self.val(KSL + ":IsValid", Object=obj)

    def valid_class(self, klass):
        return self.val(KSL + ":IsValidClass", Class=klass)

    def and_(self, a, b):
        return self.val(KML + ":BooleanAND", A=a, B=b)

    def not_(self, a):
        return self.val(KML + ":Not_PreBool", A=a)

    def cmp(self, op, a, b):
        return self.val(KML + ":%s_IntInt" % op, A=a, B=b)

    def in_range(self, value, first, last):
        return self.and_(self.cmp("GreaterEqual", value, first), self.cmp("LessEqual", value, last))

    def add(self, a, b):
        return self.val(KML + ":Add_IntInt", A=a, B=b)

    def sub(self, a, b):
        return self.val(KML + ":Subtract_IntInt", A=a, B=b)

    def max_(self, a, b):
        return self.val(KML + ":Max", A=a, B=b)

    def same(self, a, b):
        return self.val(KML + ":EqualEqual_ObjectObject", A=a, B=b)

    def pick(self, a, b, pick_a):
        return self.val(KML + ":SelectString", A=a, B=b, bPickA=pick_a)

    def itos(self, value):
        return self.val(KSTR + ":Conv_IntToString", InInt=value)

    def stoi(self, value):
        return self.val(KSTR + ":Conv_StringToInt", InString=value)

    def ttos(self, value):
        return self.val(KTXT + ":Conv_TextToString", InText=value)

    def stot(self, value):
        return self.val(KTXT + ":Conv_StringToText", InString=value)

    def upper_text(self, value):
        return self.val(KTXT + ":TextToUpper", InText=value)

    def streq(self, a, b):
        return self.val(KSTR + ":EqualEqual_StrStr", A=a, B=b)

    def strlen(self, value):
        return self.val(KSTR + ":Len", S=value)

    def cat(self, *parts):
        out = parts[0]
        for part in parts[1:]:
            out = self.val(KSTR + ":Concat_StrStr", A=out, B=part)
        return out

    def length(self, array):
        return self.val(KARR + ":Array_Length", TargetArray=array)

    def at(self, array, index):
        return self.val(KARR + ":Array_Get", out="Item", TargetArray=array, Index=index)

    def guid(self, asset):
        """SavegameID of an item, upgrade or class (read as the property, as the original Build Inspector does)."""
        return self.var("SavegameID", SAVABLE, asset)

    def owned(self, status):
        """EItemUpgradeStatus is Owned or Equipped."""
        nid = self.uid("own")
        self.node(nid, "select", index=STATUS, type={"type": "bool"})
        self.pins(nid, {"Index": status, "Owned": "true", "Equipped": "true"})
        return "@%s.ReturnValue" % nid

    # impure helpers
    def clear(self, nid, array):
        return self.do(nid, KARR + ":Array_Clear", TargetArray=array)

    def append(self, nid, array, item):
        return self.do(nid, KARR + ":Array_Add", TargetArray=array, NewItem=item)

    def incr(self, nid, name):
        return self.put(nid, name, self.add(self.var(name), "1"))

    def ends(self, pins, step):
        for pin in pins:
            self.flow(pin, step)


def obj(name, path, **extra):
    return t(name, "object", path, **extra)


# ============================================================================ DB_Data: small private helpers

def g_local_ps():
    """The local player's FSDPlayerState, or None."""
    g = D()
    pc = g.val(GS + ":GetPlayerController", PlayerIndex="0")
    g.br("brPc", g.valid(pc))
    g.put("setPs", "LocalPS_PS", g.cast_("asPs", PS, g.var("PlayerState", CONTROLLER, pc)))
    g.put("noPs", "LocalPS_PS")
    g.flow("entry", "brPc", "asPs", "setPs", "result")
    g.flow("brPc.else", "noPs", "result")
    g.flow("asPs.CastFailed", "noPs")
    g.out("PS", g.var("LocalPS_PS"))
    return g.data()


def g_class_letter():
    """Letter "S" and name "SCOUT" of a class, from its asset name (ScoutID)."""
    g = D()
    name = g.val(KSL + ":GetObjectName", Object="@entry.Class")
    first = g.val(KSTR + ":GetSubstring", SourceString=name, StartIndex="0", Length="1")
    g.out("Letter", g.val(KSTR + ":ToUpper", SourceString=first))
    chop = g.val(KSTR + ":LeftChop", SourceString=name, Count="2")
    ends = g.val(KSTR + ":EndsWith", SourceString=name, InSuffix="ID")
    g.out("Name", g.val(KSTR + ":ToUpper", SourceString=g.pick(chop, name, ends)))
    g.flow("entry", "result")
    return g.data()


def g_slot_items():
    """The class's items for a code slot (inventory list order) and their GUIDs (zero GUID for a missing item)."""
    g = D()
    P = "SlotItems_"
    g.clear("clearItems", g.var(P + "Items"))
    g.clear("clearIds", g.var(P + "Ids"))
    g.br("brClass", g.valid("@entry.Class"))
    g.put("keepList", P + "List", g.val(AFL + ":GetHeroInventoryList", characterID="@entry.Class"))
    g.br("brList", g.valid(g.var(P + "List")))
    g.node("sw", "switchint", n=len(SLOTS), start=0, default=True)
    g.pins("sw", {"Selection": "@entry.Slot"})
    for k, slot in enumerate(SLOTS):
        g.put("set%d" % k, P + "Items", g.var(SLOT_LIST[slot], INVLIST, g.var(P + "List")))
        g.flow("sw.%d" % k, "set%d" % k, "ids.Exec")
    item, _ = g.each("ids", g.var(P + "Items"))
    g.br("brItem", g.valid(item))
    g.append("addId", g.var(P + "Ids"), g.guid(item))
    g.append("addNone", g.var(P + "Ids"), g.var("ZeroGuid"))
    g.flow("entry", "clearItems", "clearIds", "brClass", "keepList", "brList", "sw")
    g.flow("ids.LoopBody", "brItem", "addId")
    g.flow("brItem.else", "addNone")
    g.ends(["brClass.else", "brList.else", "sw.Default", "ids.Completed"], "result")
    g.out("Items", g.var(P + "Items"))
    g.out("Ids", g.var(P + "Ids"))
    return g.data()


def g_gear_of():
    """UpgradableGearComponent of an item class; falls back to the component of the item's default object."""
    g = D()
    P = "GearOf_"
    g.put("clear", P + "Gear")
    g.br("brItem", g.valid("@entry.Item"))
    g.put("keepClass", P + "Class", g.val(ITEMID + ":GetItemClass", target="@entry.Item"))
    g.br("brClass", g.valid_class(g.var(P + "Class")))
    g.do("comp", AFL + ":GetComponentFromClass", Actor=g.var(P + "Class"), ComponentClass=GEARCOMP)
    g.put("setGear", P + "Gear", g.cast_("asGear", GEARCOMP, "@comp.ReturnValue"))
    item = g.val(ITEMID + ":GetItem", target="@entry.Item")
    g.br("brDefault", g.valid(item))
    g.put("setDefault", P + "Gear", g.var("UpgradableItem", ITEM, item))
    g.flow("entry", "clear", "brItem", "keepClass", "brClass", "comp", "asGear", "setGear", "result")
    g.flow("asGear.CastFailed", "brDefault", "setDefault", "result")
    g.flow("brClass.else", "brDefault")
    g.ends(["brDefault.else", "brItem.else"], "result")
    g.out("Gear", g.var(P + "Gear"))
    return g.data()


def g_overclocks_of():
    """The item's overclocks: keys of its OverclockBank (persistent data, the same order on every machine)."""
    g = D()
    P = "OverclocksOf_"
    g.clear("clear", g.var(P + "List"))
    g.do("gear", "GearOf", Item="@entry.Item")
    g.put("keepGear", P + "Gear", "@gear.Gear")
    g.br("brGear", g.valid(g.var(P + "Gear")))
    g.put("keepBank", P + "Bank", g.var("OverclockBank", GEARCOMP, g.var(P + "Gear")))
    g.br("brBank", g.valid(g.var(P + "Bank")))
    g.do("keys", KMAP + ":Map_Keys", TargetMap=g.var("Overclocks", OCBANK, g.var(P + "Bank")))
    g.put("setList", P + "List", "@keys.Keys")
    g.flow("entry", "clear", "gear", "keepGear", "brGear", "keepBank", "brBank", "keys", "setList", "result")
    g.ends(["brGear.else", "brBank.else"], "result")
    g.out("Overclocks", g.var(P + "List"))
    return g.data()


# ============================================================================ DB_Data: build code

def g_encode_part():
    """One code part "<item>-<tiers>-<oc>" from an item, its 1-based index and its upgrade selection."""
    g = D()
    P = "EncodePart_"
    g.put("digits0", P + "Digits", "")
    g.put("oc0", P + "OC", "0")
    g.br("brItem", g.valid("@entry.Item"))
    g.put("keepClass", P + "Class", g.val(ITEMID + ":GetItemClass", target="@entry.Item"))
    g.br("brClass", g.valid_class(g.var(P + "Class")))
    g.put("keepTiers", P + "Tiers", g.val(GEARCOMP + ":GetItemUpgradeTiers", itemClass=g.var(P + "Class")))
    sel = g.brk(SELECTION, "@entry.Sel")
    g.put("keepEquipped", P + "Equipped", sel("EquippedUpgrades"))
    tier, _ = g.each("tiers", g.var(P + "Tiers"))
    g.put("digit0", P + "Digit", "0")
    g.put("keepUps", P + "Ups", g.brk(UPGRADETIER, tier)("upgrades"))
    up, index = g.each("ups", g.var(P + "Ups"))
    g.br("brUp", g.valid(up))
    has = g.val(KARR + ":Array_Contains", TargetArray=g.var(P + "Equipped"), ItemToFind=g.guid(up))
    g.br("brHas", g.and_(has, g.cmp("EqualEqual", g.var(P + "Digit"), "0")))
    g.put("setDigit", P + "Digit", g.add(index, "1"))
    g.put("addDigit", P + "Digits", g.cat(g.var(P + "Digits"), g.itos(g.var(P + "Digit"))))
    g.flow("entry", "digits0", "oc0", "brItem", "keepClass", "brClass", "keepTiers", "keepEquipped", "tiers.Exec")
    g.flow("tiers.LoopBody", "digit0", "keepUps", "ups.Exec")
    g.flow("ups.LoopBody", "brUp", "brHas", "setDigit")
    g.flow("ups.Completed", "addDigit")
    # Overclock: 1-based position in the item's overclock list.
    equipped_oc = sel("EquippedOverclock")
    g.br("brOc", g.val(KGUID + ":IsValid_Guid", InGuid=equipped_oc))
    g.do("ocs", "OverclocksOf", Item="@entry.Item")
    g.put("keepOcs", P + "OCs", "@ocs.Overclocks")
    oc, oc_index = g.each("ocList", g.var(P + "OCs"), brk=True)
    g.br("brOcValid", g.valid(oc))
    g.br("brOcSame", g.val(KGUID + ":EqualEqual_GuidGuid", A=g.guid(oc), B=equipped_oc))
    g.put("setOc", P + "OC", g.add(oc_index, "1"))
    g.flow("tiers.Completed", "brOc", "ocs", "keepOcs", "ocList.Exec")
    g.flow("ocList.LoopBody", "brOcValid", "brOcSame", "setOc", "ocList.Break")
    g.put("final", P + "Part", g.cat(g.itos("@entry.Index"), "-", g.var(P + "Digits"), "-", g.itos(g.var(P + "OC"))))
    g.ends(["brItem.else", "brClass.else", "brOc.else", "ocList.Completed"], "final")
    g.flow("final", "result")
    g.out("Part", g.var(P + "Part"))
    return g.data()


def g_save_code():
    """Code of the local player's current loadout of a class, from the save. The code depends only on the class,
    the loadout's items and its upgrade selections: while those are what they were at the last call, the last code
    is returned (about 25 nodes instead of 2000)."""
    g = D()
    P = "SaveCode_"
    g.do("current", LFL + ":GetCurrentLoadout", PlayerId="@entry.Class")
    g.put("keepLoadout", P + "Loadout", "@current.ReturnValue")
    lc = g.brk(LOADOUTCOPY, g.var(P + "Loadout"))
    il = g.brk(ITEMLOADOUT, lc("ItemLoadout"))
    g.put("keepMap", P + "Map", g.brk(UPGRADELOADOUT, lc("UpgradeLoadout"))("Loadout"))
    g.node("guids", "makearray", n=len(SLOTS))
    g.pins("guids", {"[%d]" % k: il(name) for k, name in enumerate(SLOTS)})
    g.put("keepGuids", P + "Guids", "@guids.Array")
    g.do("letter", "ClassLetter", Class="@entry.Class")
    g.put("head", P + "Code", g.cat(CODE_VERSION + ":", "@letter.Letter"))
    slot = g.fori("slots", "0", LAST_SLOT)
    g.do("items", "SlotItems", Class="@entry.Class", Slot=slot)
    g.put("keepItems", P + "Items", "@items.Items")
    g.put("keepIds", P + "Ids", "@items.Ids")
    guid = g.at(g.var(P + "Guids"), slot)
    g.put("keepFound", P + "Found", g.val(KARR + ":Array_Find", TargetArray=g.var(P + "Ids"), ItemToFind=guid))
    g.br("brFound", g.cmp("GreaterEqual", g.var(P + "Found"), "0"))
    g.put("setItem", P + "Item", g.at(g.var(P + "Items"), g.var(P + "Found")))
    g.put("noItem", P + "Item")
    selection = g.val(KMAP + ":Map_Find", out="Value", TargetMap=g.var(P + "Map"), Key=guid)
    g.do("part", "EncodePart", Item=g.var(P + "Item"), Index=g.add(g.var(P + "Found"), "1"), Sel=selection)
    g.put("append", P + "Code", g.cat(g.var(P + "Code"), ":", "@part.Part"))
    g.do("keys", KMAP + ":Map_Keys", TargetMap=g.var(P + "Map"))
    g.do("vals", KMAP + ":Map_Values", TargetMap=g.var(P + "Map"))

    def identical(a, b):
        return g.val(KARR + ":Array_Identical", ArrayA=a, ArrayB=b)

    same = g.and_(g.and_(g.same("@entry.Class", g.var(P + "LastClass")),
                         identical(g.var(P + "Guids"), g.var(P + "LastGuids"))),
                  g.and_(identical("@keys.Keys", g.var(P + "LastKeys")),
                         identical("@vals.Values", g.var(P + "LastVals"))))
    g.br("brSame", g.and_(same, g.cmp("Greater", g.strlen(g.var(P + "Code")), "0")))
    g.put("lastClass", P + "LastClass", "@entry.Class")
    g.put("lastGuids", P + "LastGuids", g.var(P + "Guids"))
    g.put("lastKeys", P + "LastKeys", "@keys.Keys")
    g.put("lastVals", P + "LastVals", "@vals.Values")
    g.flow("entry", "current", "keepLoadout", "keepMap", "keepGuids", "keys", "vals", "brSame", "result")
    g.flow("brSame.else", "lastClass", "lastGuids", "lastKeys", "lastVals", "letter", "head", "slots")
    g.flow("slots.LoopBody", "items", "keepItems", "keepIds", "keepFound", "brFound", "setItem", "part", "append")
    g.flow("brFound.else", "noItem", "part")
    g.flow("slots.Completed", "result")
    g.out("Code", g.var(P + "Code"))
    return g.data()


def g_remote_code():
    """Code of another player: per slot, the first replicated ItemUpgradeSelections entry whose WeaponID is an
    item of that slot (as the original Build Inspector). "" until some selection has replicated."""
    g = D()
    P = "RemoteCode_"
    g.clear("clearSels", g.var(P + "Sels"))
    g.put("any0", P + "Any", "false")
    comp = g.var("SaveGameStateComponent", PS, "@entry.Player")
    g.br("brComp", g.valid(comp))
    g.put("keepSels", P + "Sels", g.var("ItemUpgradeSelections", SGSC, comp))
    g.do("letter", "ClassLetter", Class="@entry.Class")
    g.put("head", P + "Code", g.cat(CODE_VERSION + ":", "@letter.Letter"))
    slot = g.fori("slots", "0", LAST_SLOT)
    g.do("items", "SlotItems", Class="@entry.Class", Slot=slot)
    g.put("keepItems", P + "Items", "@items.Items")
    g.put("keepIds", P + "Ids", "@items.Ids")
    g.put("found0", P + "Found", "-1")
    g.put("item0", P + "Item")
    g.put("sel0", P + "Sel", g.var("ZeroSel"))
    sel, _ = g.each("sels", g.var(P + "Sels"), brk=True)
    weapon = g.brk(SELECTION, sel)("WeaponID")
    g.put("keepFound", P + "Found", g.val(KARR + ":Array_Find", TargetArray=g.var(P + "Ids"), ItemToFind=weapon))
    g.br("brHit", g.cmp("GreaterEqual", g.var(P + "Found"), "0"))
    g.put("setItem", P + "Item", g.at(g.var(P + "Items"), g.var(P + "Found")))
    g.put("setSel", P + "Sel", sel)
    g.put("setAny", P + "Any", "true")
    g.do("part", "EncodePart", Item=g.var(P + "Item"), Index=g.add(g.var(P + "Found"), "1"), Sel=g.var(P + "Sel"))
    g.put("append", P + "Code", g.cat(g.var(P + "Code"), ":", "@part.Part"))
    # No component or no slot found: the data has not replicated yet.
    g.br("brAny", g.var(P + "Any"))
    g.put("empty", P + "Code", "")
    g.flow("entry", "clearSels", "any0", "brComp", "keepSels", "letter", "head", "slots")
    g.flow("brComp.else", "empty", "result")
    g.flow("slots.LoopBody", "items", "keepItems", "keepIds", "found0", "item0", "sel0", "sels.Exec")
    g.flow("sels.LoopBody", "keepFound", "brHit", "setItem", "setSel", "setAny", "sels.Break")
    g.flow("sels.Completed", "part", "append")
    g.flow("slots.Completed", "brAny", "result")
    g.flow("brAny.else", "empty")
    g.out("Code", g.var(P + "Code"))
    return g.data()


def g_code_of():
    """Another player with a link (LinkFor): the link's code as it is. Else gear parts (local player: the save;
    others: replicated selections), then the perks part from PerksOf (empty when the perks are not known).
    The local player's full code is remembered: while the gear parts and the save's equipped perks are what they
    were, it is returned without PerksOf and PerksPart."""
    g = D()
    P = "CodeOf_"
    g.put("code0", P + "Code", "")
    g.do("link", "LinkFor", Player="@entry.Player")
    g.br("brLink", g.valid("@link.Link"))
    g.put("fromLink", P + "Code", g.var("Code", LINK_C, "@link.Link"))
    g.br("brPlayer", g.valid("@entry.Player"))
    g.put("keepClass", P + "Class", g.val(PS + ":GetSelectedCharacterID", target="@entry.Player"))
    g.br("brClass", g.valid(g.var(P + "Class")))
    g.do("local", "LocalPS")
    g.br("brLocal", g.same("@entry.Player", "@local.PS"))
    g.do("save", "SaveCode", Class=g.var(P + "Class"))
    g.put("setSave", P + "Code", "@save.Code")
    g.put("localOn", P + "Local", "true")
    g.put("keepNow", P + "Now", g.val(PFL + ":GetCharacterEquippedPerks", characterID=g.var(P + "Class")))
    known = g.and_(g.val(KARR + ":Array_Identical", ArrayA=g.var(P + "Now"), ArrayB=g.var(P + "LastPerks")),
                   g.and_(g.streq(g.var(P + "Code"), g.var(P + "LastGear")),
                          g.cmp("Greater", g.strlen(g.var(P + "LastFull")), "0")))
    g.br("brMemo", known)
    g.put("useMemo", P + "Code", g.var(P + "LastFull"))
    g.do("remote", "RemoteCode", Player="@entry.Player", Class=g.var(P + "Class"))
    g.put("setRemote", P + "Code", "@remote.Code")
    g.put("localOff", P + "Local", "false")
    g.flow("entry", "code0", "link", "brLink", "fromLink", "result")
    g.flow("brLink.else", "brPlayer", "keepClass", "brClass", "local", "brLocal", "save", "setSave", "localOn",
           "keepNow", "brMemo", "useMemo", "result")
    g.flow("brMemo.else", "brGear")
    g.flow("brLocal.else", "remote", "setRemote", "localOff", "brGear")
    g.ends(["brPlayer.else", "brClass.else"], "result")
    # Perks part ("" until the gear is known: no code at all then).
    g.br("brGear", g.cmp("Greater", g.strlen(g.var(P + "Code")), "0"))
    g.put("keepGear", P + "Gear", g.var(P + "Code"))
    g.do("perks", "PerksOf", Player="@entry.Player")
    g.put("keepPerks", P + "Perks", "@perks.Perks")
    g.br("brKnown", g.cmp("EqualEqual", "@perks.State", "0"))
    g.do("part", "PerksPart", Perks=g.var(P + "Perks"))
    g.put("addPart", P + "Code", g.cat(g.var(P + "Code"), ":", "@part.Part"))
    g.put("addNone", P + "Code", g.cat(g.var(P + "Code"), ":"))
    g.br("brStore", g.var(P + "Local"))
    g.put("lastPerks", P + "LastPerks", g.var(P + "Now"))
    g.put("lastGear", P + "LastGear", g.var(P + "Gear"))
    g.put("lastFull", P + "LastFull", g.var(P + "Code"))
    g.flow("brGear", "keepGear", "perks", "keepPerks", "brKnown", "part", "addPart", "brStore")
    g.flow("brKnown.else", "addNone", "brStore")
    g.flow("brStore", "lastPerks", "lastGear", "lastFull", "result")
    g.flow("brStore.else", "result")
    g.flow("brGear.else", "result")
    g.out("Code", g.var(P + "Code"))
    return g.data()


def g_local_code():
    g = D()
    g.do("local", "LocalPS")
    g.br("brPs", g.valid("@local.PS"))
    g.do("code", "CodeOf", Player="@local.PS")
    g.put("set", "LocalCode_Code", "@code.Code")
    g.put("none", "LocalCode_Code", "")
    g.flow("entry", "local", "brPs", "code", "set", "result")
    g.flow("brPs.else", "none", "result")
    g.out("Code", g.var("LocalCode_Code"))
    return g.data()


def g_parse_code():
    """Splits a code into ParseCode_Parts (padded to 10: version, class, seven slots, perks) and finds its class.
    Valid: DB1, a known class and at least one part with item index above 0. A valid code is parsed once (cached)."""
    g = D()
    P = "ParseCode_"
    g.br("brSame", g.and_(g.var(P + "Valid"), g.streq("@entry.Code", g.var(P + "Code"))))
    g.put("keepCode", P + "Code", "@entry.Code")
    trimmed = g.val(KSTR + ":TrimTrailing", SourceString=g.val(KSTR + ":Trim", SourceString="@entry.Code"))
    clean = g.val(KSTR + ":ToUpper", SourceString=trimmed)
    g.put("keepParts", P + "Parts",
          g.val(KSTR + ":ParseIntoArray", SourceString=clean, Delimiter=":", CullEmptyStrings="false"))
    g.put("valid0", P + "Valid", "false")
    g.put("class0", P + "Class")
    # Missing parts read as empty: version, class, the seven slots and the perks part always exist after this.
    g.do("pad", KARR + ":Array_Resize", TargetArray=g.var(P + "Parts"),
         Size=g.max_(g.length(g.var(P + "Parts")), str(3 + len(SLOTS))))
    g.br("brVersion", g.streq(g.at(g.var(P + "Parts"), "0"), CODE_VERSION))
    # Some part names an item: Conv_StringToInt reads the leading digits of "<item>-<tiers>-<oc>".
    any_item = None
    for k in range(len(SLOTS)):
        has = g.cmp("Greater", g.stoi(g.at(g.var(P + "Parts"), str(2 + k))), "0")
        any_item = has if any_item is None else g.val(KML + ":BooleanOR", A=any_item, B=has)
    g.br("brAny", any_item)
    g.put("keepData", P + "Data", g.val(GFL + ":GetFSDGameData"))
    g.br("brData", g.valid(g.var(P + "Data")))
    g.put("keepSettings", P + "Settings", g.var("CharacterSettings", GAMEDATA, g.var(P + "Data")))
    g.br("brSettings", g.valid(g.var(P + "Settings")))
    g.put("keepIds", P + "IDs", g.var("PlayerCharacterIDs", CHARSETTINGS, g.var(P + "Settings")))
    cid, _ = g.each("ids", g.var(P + "IDs"), brk=True)
    g.br("brId", g.valid(cid))
    g.do("letter", "ClassLetter", Class=cid)
    g.br("brLetter", g.streq("@letter.Letter", g.at(g.var(P + "Parts"), "1")))
    g.put("setClass", P + "Class", cid)
    g.put("setValid", P + "Valid", "true")
    g.flow("entry", "brSame")
    g.link("brSame.then", "result.execute")
    g.flow("brSame.else", "keepCode", "keepParts", "valid0", "class0", "pad", "brVersion", "brAny", "keepData",
           "brData", "keepSettings", "brSettings", "keepIds", "ids.Exec")
    g.flow("ids.LoopBody", "brId", "letter", "brLetter", "setClass", "setValid", "ids.Break")
    g.ends(["brVersion.else", "brAny.else", "brData.else", "brSettings.else", "ids.Completed"], "result")
    g.out("Valid", g.var(P + "Valid"))
    return g.data()


def g_class_of_code():
    g = D()
    g.do("parse", "ParseCode", Code="@entry.Code")
    g.flow("entry", "parse", "result")
    g.out("Class", g.var("ParseCode_Class"))
    g.out("Valid", "@parse.Valid")
    return g.data()


def g_decode_slot():
    g = D()
    P = "DecodeSlot_"
    g.put("item0", P + "Item")
    g.put("oc0", P + "Overclock")
    g.put("digits0", P + "Digits", "")
    g.put("found0", P + "Found", "false")
    g.clear("choices0", g.var(P + "Choices"))
    g.do("parse", "ParseCode", Code="@entry.Code")
    g.br("brValid", "@parse.Valid")
    g.br("brSlot", g.in_range("@entry.Slot", "0", LAST_SLOT))
    part = g.at(g.var("ParseCode_Parts"), g.add("@entry.Slot", "2"))
    g.put("keepSub", P + "Sub", g.val(KSTR + ":ParseIntoArray", SourceString=part, Delimiter="-", CullEmptyStrings="false"))
    g.do("pad", KARR + ":Array_Resize", TargetArray=g.var(P + "Sub"), Size=g.max_(g.length(g.var(P + "Sub")), "3"))
    g.do("items", "SlotItems", Class=g.var("ParseCode_Class"), Slot="@entry.Slot")
    g.put("keepItems", P + "Items", "@items.Items")
    g.put("keepIndex", P + "Index", g.stoi(g.at(g.var(P + "Sub"), "0")))
    g.br("brIndex", g.in_range(g.var(P + "Index"), "1", g.length(g.var(P + "Items"))))
    g.put("setItem", P + "Item", g.at(g.var(P + "Items"), g.sub(g.var(P + "Index"), "1")))
    g.br("brItem", g.valid(g.var(P + "Item")))
    g.put("setFound", P + "Found", "true")
    g.put("keepClass", P + "Class", g.val(ITEMID + ":GetItemClass", target=g.var(P + "Item")))
    g.br("brClass", g.valid_class(g.var(P + "Class")))
    g.put("keepTiers", P + "Tiers", g.val(GEARCOMP + ":GetItemUpgradeTiers", itemClass=g.var(P + "Class")))
    g.put("keepText", P + "TierText", g.at(g.var(P + "Sub"), "1"))
    tier = g.fori("tiers", "0", g.sub(g.length(g.var(P + "Tiers")), "1"))
    options = g.length(g.brk(UPGRADETIER, g.at(g.var(P + "Tiers"), tier))("upgrades"))
    digit = g.val(KSTR + ":GetSubstring", SourceString=g.var(P + "TierText"), StartIndex=tier, Length="1")
    g.put("keepDigit", P + "Digit", g.stoi(digit))
    choice = g.val(KML + ":SelectInt", A=g.var(P + "Digit"), B="0", bPickA=g.in_range(g.var(P + "Digit"), "1", options))
    g.put("keepChoice", P + "Choice", choice)
    g.append("addChoice", g.var(P + "Choices"), g.var(P + "Choice"))
    space = g.pick(" ", "", g.cmp("Greater", tier, "0"))
    g.put("addDigit", P + "Digits", g.cat(g.var(P + "Digits"), space, g.itos(g.var(P + "Choice"))))
    g.flow("tiers.LoopBody", "keepDigit", "keepChoice", "addChoice", "addDigit")
    # Overclock.
    g.put("keepOcIndex", P + "OcIndex", g.stoi(g.at(g.var(P + "Sub"), "2")))
    g.do("ocs", "OverclocksOf", Item=g.var(P + "Item"))
    g.put("keepOcs", P + "OCs", "@ocs.Overclocks")
    g.br("brOc", g.in_range(g.var(P + "OcIndex"), "1", g.length(g.var(P + "OCs"))))
    g.put("setOc", P + "Overclock", g.at(g.var(P + "OCs"), g.sub(g.var(P + "OcIndex"), "1")))
    g.flow("entry", "item0", "oc0", "digits0", "found0", "choices0", "parse", "brValid", "brSlot", "keepSub", "pad",
           "items", "keepItems", "keepIndex", "brIndex", "setItem", "brItem", "setFound", "keepClass", "brClass",
           "keepTiers", "keepText", "tiers")
    g.flow("tiers.Completed", "keepOcIndex", "ocs", "keepOcs", "brOc", "setOc", "result")
    g.flow("brClass.else", "keepOcIndex")
    g.ends(["brValid.else", "brSlot.else", "brIndex.else", "brItem.else", "brOc.else"], "result")
    g.out("Item", g.var(P + "Item"))
    g.out("Choices", g.var(P + "Choices"))
    g.out("Overclock", g.var(P + "Overclock"))
    g.out("Digits", g.var(P + "Digits"))
    g.out("Found", g.var(P + "Found"))
    return g.data()


def g_tier_options():
    g = D()
    P = "TierOptions_"
    g.clear("clear", g.var(P + "Upgrades"))
    g.br("brItem", g.valid("@entry.Item"))
    g.put("keepClass", P + "Class", g.val(ITEMID + ":GetItemClass", target="@entry.Item"))
    g.br("brClass", g.valid_class(g.var(P + "Class")))
    g.put("keepTiers", P + "Tiers", g.val(GEARCOMP + ":GetItemUpgradeTiers", itemClass=g.var(P + "Class")))
    g.br("brTier", g.in_range("@entry.Tier", "0", g.sub(g.length(g.var(P + "Tiers")), "1")))
    g.put("set", P + "Upgrades", g.brk(UPGRADETIER, g.at(g.var(P + "Tiers"), "@entry.Tier"))("upgrades"))
    g.flow("entry", "clear", "brItem", "keepClass", "brClass", "keepTiers", "brTier", "set", "result")
    g.ends(["brItem.else", "brClass.else", "brTier.else"], "result")
    g.out("Upgrades", g.var(P + "Upgrades"))
    return g.data()


# ============================================================================ DB_Data: perk IDs of the build code
# PerkNames = Tools/dwarfbuilds/perk_ids.json, baked in when the spec is made; perk ID = index + 1. PerkTable holds
# the perk asset of each name (None when this game has no such perk), filled once from the game's perk list.

def g_ensure_perk_names():
    g = D()
    names = perk_names()
    g.br("brEmpty", g.cmp("EqualEqual", g.length(g.var("PerkNames")), "0"))
    g.node("names", "makearray", n=len(names))
    g.pins("names", {"[%d]" % k: name for k, name in enumerate(names)})
    g.put("set", "PerkNames", "@names.Array")
    g.flow("entry", "brEmpty", "set")
    return g.data()


def g_ensure_perk_table():
    """PerkTable[i] = the perk named PerkNames[i]: from GetAvailablePerks (the perk bank), then the owned perks. Done
    once the game gave any perks (else tried again on the next call)."""
    g = D()
    P = "PerkTable_"
    g.br("brDone", g.var("PerkTableDone"))
    g.do("names", "EnsurePerkNames")
    g.clear("clear", g.var("PerkTable"))
    g.do("size", KARR + ":Array_Resize", TargetArray=g.var("PerkTable"), Size=g.length(g.var("PerkNames")))
    g.put("keepAll", P + "All", g.val(PFL + ":GetAvailablePerks"))
    g.do("owned", KARR + ":Array_Append", TargetArray=g.var(P + "All"), SourceArray=g.val(PFL + ":GetOwnedPerks"))
    perk, _ = g.each("perks", g.var(P + "All"))
    g.br("brPerk", g.valid(perk))
    name = g.val(KSL + ":GetObjectName", Object=perk)
    g.put("keepIndex", P + "Index", g.val(KARR + ":Array_Find", TargetArray=g.var("PerkNames"), ItemToFind=name))
    g.br("brKnown", g.cmp("GreaterEqual", g.var(P + "Index"), "0"))
    g.do("setPerk", KARR + ":Array_Set", TargetArray=g.var("PerkTable"), Index=g.var(P + "Index"), Item=perk,
         bSizeToFit="false")
    g.put("done", "PerkTableDone", g.cmp("Greater", g.length(g.var(P + "All")), "0"))
    g.flow("entry", "brDone")
    g.flow("brDone.else", "names", "clear", "size", "keepAll", "owned", "perks.Exec")
    g.flow("perks.LoopBody", "brPerk", "keepIndex", "brKnown", "setPerk")
    g.flow("perks.Completed", "done")
    return g.data()


def g_perk_id():
    """Perk ID of a perk (its asset name in PerkNames, + 1); 0 = unknown or None."""
    g = D()
    P = "PerkId_"
    g.put("zero", P + "Id", "0")
    g.br("brPerk", g.valid("@entry.Perk"))
    g.do("names", "EnsurePerkNames")
    name = g.val(KSL + ":GetObjectName", Object="@entry.Perk")
    g.put("set", P + "Id", g.add(g.val(KARR + ":Array_Find", TargetArray=g.var("PerkNames"), ItemToFind=name), "1"))
    g.flow("entry", "zero", "brPerk", "names", "set", "result")
    g.flow("brPerk.else", "result")
    g.out("Id", g.var(P + "Id"))
    return g.data()


def g_perks_part():
    """The perks part of a code: the IDs of the perks in their order, joined with "."; unknown perks left out."""
    g = D()
    P = "PerksPart_"
    g.put("part0", P + "Part", "")
    g.put("keep", P + "Perks", "@entry.Perks")
    perk, _ = g.each("perks", g.var(P + "Perks"))
    g.do("id", "PerkId", Perk=perk)
    g.br("brId", g.cmp("Greater", "@id.Id", "0"))
    dot = g.pick(".", "", g.cmp("Greater", g.strlen(g.var(P + "Part")), "0"))
    g.put("add", P + "Part", g.cat(g.var(P + "Part"), dot, g.itos("@id.Id")))
    g.flow("entry", "part0", "keep", "perks.Exec")
    g.flow("perks.LoopBody", "id", "brId", "add")
    g.flow("perks.Completed", "result")
    g.out("Part", g.var(P + "Part"))
    return g.data()


def g_perk_ids():
    """Perk IDs of a perks part ("12.7.21"): numbers in 1..len(PerkNames), each once, in order. PerkIds_Bad counts
    the pieces outside that range (perks of a newer game version)."""
    g = D()
    P = "PerkIds_"
    g.clear("clear", g.var(P + "Ids"))
    g.put("bad0", P + "Bad", "0")
    g.do("names", "EnsurePerkNames")
    g.put("keepPieces", P + "Pieces",
          g.val(KSTR + ":ParseIntoArray", SourceString="@entry.Part", Delimiter=".", CullEmptyStrings="true"))
    piece, _ = g.each("pieces", g.var(P + "Pieces"))
    g.put("keepId", P + "Id", g.stoi(piece))
    g.br("brId", g.in_range(g.var(P + "Id"), "1", g.length(g.var("PerkNames"))))
    g.do("add", KARR + ":Array_AddUnique", TargetArray=g.var(P + "Ids"), NewItem=g.var(P + "Id"))
    g.incr("countBad", P + "Bad")
    g.flow("entry", "clear", "bad0", "names", "keepPieces", "pieces.Exec")
    g.flow("pieces.LoopBody", "keepId", "brId", "add")
    g.flow("brId.else", "countBad")
    g.flow("pieces.Completed", "result")
    g.out("Ids", g.var(P + "Ids"))
    return g.data()


def g_perks_of_code():
    """PerksOfCode_Unknown: perk IDs of the code that this game version does not have (ApplyPerks reports them)."""
    g = D()
    P = "PerksOfCode_"
    g.clear("perks0", g.var(P + "Perks"))
    g.clear("ranks0", g.var(P + "Ranks"))
    g.put("unknown0", P + "Unknown", "0")
    g.do("parse", "ParseCode", Code="@entry.Code")
    g.br("brValid", "@parse.Valid")
    g.do("ids", "PerkIds", Part=g.at(g.var("ParseCode_Parts"), PERKS_PART))
    g.put("keepIds", P + "Ids", "@ids.Ids")
    g.put("keepBad", P + "Unknown", g.var("PerkIds_Bad"))
    g.do("table", "EnsurePerkTable")
    pid, _ = g.each("each", g.var(P + "Ids"))
    g.put("keepPerk", P + "Perk", g.at(g.var("PerkTable"), g.sub(pid, "1")))
    g.br("brPerk", g.valid(g.var(P + "Perk")))
    g.append("addPerk", g.var(P + "Perks"), g.var(P + "Perk"))
    # Rank for the tooltip: yours, or the highest when you do not own it.
    g.put("keepRank", P + "Rank", g.val(PERKASSET + ":GetCurrentRank", target=g.var(P + "Perk")))
    top = g.val(PERKASSET + ":GetMaxRank", target=g.var(P + "Perk"))
    g.append("addRank", g.var(P + "Ranks"),
             g.val(KML + ":SelectInt", A=g.var(P + "Rank"), B=top, bPickA=g.cmp("Greater", g.var(P + "Rank"), "0")))
    g.incr("countUnknown", P + "Unknown")
    g.flow("entry", "perks0", "ranks0", "unknown0", "parse", "brValid", "ids", "keepIds", "keepBad", "table",
           "each.Exec")
    g.flow("each.LoopBody", "keepPerk", "brPerk", "addPerk", "keepRank", "addRank")
    g.flow("brPerk.else", "countUnknown")
    g.ends(["brValid.else", "each.Completed"], "result")
    g.out("Perks", g.var(P + "Perks"))
    g.out("Ranks", g.var(P + "Ranks"))
    g.out("Found", g.cmp("Greater", g.length(g.var(P + "Perks")), "0"))
    return g.data()


def g_perk_kind():
    """0 = passive, 1 = active, 2 = proficiency (neither passive nor active). Perk must be valid."""
    g = D()
    passive = g.val(PERKASSET + ":IsUsageType", target="@entry.Perk", InType="Passive")
    active = g.val(PERKASSET + ":IsUsageType", target="@entry.Perk", InType="Active")
    g.out("Kind", g.val(KML + ":SelectInt", A="0", B=g.val(KML + ":SelectInt", A="1", B="2", bPickA=active),
                        bPickA=passive))
    g.flow("entry", "result")
    return g.data()


# ============================================================================ DB_Data: players

def g_get_players():
    g = D()
    P = "GetPlayers_"
    g.put("keepState", P + "State", g.val(GFL + ":GetFSDGameState"))
    g.br("brState", g.valid(g.var(P + "State")))
    g.put("set", P + "Players", g.val(GAMESTATE + ":GetNetworkSortedPlayerArray", target=g.var(P + "State")))
    g.clear("clear", g.var(P + "Players"))
    g.flow("entry", "keepState", "brState", "set", "result")
    g.flow("brState.else", "clear", "result")
    g.out("Players", g.var(P + "Players"))
    return g.data()


def g_header_of():
    g = D()
    P = "HeaderOf_"
    player = "@entry.Player"
    g.put("name0", P + "Name", "")
    g.put("sub0", P + "Sub", "")
    g.put("color0", P + "Color", colour(ORANGE))
    g.put("icon0", P + "Icon")
    g.put("you0", P + "IsYou", "false")
    g.put("host0", P + "IsHost", "false")
    g.br("brPlayer", g.valid(player))
    g.put("setName", P + "Name", g.val(PLAYERSTATE + ":GetPlayerName", target=player))
    g.put("setHost", P + "IsHost", g.var("bIsServer", PS, player))
    g.do("local", "LocalPS")
    g.put("setYou", P + "IsYou", g.same(player, "@local.PS"))
    g.put("keepClass", P + "Class", g.val(PS + ":GetSelectedCharacterID", target=player))
    g.br("brClass", g.valid(g.var(P + "Class")))
    g.put("noClass", P + "Sub", "SELECTING CLASS")
    g.do("letter", "ClassLetter", Class=g.var(P + "Class"))
    g.put("promos0", P + "Promos", "0")
    comp = g.var("SaveGameStateComponent", PS, player)
    g.br("brComp", g.valid(comp))
    g.do("stat", SGSC + ":GetCharacterStat", target=comp, characterID=g.var(P + "Class"))
    g.put("setPromos", P + "Promos", g.brk(PROGRESS, "@stat.ReturnValue")("TimesRetired"))
    promos = g.var(P + "Promos")
    some = g.pick("1 PROMOTION", g.cat(g.itos(promos), " PROMOTIONS"), g.cmp("EqualEqual", promos, "1"))
    promo_text = g.pick("NO PROMOTIONS", some, g.cmp("LessEqual", promos, "0"))
    level = g.itos(g.val(PS + ":GetSelectedCharacterLevel", target=player))
    g.put("setSub", P + "Sub", g.cat("@letter.Name", DOT + "LV ", level, DOT, promo_text))
    g.put("keepHero", P + "Hero", g.val(CHARID + ":GetCharacterClass", target=g.var(P + "Class")))
    g.br("brHero", g.valid_class(g.var(P + "Hero")))
    g.put("setColor", P + "Color", g.val(AFL + ":GetHeroColor", playerClass=g.var(P + "Hero")))
    g.put("setIcon", P + "Icon", g.val(AFL + ":GetHeroImageSmall", playerClass=g.var(P + "Hero")))
    g.flow("entry", "name0", "sub0", "color0", "icon0", "you0", "host0", "brPlayer", "setName", "setHost", "local",
           "setYou", "keepClass", "brClass", "letter", "promos0", "brComp", "stat", "setPromos", "setSub", "keepHero",
           "brHero", "setColor", "setIcon", "result")
    g.flow("brComp.else", "setSub")
    g.flow("brClass.else", "noClass", "result")
    g.ends(["brPlayer.else", "brHero.else"], "result")
    for name in ("Name", "Sub", "Color", "Icon", "IsYou", "IsHost"):
        g.out(name, g.var(P + name))
    return g.data()


def g_header_of_code():
    g = D()
    P = "HeaderOfCode_"
    g.put("sub0", P + "Sub", "")
    g.put("color0", P + "Color", colour(ORANGE))
    g.put("icon0", P + "Icon")
    g.do("parse", "ParseCode", Code="@entry.Code")
    g.br("brValid", "@parse.Valid")
    g.do("letter", "ClassLetter", Class=g.var("ParseCode_Class"))
    g.put("setSub", P + "Sub", g.cat("@letter.Name", " BUILD"))
    g.put("keepHero", P + "Hero", g.val(CHARID + ":GetCharacterClass", target=g.var("ParseCode_Class")))
    g.br("brHero", g.valid_class(g.var(P + "Hero")))
    g.put("setColor", P + "Color", g.val(AFL + ":GetHeroColor", playerClass=g.var(P + "Hero")))
    g.put("setIcon", P + "Icon", g.val(AFL + ":GetHeroImageSmall", playerClass=g.var(P + "Hero")))
    g.flow("entry", "sub0", "color0", "icon0", "parse", "brValid", "letter", "setSub", "keepHero", "brHero",
           "setColor", "setIcon", "result")
    g.ends(["brValid.else", "brHero.else"], "result")
    for name in ("Sub", "Color", "Icon"):
        g.out(name, g.var(P + name))
    return g.data()


def g_perks_of():
    """Another player with a link (LinkFor): the perks of the link's code, or state 3 when the link does not know
    them. Else, local player: the save; host: the player's EquippedPerks; client: the host's DB_PerkShare_v1 table
    (cached once found). The game sends a player's perks to the host only at times and to clients never, so none
    known for another player is state 3 (unknown), not an empty row. Sorted by kind (SortPerks; a code's perks
    are in that order already)."""
    g = D()
    P = "PerksOf_"
    player = "@entry.Player"
    g.clear("perks0", g.var(P + "Perks"))
    g.clear("ranks0", g.var(P + "Ranks"))
    g.put("state0", P + "State", "0")
    g.br("brPlayer", g.valid(player))
    # Another player's link (None for the local player): the perks are those of its code, as CodeOf gives the code.
    g.do("link", "LinkFor", Player=player)
    g.br("brLink", g.valid("@link.Link"))
    g.br("brLinkKnown", g.var("PerksKnown", LINK_C, "@link.Link"))
    g.do("linkPerks", "PerksOfCode", Code=g.var("Code", LINK_C, "@link.Link"))
    g.put("setLinkPerks", P + "Perks", "@linkPerks.Perks")
    g.put("setLinkRanks", P + "Ranks", "@linkPerks.Ranks")
    g.put("state3", P + "State", "3")
    g.put("keepClass", P + "Class", g.val(PS + ":GetSelectedCharacterID", target=player))
    g.br("brClass", g.valid(g.var(P + "Class")))
    g.do("local", "LocalPS")
    g.br("brLocal", g.same(player, "@local.PS"))
    g.flow("entry", "perks0", "ranks0", "state0", "brPlayer", "link", "brLink", "brLinkKnown", "linkPerks",
           "setLinkPerks", "setLinkRanks", "result")
    g.flow("brLinkKnown.else", "state3", "result")
    g.flow("brLink.else", "keepClass", "brClass", "local", "brLocal")
    g.ends(["brPlayer.else", "brClass.else"], "result")
    # Local player: the save.
    g.put("keepOwn", P + "Own", g.val(PFL + ":GetCharacterEquippedPerks", characterID=g.var(P + "Class")))
    perk, _ = g.each("own", g.var(P + "Own"))
    g.br("brOwn", g.valid(perk))
    g.append("addOwn", g.var(P + "Perks"), perk)
    g.append("addOwnRank", g.var(P + "Ranks"), g.val(PERKASSET + ":GetCurrentRank", target=perk))
    g.flow("brLocal", "keepOwn", "own.Exec")
    g.flow("own.LoopBody", "brOwn", "addOwn", "addOwnRank")
    g.flow("own.Completed", "sort")
    # No perks from the sources below: unknown. But a player whose link is young may still send their build (their
    # mod does it when the link reaches them): state 2 for LINK_YOUNG seconds, so "not available" does not flash.
    g.br("brNone", g.cmp("EqualEqual", g.length(g.var(P + "Perks")), "0"))
    g.call("theirs", KMAP + ":Map_Find", TargetMap=g.var("LinkMap"), Key=player)
    g.put("keepTheirs", P + "Link", "@theirs.Value")
    g.br("brTheirs", g.valid(g.var(P + "Link")))
    young = g.val(KML + ":Less_FloatFloat", A=g.val(ACTOR + ":GetGameTimeSinceCreation", target=g.var(P + "Link")),
                  B=LINK_YOUNG)
    g.br("brYoung", young)
    g.put("stateWait", P + "State", "2")
    g.flow("brNone", "keepTheirs", "brTheirs", "brYoung", "stateWait", "result")
    g.flow("brNone.else", "sort")
    g.ends(["brTheirs.else", "brYoung.else"], "state3")
    # Host: what the server knows of the player.
    g.br("brServer", g.val(KSL + ":IsServer"))
    comp = g.var("SaveGameStateComponent", PS, player)
    g.br("brComp", g.valid(comp))
    g.put("keepItems", P + "Items", g.var("EquippedPerks", SGSC, comp))
    item, _ = g.each("items", g.var(P + "Items"))
    entry = g.brk(PERKITEM, item)
    g.br("brItem", g.valid(entry("Perk")))
    g.append("addItem", g.var(P + "Perks"), entry("Perk"))
    g.append("addItemRank", g.var(P + "Ranks"), g.val(KML + ":Conv_ByteToInt", InByte=entry("Rank")))
    g.flow("brLocal.else", "brServer", "brComp", "keepItems", "items.Exec")
    g.flow("items.LoopBody", "brItem", "addItem", "addItemRank")
    g.flow("items.Completed", "brNone")
    g.flow("brComp.else", "keepTheirs")
    # Client: the host's table. No table in the first 10 s: not received yet (2); after that: the host does not
    # run this mod (1).
    g.br("brCached", g.valid(g.var(P + "Share")))
    g.do("findShare", GS + ":GetActorOfClass", ActorClass=SHARE_C)
    g.put("keepShare", P + "Share", "@findShare.ReturnValue")
    g.br("brShare", g.valid(g.var(P + "Share")))
    g.br("brEarly", g.val(KML + ":Less_FloatFloat", A=g.val(ACTOR + ":GetGameTimeSinceCreation"), B="10.0"))
    g.put("waitShare", P + "State", "2")
    g.put("state1", P + "State", "1")
    g.do("find", SHARE_C + ":Find", target=g.var(P + "Share"), PlayerId=g.var("PlayerId", PLAYERSTATE, player),
         Class=g.var(P + "Class"))
    g.br("brFound", "@find.Found")
    g.put("state2", P + "State", "2")
    g.put("setPerks", P + "Perks", "@find.Perks")
    g.put("setRanks", P + "Ranks", "@find.Ranks")
    g.flow("brServer.else", "brCached", "find")
    g.flow("brCached.else", "findShare", "keepShare", "brShare", "find")
    g.flow("brShare.else", "brEarly", "waitShare", "result")
    g.flow("brEarly.else", "state1", "result")
    g.flow("find", "brFound", "setPerks", "setRanks", "brNone")
    g.flow("brFound.else", "state2", "result")
    g.do("sort", "SortPerks")
    g.flow("sort", "result")
    g.out("Perks", g.var(P + "Perks"))
    g.out("Ranks", g.var(P + "Ranks"))
    g.out("State", g.var(P + "State"))
    return g.data()


def g_sort_perks():
    """PerksOf_Perks/Ranks: passive perks, then active ones, then the proficiency (PerkKind order); each kind keeps
    its order; None entries dropped."""
    g = D()
    P, O = "SortPerks_", "PerksOf_"
    g.clear("clearPerks", g.var(P + "Perks"))
    g.clear("clearRanks", g.var(P + "Ranks"))
    g.do("pad", KARR + ":Array_Resize", TargetArray=g.var(O + "Ranks"),
         Size=g.max_(g.length(g.var(O + "Ranks")), g.length(g.var(O + "Perks"))))
    g.flow("entry", "clearPerks", "clearRanks", "pad", "pass0.Exec")
    for k in range(len(KINDS)):
        perk, index = g.each("pass%d" % k, g.var(O + "Perks"))
        g.br("brValid%d" % k, g.valid(perk))
        g.do("kind%d" % k, "PerkKind", Perk=perk)
        g.br("brType%d" % k, g.cmp("EqualEqual", "@kind%d.Kind" % k, str(k)))
        g.append("addPerk%d" % k, g.var(P + "Perks"), perk)
        g.append("addRank%d" % k, g.var(P + "Ranks"), g.at(g.var(O + "Ranks"), index))
        g.flow("pass%d.LoopBody" % k, "brValid%d" % k, "kind%d" % k, "brType%d" % k, "addPerk%d" % k, "addRank%d" % k)
        if k:
            g.flow("pass%d.Completed" % (k - 1), "pass%d.Exec" % k)
    g.put("copyPerks", O + "Perks", g.var(P + "Perks"))
    g.put("copyRanks", O + "Ranks", g.var(P + "Ranks"))
    g.flow("pass%d.Completed" % (len(KINDS) - 1), "copyPerks", "copyRanks")
    return g.data()


# ============================================================================ DB_Data: texts and tooltips

def g_item_texts():
    """Name, upper-case category, description and icons of an item (item data, else its gear component)."""
    g = D()
    P = "ItemTexts_"
    for name in ("Name", "Category", "Description", "Line", "Fill"):
        g.put(name + "0", P + name)
    g.br("brItem", g.valid("@entry.Item"))
    g.put("keepData", P + "Data", g.val(ITEMID + ":GetItemData", target="@entry.Item"))
    g.br("brData", g.valid(g.var(P + "Data")))
    data = g.var(P + "Data")
    g.put("setName", P + "Name", g.var("Name", ITEMDATA, data))
    g.put("setCategory", P + "Category", g.upper_text(g.var("Category", ITEMDATA, data)))
    g.put("setDescription", P + "Description", g.var("Description", ITEMDATA, data))
    g.put("setLine", P + "Line", g.var("IconLine", ITEMDATA, data))
    g.put("setFill", P + "Fill", g.var("IconBG", ITEMDATA, data))
    g.do("gear", "GearOf", Item="@entry.Item")
    g.put("keepGear", P + "Gear", "@gear.Gear")
    g.br("brGear", g.valid(g.var(P + "Gear")))
    gear = g.var(P + "Gear")
    g.put("gearName", P + "Name", g.val(GEARCOMP + ":GetGearName", target=gear))
    g.put("gearCategory", P + "Category", g.upper_text(g.val(GEARCOMP + ":GetGearCategory", target=gear)))
    g.put("gearDescription", P + "Description", g.val(GEARCOMP + ":GetGearDescription", target=gear))
    g.put("gearLine", P + "Line", g.val(GEARCOMP + ":GetIconLine", target=gear))
    g.put("gearFill", P + "Fill", g.val(GEARCOMP + ":GetIconBG", target=gear))
    g.flow("entry", "Name0", "Category0", "Description0", "Line0", "Fill0", "brItem", "keepData", "brData", "setName",
           "setCategory", "setDescription", "setLine", "setFill", "result")
    g.flow("brData.else", "gear", "keepGear", "brGear", "gearName", "gearCategory", "gearDescription", "gearLine",
           "gearFill", "result")
    g.ends(["brItem.else", "brGear.else"], "result")
    for name in ("Name", "Category", "Description", "Line", "Fill"):
        g.out(name, g.var(P + name))
    return g.data()


def g_item_visual():
    g = D()
    g.do("texts", "ItemTexts", Item="@entry.Item")
    g.flow("entry", "texts", "result")
    for name in ("Name", "Category", "Line", "Fill"):
        g.out(name, "@texts." + name)
    return g.data()


def g_item_tip():
    g = D()
    g.do("texts", "ItemTexts", Item="@entry.Item")
    g.flow("entry", "texts", "result")
    g.out("Title", "@texts.Name")
    g.out("Category", "@texts.Category")
    g.out("Body", "@texts.Description")
    g.out("Icon", "@texts.Line")
    return g.data()


def g_stat_body():
    """Description, then one line per stat text: "+ ..." when advantageous, "- ..." when not."""
    g = D()
    P = "StatBody_"
    upgrade = "@entry.Upgrade"
    g.put("keepText", P + "Text", g.ttos(g.var("Description", UPGRADE, upgrade)))
    g.put("keepStats", P + "Stats", g.val(UPGRADE + ":GetUpgradeStatTexts", target=upgrade))
    stat, _ = g.each("stats", g.var(P + "Stats"))
    fields = g.brk(STATTEXT, stat)
    g.put("keepLine", P + "Line", g.ttos(fields("StatText")))
    g.br("brLine", g.cmp("Greater", g.strlen(g.var(P + "Line")), "0"))
    sign = g.pick("+ ", "- ", fields("IsAdventageous"))
    newline = g.pick("\n", "", g.cmp("Greater", g.strlen(g.var(P + "Text")), "0"))
    g.put("append", P + "Text", g.cat(g.var(P + "Text"), newline, sign, g.var(P + "Line")))
    g.flow("entry", "keepText", "keepStats", "stats.Exec")
    g.flow("stats.LoopBody", "keepLine", "brLine", "append")
    g.flow("stats.Completed", "result")
    g.out("Body", g.stot(g.var(P + "Text")))
    return g.data()


def g_upgrade_tip():
    g = D()
    P = "UpgradeTip_"
    upgrade = "@entry.Upgrade"
    for name in ("Title", "Category", "Body", "Icon"):
        g.put(name + "0", P + name)
    g.br("brUp", g.valid(upgrade))
    g.put("setTitle", P + "Title", g.var("Name", UPGRADE, upgrade))
    g.do("body", "StatBody", Upgrade=upgrade)
    g.put("setBody", P + "Body", "@body.Body")
    for name in ("ExtraTitle", "Extra"):
        g.put(name + "0", P + name)
    g.put("keepCat", P + "Cat", g.var("Category", UPGRADE, upgrade))
    g.br("brCat", g.valid(g.var(P + "Cat")))
    cat = g.var(P + "Cat")
    g.put("setCategory", P + "Category", g.upper_text(g.var("CategoryName", UPGCAT, cat)))
    g.put("setIcon", P + "Icon", g.var("CategoryIcon", UPGCAT, cat))
    # The "more info" box, as TOOLTIP_UpgradeIcon fills it: upper-case category name and its description.
    g.put("setExtra", P + "Extra", g.var("CategoryDescription", UPGCAT, cat))
    g.br("brExtra", g.val(KTXT + ":TextIsEmpty", InText=g.var(P + "Extra")))
    g.put("setExtraTitle", P + "ExtraTitle", g.var(P + "Category"))
    g.flow("entry", "Title0", "Category0", "Body0", "Icon0", "ExtraTitle0", "Extra0", "brUp", "setTitle", "body",
           "setBody", "keepCat", "brCat", "setCategory", "setIcon", "setExtra", "brExtra")
    g.flow("brExtra.else", "setExtraTitle", "result")
    g.ends(["brUp.else", "brCat.else", "brExtra.then"], "result")
    for name in ("Title", "Category", "Body", "Icon", "ExtraTitle", "Extra"):
        g.out(name, g.var(P + name))
    return g.data()


def g_overclock_tip():
    """Type (Clean/Balanced/Unstable) from the schematic category: asset SCAT_OC_<Type>, name "<Type> Overclock"."""
    g = D()
    P = "OverclockTip_"
    oc = "@entry.Overclock"
    resets = []
    for name, value in (("Title", None), ("Body", None), ("CatText", ""), ("CatName", ""), ("TypeFrame", None),
                        ("Icon", None), ("Frame", None), ("Scat", None), ("Color", colour(ORANGE))):
        resets.append(g.put(name + "0", P + name, value))
    g.br("brOc", g.valid(oc))
    g.put("setTitle", P + "Title", g.var("Name", UPGRADE, oc))
    g.do("body", "StatBody", Upgrade=oc)
    g.put("setBody", P + "Body", "@body.Body")
    g.put("keepCat", P + "Cat", g.var("Category", UPGRADE, oc))
    g.br("brCat", g.valid(g.var(P + "Cat")))
    g.put("setIcon", P + "Icon", g.var("CategoryIcon", UPGCAT, g.var(P + "Cat")))
    g.put("keepScat", P + "Scat", g.var("SchematicCategory", OVERCLOCK, oc))
    g.br("brScat", g.valid(g.var(P + "Scat")))
    g.do("findScat", SCHEMLIB + ":FindItemUpgradeSchematicCategory", Upgrade=oc)
    g.put("setScat", P + "Scat", "@findScat.ReturnValue")
    g.br("brScat2", g.valid(g.var(P + "Scat")))
    scat = g.var(P + "Scat")
    g.put("keepName", P + "CatName", g.ttos(g.var("CategoryName", SCHEMCAT, scat)))
    g.put("keepKey", P + "Key", g.cat(g.val(KSL + ":GetObjectName", Object=scat), " ", g.var(P + "CatName")))
    g.put("noKey", P + "Key", "")
    g.flow("entry", *resets)
    # The game's own overclock icon asks FindItemUpgradeSchematicCategory first; the asset's SchematicCategory is
    # only the fallback here.
    g.flow(resets[-1], "brOc", "setTitle", "body", "setBody", "keepCat", "brCat", "setIcon", "findScat", "setScat",
           "brScat", "keepName", "keepKey", "isClean")
    g.flow("brCat.else", "findScat")
    g.flow("brScat.else", "keepScat", "brScat2", "keepName")
    g.flow("brScat2.else", "noKey", "isClean")
    g.flow("brOc.else", "result")
    previous = None
    for kind in ("Clean", "Balanced", "Unstable"):
        g.br("is" + kind, g.val(KSTR + ":Contains", SearchIn=g.var(P + "Key"), Substring=kind))
        g.put("cat" + kind, P + "CatText", kind.upper() + " OVERCLOCK")
        g.put("color" + kind, P + "Color", colour(OC_COLOURS[kind]))
        g.put("type" + kind, P + "TypeFrame", g.var("OcFrame" + kind))
        g.flow("is" + kind, "cat" + kind, "color" + kind, "type" + kind, "frame")
        if previous:
            g.flow("is%s.else" % previous, "is" + kind)
        previous = kind
    # Unknown type: the category's own name.
    other = g.pick(g.val(KSTR + ":ToUpper", SourceString=g.var(P + "CatName")), "OVERCLOCK",
                   g.cmp("Greater", g.strlen(g.var(P + "CatName")), "0"))
    g.put("catOther", P + "CatText", other)
    g.flow("isUnstable.else", "catOther", "frame")
    # Frame: the category's own frame texture if it is loaded already, else the type's frame (loaded at BeginPlay;
    # None until then). Nothing is loaded here.
    g.br("frame", g.valid(g.var(P + "Scat")))
    own = g.val(KSL + ":Conv_SoftObjectReferenceToObject",
                SoftObject=g.var("FrameTexture", SCHEMCAT, g.var(P + "Scat")))
    g.put("setOwn", P + "Frame", g.cast_("asOwn", TEXTURE, own))
    g.br("brFrame", g.valid(g.var(P + "Frame")))
    g.put("setType", P + "Frame", g.var(P + "TypeFrame"))
    g.flow("frame", "asOwn", "setOwn", "brFrame")
    g.ends(["asOwn.CastFailed", "frame.else"], "brFrame")
    g.flow("brFrame.else", "setType", "result")
    g.flow("brFrame.then", "result")
    g.out("Title", g.var(P + "Title"))
    g.out("Category", g.stot(g.var(P + "CatText")))
    g.out("Body", g.var(P + "Body"))
    g.out("Icon", g.var(P + "Icon"))
    g.out("Color", g.var(P + "Color"))
    g.out("Frame", g.var(P + "Frame"))
    return g.data()


def g_perk_tip():
    g = D()
    P = "PerkTip_"
    perk = "@entry.Perk"
    for name in ("Title", "Category", "Body", "Icon"):
        g.put(name + "0", P + name)
    g.put("Color0", P + "Color", colour(PERK_PASSIVE))
    g.br("brPerk", g.valid(perk))
    g.put("setTitle", P + "Title", g.var("Title", PERKASSET, perk))
    g.put("setIcon", P + "Icon", g.var("Icon", PERKASSET, perk))
    g.do("kind", "PerkKind", Perk=perk)
    passive, active = g.cmp("EqualEqual", "@kind.Kind", "0"), g.cmp("EqualEqual", "@kind.Kind", "1")
    category = g.pick("PASSIVE PERK", g.pick("ACTIVE PERK", "PROFICIENCY", active), passive)
    g.put("setCategory", P + "Category", g.stot(category))
    tone = g.val(KML + ":SelectColor", A=colour(PERK_PASSIVE),
                 B=g.val(KML + ":SelectColor", A=colour(PERK_ACTIVE), B=colour(PERK_PROF), bPickA=active), bPickA=passive)
    g.put("setColor", P + "Color", tone)
    # The description. GetRankDescription has a second parameter (bPreviewNextRank) only in game versions with
    # proficiency perks; a Blueprint call with a parameter the game does not have runs off the end of its
    # bytecode and hangs the game. So it is called only when the game has ProficiencyPerkAsset (the same update);
    # older versions show GetAdditionalRankDescription (one parameter in both versions) instead.
    rank = g.max_("@entry.Rank", "1")
    g.do("newApi", KSL + ":LoadClassAsset_Blocking",
         AssetClass=g.val(KSL + ":Conv_SoftClassPathToSoftClassRef",
                          SoftClassPath=g.val(KSL + ":MakeSoftClassPath", PathString=PROFASSET)))
    g.br("brNewApi", g.valid_class("@newApi.ReturnValue"))
    text = g.val(PERKASSET + ":GetRankDescription", target=perk, Rank=rank, bPreviewNextRank="false")
    g.do("strip", "StripTags", Source=g.ttos(text))
    g.put("setBody", P + "Body", g.stot("@strip.Out"))
    g.do("stripOld", "StripTags", Source=g.val(PERKASSET + ":GetAdditionalRankDescription", target=perk, Rank=rank))
    g.put("setBodyOld", P + "Body", g.stot("@stripOld.Out"))
    g.flow("entry", "Title0", "Category0", "Body0", "Icon0", "Color0", "brPerk", "setTitle", "setIcon", "kind",
           "setCategory", "setColor", "newApi", "brNewApi", "strip", "setBody", "result")
    g.flow("brNewApi.else", "stripOld", "setBodyOld", "result")
    g.flow("brPerk.else", "result")
    for name in ("Title", "Category", "Body", "Icon", "Color"):
        g.out(name, g.var(P + name))
    return g.data()


def g_strip_tags():
    """Removes rich-text tags (<Highlight>, </>) from a perk description. One loop step per tag: the source is split
    at "<"; each piece after the first starts inside a tag, so only the text after its first ">" is kept (a piece
    without ">" is still inside the tag and is dropped)."""
    g = D()
    P = "StripTags_"
    g.put("out0", P + "Out", "")
    g.put("keepPieces", P + "Pieces",
          g.val(KSTR + ":ParseIntoArray", SourceString="@entry.Source", Delimiter="<", CullEmptyStrings="false"))
    piece, index = g.each("pieces", g.var(P + "Pieces"))
    g.br("brFirst", g.cmp("EqualEqual", index, "0"))
    g.put("first", P + "Out", piece)
    g.put("keepClose", P + "Close", g.val(KSTR + ":FindSubstring", SearchIn=piece, Substring=">"))
    g.br("brClosed", g.cmp("GreaterEqual", g.var(P + "Close"), "0"))
    rest = g.val(KSTR + ":GetSubstring", SourceString=piece, StartIndex=g.add(g.var(P + "Close"), "1"),
                 Length=g.strlen(piece))
    g.put("append", P + "Out", g.cat(g.var(P + "Out"), rest))
    g.flow("entry", "out0", "keepPieces", "pieces.Exec")
    g.flow("pieces.LoopBody", "brFirst", "first")
    g.flow("brFirst.else", "keepClose", "brClosed", "append")
    g.flow("pieces.Completed", "result")
    g.out("Out", g.var(P + "Out"))
    return g.data()


# ============================================================================ DB_Data: "more info" and tip registry
# The setting is the mod's own DB_Settings.MoreInfo in save slot SAVE_SLOT, so it stays after a restart. Not the
# game's bShowUpgradeExtraDetails: that one is transient and the equipment terminal turns it off.
# TipRefs holds soft references: they do not keep a tip alive, so tips of closed windows are garbage collected.

def g_load_settings():
    """Settings = DB_Settings from the save slot, else a new one (written to disk on the first toggle only).
    DoesSaveGameExist first: LoadGameFromSlot logs a warning when the file is missing."""
    g = D()
    g.do("exists", GS + ":DoesSaveGameExist", SlotName=SAVE_SLOT, UserIndex="0")
    g.br("brExists", "@exists.ReturnValue")
    g.do("load", GS + ":LoadGameFromSlot", SlotName=SAVE_SLOT, UserIndex="0")
    g.put("setLoaded", "Settings", g.cast_("asLoaded", SETTINGS_C, "@load.ReturnValue"))
    g.do("create", GS + ":CreateSaveGameObject", SaveGameClass=SETTINGS_C)
    g.put("setNew", "Settings", g.cast_("asNew", SETTINGS_C, "@create.ReturnValue"))
    g.flow("entry", "exists", "brExists", "load", "asLoaded", "setLoaded")
    # No file, or a file that is not a DB_Settings (or unreadable): a new object with the defaults.
    g.ends(["brExists.else", "asLoaded.CastFailed"], "create")
    g.flow("create", "asNew", "setNew")
    return g.data()


def g_more_info():
    """Settings.MoreInfo; false when there are no settings."""
    g = D()
    P = "MoreInfo_"
    g.put("off", P + "On", "false")
    g.br("brSettings", g.valid(g.var("Settings")))
    g.put("set", P + "On", g.var("MoreInfo", SETTINGS_C, g.var("Settings")))
    g.flow("entry", "off", "brSettings", "set", "result")
    g.flow("brSettings.else", "result")
    g.out("On", g.var(P + "On"))
    return g.data()


def g_open_key():
    """Settings.OpenKey; DEFAULT_KEY when there are no settings. No settings yet (BeginPlay has not run): loads them."""
    g = D()
    P = "OpenKey_"
    g.put("dflt", P + "Key", DEFAULT_KEY)
    g.br("brHave", g.valid(g.var("Settings")))
    g.do("load", "LoadSettings")
    g.br("brSettings", g.valid(g.var("Settings")))
    g.put("set", P + "Key", g.var("OpenKey", SETTINGS_C, g.var("Settings")))
    g.flow("entry", "dflt", "brHave", "brSettings", "set", "result")
    g.flow("brHave.else", "load", "brSettings")
    g.flow("brSettings.else", "result")
    g.out("Key", g.var(P + "Key"))
    return g.data()


def g_set_open_key():
    """Settings.OpenKey = Key, saved to the slot (SaveGameToSlot)."""
    g = D()
    g.br("brHave", g.valid(g.var("Settings")))
    g.do("load", "LoadSettings")
    g.br("brSettings", g.valid(g.var("Settings")))
    g.node("mark", "set", var="OpenKey", **{"class": SETTINGS_C})
    g.link(raw(g.var("Settings")), "mark.self")
    g.pins("mark", {"OpenKey": "@entry.Key"})
    g.do("save", GS + ":SaveGameToSlot", SaveGameObject=g.var("Settings"), SlotName=SAVE_SLOT, UserIndex="0")
    g.flow("entry", "brHave", "brSettings", "mark", "save")
    g.flow("brHave.else", "load", "brSettings")
    return g.data()


def g_live_tip():
    """The tip of a TipRefs entry; None when it is gone (collected) or pending kill."""
    g = D()
    P = "LiveTip_"
    g.put("none", P + "Tip")
    g.put("keepObj", P + "Obj", g.val(KSL + ":Conv_SoftObjectReferenceToObject", SoftObject="@entry.Ref"))
    g.br("brObj", g.valid(g.var(P + "Obj")))
    g.put("set", P + "Tip", g.cast_("asTip", TIP_C, g.var(P + "Obj")))
    g.flow("entry", "none", "keepObj", "brObj", "asTip", "set", "result")
    g.ends(["brObj.else", "asTip.CastFailed"], "result")
    g.out("Tip", g.var(P + "Tip"))
    return g.data()


def g_toggle_more_info():
    """Flips Settings.MoreInfo and saves it to the slot, then shows or hides the box of every live tip. No settings
    yet (BeginPlay has not run): loads them first. TipRefs is copied first: ShowExtra is another module's code."""
    g = D()
    P = "ToggleMoreInfo_"
    g.br("brHave", g.valid(g.var("Settings")))
    g.do("load", "LoadSettings")
    g.br("brSettings", g.valid(g.var("Settings")))
    g.put("keepOn", P + "On", g.not_(g.var("MoreInfo", SETTINGS_C, g.var("Settings"))))
    g.node("flip", "set", var="MoreInfo", **{"class": SETTINGS_C})
    g.link(raw(g.var("Settings")), "flip.self")
    g.pins("flip", {"MoreInfo": g.var(P + "On")})
    g.do("save", GS + ":SaveGameToSlot", SaveGameObject=g.var("Settings"), SlotName=SAVE_SLOT, UserIndex="0")
    g.put("keepRefs", P + "Refs", g.var("TipRefs"))
    ref, _ = g.each("tips", g.var(P + "Refs"))
    g.do("live", "LiveTip", Ref=ref)
    g.br("brLive", g.valid("@live.Tip"))
    g.do("show", TIP_C + ":ShowExtra", target="@live.Tip", On=g.var(P + "On"))
    g.flow("entry", "brHave", "brSettings", "keepOn", "flip", "save", "keepRefs", "tips.Exec")
    g.flow("brHave.else", "load", "brSettings")
    g.flow("tips.LoopBody", "live", "brLive", "show")
    return g.data()






def g_register_tip():
    """Adds a tip once. Entries of tips that are gone are dropped here, so the list stays short."""
    g = D()
    P = "RegisterTip_"
    tip = "@entry.Tip"
    g.br("brTip", g.valid(tip))
    g.clear("clearKeep", g.var(P + "Keep"))
    ref, _ = g.each("refs", g.var("TipRefs"))
    g.do("live", "LiveTip", Ref=ref)
    g.br("brKeep", g.and_(g.valid("@live.Tip"), g.not_(g.same("@live.Tip", tip))))
    g.append("keep", g.var(P + "Keep"), ref)
    g.append("addNew", g.var(P + "Keep"), g.val(KSL + ":Conv_ObjectToSoftObjectReference", Object=tip))
    g.put("store", "TipRefs", g.var(P + "Keep"))
    g.flow("entry", "brTip", "clearKeep", "refs.Exec")
    g.flow("refs.LoopBody", "live", "brKeep", "keep")
    g.flow("refs.Completed", "addNew", "store")
    return g.data()


def g_hide_tips():
    """Collapses every live tip (a tooltip shown when the window closes or loses focus would stay on screen)."""
    g = D()
    ref, _ = g.each("tips", g.var("TipRefs"))
    g.do("live", "LiveTip", Ref=ref)
    g.br("brLive", g.valid("@live.Tip"))
    g.do("hide", UMG + "Widget:SetVisibility", target="@live.Tip", InVisibility="Collapsed")
    g.flow("entry", "tips.Exec")
    g.flow("tips.LoopBody", "live", "brLive", "hide")
    return g.data()


# ============================================================================ DB_Data: taking a build

def g_can_take():
    g = D()
    pc = g.val(GS + ":GetPlayerController", PlayerIndex="0")
    g.br("brRig", g.var("IsOnSpaceRig", PC, g.cast_("asPc", PC, pc)))
    g.put("ok", "CanTake_Ok", "true")
    g.put("okReason", "CanTake_Reason", "")
    g.put("no", "CanTake_Ok", "false")
    g.put("noReason", "CanTake_Reason", "Builds can only be taken on the Space Rig.")
    g.flow("entry", "asPc", "brRig", "ok", "okReason", "result")
    g.flow("brRig.else", "no", "noReason", "result")
    g.flow("asPc.CastFailed", "no")
    g.out("Ok", g.var("CanTake_Ok"))
    g.out("Reason", g.var("CanTake_Reason"))
    return g.data()


def g_slot_info():
    """Slots = max(7, length of the class's Loadouts in the save) (More Loadout Slots adds more)."""
    g = D()
    P = "SlotInfo_"
    g.put("count0", P + "Count", "7")
    g.put("current0", P + "Current", "0")
    g.br("brClass", g.valid("@entry.Class"))
    g.put("keepSave", P + "Save", g.val(GFL + ":GetFSDSaveGame"))
    g.br("brSave", g.valid(g.var(P + "Save")))
    save = g.var(P + "Save")
    g.put("setCurrent", P + "Current", g.val(SAVEGAME + ":GetSelectedLoadoutIndex", target=save, characterID="@entry.Class"))
    g.put("keepId", P + "Id", g.val(AFL + ":GetSaveGameIDFromCharacterID", characterID="@entry.Class"))
    g.put("keepSaves", P + "Saves", g.var("CharacterSaves", SAVEGAME, save))
    character, _ = g.each("saves", g.var(P + "Saves"), brk=True)
    fields = g.brk(CHARSAVE, character)
    g.br("brSame", g.val(KGUID + ":EqualEqual_GuidGuid", A=fields("SavegameID"), B=g.var(P + "Id")))
    g.put("setCount", P + "Count", g.max_(g.length(fields("Loadouts")), "7"))
    g.put("fix", P + "Count", g.max_(g.var(P + "Count"), g.add(g.var(P + "Current"), "1")))
    g.flow("entry", "count0", "current0", "brClass", "keepSave", "brSave", "setCurrent", "keepId", "keepSaves",
           "saves.Exec")
    g.flow("saves.LoopBody", "brSame", "setCount", "saves.Break")
    g.flow("saves.Completed", "fix", "result")
    g.ends(["brClass.else", "brSave.else"], "result")
    g.out("Count", g.var(P + "Count"))
    g.out("Current", g.var(P + "Current"))
    return g.data()


def g_apply_code():
    """apply.md section 3: switch to the slot, edit the current loadout, write it back, set the perks (ApplyPerks),
    switch back. The perks go last: SetCurrLoadout writes back the perks it read with the loadout, so perks set
    before it could be overwritten. Code slots this game does not know (DecodeSlot Found = false) are counted first
    (Unknown) and keep the slot's choice; when no slot and no perk of the code is known nothing is touched (known
    perks alone are still applied). Into another slot: after the perks the loadout is read and written once more
    (GetCurrentLoadout, SetCurrLoadout) before switching back, so that slot keeps the new perks."""
    g = D()
    P = "ApplyCode_"
    code, slot = "@entry.Code", "@entry.Slot"
    g.put("applied0", P + "Applied", "0")
    g.put("skipped0", P + "Skipped", "0")
    g.put("unknown0", P + "Unknown", "0")
    g.put("message0", P + "Message", "")
    g.clear("perkSkips0", g.var("ApplyPerks_Skips"))
    g.put("perkUnknown0", "ApplyPerks_Unknown", "0")
    g.do("can", "CanTake")
    g.br("brCan", "@can.Ok")
    g.put("noRig", P + "Message", "@can.Reason")
    g.do("klass", "ClassOfCode", Code=code)
    g.br("brCode", "@klass.Valid")
    g.put("badCode", P + "Message", "This code is not a valid Dwarf Builds code.")
    g.put("keepClass", P + "Class", "@klass.Class")
    g.put("keepSave", P + "Save", g.val(GFL + ":GetFSDSaveGame"))
    g.br("brSave", g.valid(g.var(P + "Save")))
    g.put("noSave", P + "Message", "The save game is not available.")
    g.do("slots", "SlotInfo", Class=g.var(P + "Class"))
    g.br("brSlot", g.and_(g.cmp("GreaterEqual", slot, "0"), g.cmp("Less", slot, "@slots.Count")))
    g.put("badSlot", P + "Message", "This loadout slot does not exist.")
    # Unknown code slots, before anything is changed.
    known = g.fori("known", "0", LAST_SLOT)
    g.do("decode", "DecodeSlot", Code=code, Slot=known)
    g.br("brKnown", "@decode.Found")
    g.incr("countUnknown", P + "Unknown")
    g.flow("known.LoopBody", "decode", "brKnown")
    g.flow("brKnown.else", "countUnknown")
    g.do("codePerks", "PerksOfCode", Code=code)
    g.br("brSome", g.val(KML + ":BooleanOR", A=g.cmp("Less", g.var(P + "Unknown"), str(len(SLOTS))),
                         B="@codePerks.Found"))
    g.put("nothing", P + "Message", "Nothing to apply: this build is not known yet.")
    save, klass = g.var(P + "Save"), g.var(P + "Class")
    g.do("ignoreOn", SAVEGAME + ":SetIgnoreRandomLoadout", target=save, inIgnoreRandomLoadout="true")
    g.put("keepOld", P + "Old", g.val(SAVEGAME + ":GetSelectedLoadoutIndex", target=save, characterID=klass))
    g.br("brSwitch", g.cmp("NotEqual", slot, g.var(P + "Old")))
    g.do("switch", SAVEGAME + ":SetCharacterLoadout", target=save, characterID=klass, loadoutNumber=slot)
    g.do("current", LFL + ":GetCurrentLoadout", PlayerId=klass)
    g.put("keepLoadout", P + "Loadout", "@current.ReturnValue")
    lc = g.brk(LOADOUTCOPY, g.var(P + "Loadout"))
    il = g.brk(ITEMLOADOUT, lc("ItemLoadout"))
    g.put("keepMap", P + "Map", g.brk(UPGRADELOADOUT, lc("UpgradeLoadout"))("Loadout"))
    g.node("guids", "makearray", n=len(SLOTS))
    g.pins("guids", {"[%d]" % k: il(name) for k, name in enumerate(SLOTS)})
    g.put("keepGuids", P + "Guids", "@guids.Array")
    part = g.fori("parts", "0", LAST_SLOT)
    g.do("part", "ApplyPart", Code=code, CodeSlot=part)
    # Write back the seven code slots (pickaxe included) and their selections; flare, icon, perks and vanity stay.
    fields = {name: g.at(g.var(P + "Guids"), str(k)) for k, name in enumerate(SLOTS)}
    fields.update({name: il(name) for name in ("Flare", "iconIndex")})
    items = g.make("items", ITEMLOADOUT, **fields)
    upgrades = g.make("upgrades", UPGRADELOADOUT, Loadout=g.var(P + "Map"))
    g.node("write", "setfields", struct=LOADOUTCOPY, fields=["ItemLoadout", "UpgradeLoadout"])
    g.pins("write", {"StructRef": g.var(P + "Loadout"), "ItemLoadout": items, "UpgradeLoadout": upgrades})
    g.do("setCurrent", LFL + ":SetCurrLoadout", PlayerId=klass, newLoadout=g.var(P + "Loadout"))
    g.br("brBack", g.and_(g.cmp("NotEqual", slot, g.var(P + "Old")), g.not_("@entry.EquipAfter")))
    g.do("again", LFL + ":GetCurrentLoadout", PlayerId=klass)
    g.do("setAgain", LFL + ":SetCurrLoadout", PlayerId=klass, newLoadout="@again.ReturnValue")
    g.do("back", SAVEGAME + ":SetCharacterLoadout", target=save, characterID=klass, loadoutNumber=g.var(P + "Old"))
    # The played class: refresh as the game's loadout menu does when it closes.
    g.do("local", "LocalPS")
    g.br("brLocal", g.valid("@local.PS"))
    g.br("brPlayed", g.same(g.val(PS + ":GetSelectedCharacterID", target="@local.PS"), klass))
    g.do("fromCharacter", SAVEGAME + ":RefreshLoadoutFromCharacter", target=save, characterID=klass)
    comp = g.var("SaveGameStateComponent", PS, "@local.PS")
    g.br("brComp", g.valid(comp))
    g.do("fromSave", SGSC + ":RefreshLoadoutFromSave", target=comp, characterID=klass)
    g.do("disk", SAVEGAME + ":SaveToDisk", target=save)
    g.do("ignoreOff", SAVEGAME + ":SetIgnoreRandomLoadout", target=save, inIgnoreRandomLoadout="false")
    letter = g.val(KSTR + ":GetSubstring", SourceString=LETTERS, StartIndex=slot, Length="1")
    label = g.pick(letter, g.itos(g.add(slot, "1")), g.cmp("Less", slot, str(len(LETTERS))))
    skipped = g.var(P + "Skipped")
    many = g.cat(" ", g.itos(skipped), " parts you do not own were kept as they were.")
    some = g.pick(" 1 part you do not own was kept as it was.", many, g.cmp("EqualEqual", skipped, "1"))
    tail = g.pick("", some, g.cmp("EqualEqual", skipped, "0"))
    unknown = g.var(P + "Unknown")
    many_unknown = g.cat(" ", g.itos(unknown), " parts of the code are unknown and were kept as they were.")
    some_unknown = g.pick(" 1 part of the code is unknown and was kept as it was.", many_unknown,
                          g.cmp("EqualEqual", unknown, "1"))
    tail_unknown = g.pick("", some_unknown, g.cmp("EqualEqual", unknown, "0"))
    skips = g.var("ApplyPerks_Skips")
    perk_list = g.val(KSTR + ":JoinStringArray", SourceArray=skips, Separator=", ")
    tail_perks = g.pick("", g.cat(" Perks not taken: ", perk_list, "."), g.cmp("EqualEqual", g.length(skips), "0"))
    lost = g.var("ApplyPerks_Unknown")
    many_lost = g.cat(" ", g.itos(lost), " perks unknown to this game version were left out.")
    some_lost = g.pick(" 1 perk unknown to this game version was left out.", many_lost, g.cmp("EqualEqual", lost, "1"))
    tail_lost = g.pick("", some_lost, g.cmp("EqualEqual", lost, "0"))
    g.put("done", P + "Message", g.cat("Saved to loadout ", label, ".", tail, tail_unknown, tail_perks, tail_lost))
    g.put("countPerkSkips", P + "Skipped", g.add(g.var(P + "Skipped"), g.length(skips)))
    g.flow("entry", "applied0", "skipped0", "unknown0", "message0", "perkSkips0", "perkUnknown0", "can", "brCan", "klass",
           "brCode", "keepClass", "keepSave", "brSave", "slots", "brSlot", "known")
    g.flow("known.Completed", "codePerks", "brSome", "ignoreOn", "keepOld", "brSwitch", "switch", "current")
    g.flow("brSome.else", "nothing", "result")
    g.flow("brSwitch.else", "current")
    g.flow("current", "keepLoadout", "keepMap", "keepGuids", "parts")
    g.flow("parts.LoopBody", "part")
    g.do("perks", "ApplyPerks", Code=code)
    g.flow("parts.Completed", "write", "setCurrent", "perks", "brBack", "again", "setAgain", "back", "local")
    g.flow("brBack.else", "local")
    g.flow("local", "brLocal", "brPlayed", "fromCharacter", "brComp", "fromSave", "disk")
    g.ends(["brLocal.else", "brPlayed.else", "brComp.else"], "disk")
    # The save changed: columns that show the local player look again (DB_Column.SameAsLast).
    g.incr("bump", "Revision")
    g.do("share", "SendOwn")
    g.flow("disk", "ignoreOff", "done", "countPerkSkips", "bump", "share", "result")
    g.flow("brCan.else", "noRig", "result")
    g.flow("brCode.else", "badCode", "result")
    g.flow("brSave.else", "noSave", "result")
    g.flow("brSlot.else", "badSlot", "result")
    for name in ("Applied", "Skipped", "Message"):
        g.out(name, g.var(P + name))
    return g.data()


def g_apply_part():
    """One code slot into ApplyCode_Guids / ApplyCode_Map. Only owned parts; the rest keeps the slot's choice and
    counts as skipped. An unknown slot (Found = false; ApplyCode counted it) changes nothing. A tier or overclock
    that is 0 in the code is cleared."""
    g = D()
    P, A = "ApplyPart_", "ApplyCode_"
    g.do("decode", "DecodeSlot", Code="@entry.Code", Slot="@entry.CodeSlot")
    g.put("keepItem", P + "Item", "@decode.Item")
    g.put("keepChoices", P + "Choices", "@decode.Choices")
    g.put("keepOc", P + "Overclock", "@decode.Overclock")
    g.br("brFound", "@decode.Found")
    item = g.var(P + "Item")
    g.br("brOwned", g.val(GEARCOMP + ":IsItemOwned", Item=item))
    g.put("keepClass", P + "Class", g.val(ITEMID + ":GetItemClass", target=item))
    g.br("brClass", g.valid_class(g.var(P + "Class")))
    g.incr("skipItem", A + "Skipped")
    g.put("keepGuid", P + "Guid", g.guid(item))
    g.do("setGuid", KARR + ":Array_Set", TargetArray=g.var(A + "Guids"), Index="@entry.CodeSlot",
         Item=g.var(P + "Guid"), bSizeToFit="false")
    g.incr("countItem", A + "Applied")
    g.call("find", KMAP + ":Map_Find", TargetMap=g.var(A + "Map"), Key=g.var(P + "Guid"))
    g.br("brSel", "@find.ReturnValue")
    g.put("oldSel", P + "Sel", "@find.Value")
    g.put("newSel", P + "Sel", g.make("makeSel", SELECTION, WeaponID=g.var(P + "Guid")))
    sel = g.brk(SELECTION, g.var(P + "Sel"))
    g.put("keepUps", P + "Ups", sel("EquippedUpgrades"))
    g.put("keepOcGuid", P + "OcGuid", sel("EquippedOverclock"))
    g.put("keepTiers", P + "Tiers", g.val(GEARCOMP + ":GetItemUpgradeTiers", itemClass=g.var(P + "Class")))
    g.do("pad", KARR + ":Array_Resize", TargetArray=g.var(P + "Choices"),
         Size=g.max_(g.length(g.var(P + "Choices")), g.length(g.var(P + "Tiers"))))
    g.flow("entry", "decode", "keepItem", "keepChoices", "keepOc", "brFound", "brOwned", "keepClass", "brClass",
           "keepGuid", "setGuid", "countItem", "brSel", "oldSel", "keepUps")
    g.flow("brSel.else", "newSel", "keepUps")
    g.flow("keepUps", "keepOcGuid", "keepTiers", "pad", "tiers")
    g.ends(["brOwned.else", "brClass.else"], "skipItem")
    # Upgrades, tier by tier.
    who, klass = g.var(A + "Class"), g.var(P + "Class")
    tier = g.fori("tiers", "0", g.sub(g.length(g.var(P + "Tiers")), "1"))
    g.put("keepTierUps", P + "TierUps", g.brk(UPGRADETIER, g.at(g.var(P + "Tiers"), tier))("upgrades"))
    g.put("keepChoice", P + "Choice", g.at(g.var(P + "Choices"), tier))
    g.br("brNone", g.cmp("LessEqual", g.var(P + "Choice"), "0"))
    g.do("clearNone", "ClearTier")
    g.br("brRange", g.cmp("LessEqual", g.var(P + "Choice"), g.length(g.var(P + "TierUps"))))
    g.put("keepUp", P + "Upgrade", g.at(g.var(P + "TierUps"), g.sub(g.var(P + "Choice"), "1")))
    g.br("brUp", g.valid(g.var(P + "Upgrade")))
    status = g.val(GEARCOMP + ":GetItemUpgradeStatus", itemClass=klass, ItemUpgrade=g.var(P + "Upgrade"),
                   characterID=who)
    unlocked = g.val(GEARCOMP + ":IsTierUnLocked", itemClass=klass, tierIndex=tier, characterID=who)
    g.br("brOwnUp", g.and_(g.owned(status), unlocked))
    g.do("clearUp", "ClearTier")
    g.do("addUp", KARR + ":Array_AddUnique", TargetArray=g.var(P + "Ups"), NewItem=g.guid(g.var(P + "Upgrade")))
    g.incr("countUp", A + "Applied")
    g.incr("skipUp", A + "Skipped")
    g.flow("tiers.LoopBody", "keepTierUps", "keepChoice", "brNone", "clearNone")
    g.flow("brNone.else", "brRange", "keepUp", "brUp", "brOwnUp", "clearUp", "addUp", "countUp")
    g.flow("brOwnUp.else", "skipUp")
    # Overclock: forged and allowed, else the slot's own stays.
    oc = g.var(P + "Overclock")
    g.br("brOc", g.valid(oc))
    g.put("noOc", P + "OcGuid", g.var("ZeroGuid"))
    can = g.and_(g.val(GEARCOMP + ":CanItemOverclock", itemClass=klass),
                 g.val(GEARCOMP + ":IsOverclockingEnabled", characterID=who, itemClass=klass))
    g.br("brCanOc", can)
    equippable = g.val(GEARCOMP + ":GetEquippableOverclocks", itemClass=klass, characterID=who)
    forged = g.val(KARR + ":Array_Contains", TargetArray=equippable, ItemToFind=oc)
    oc_status = g.val(GEARCOMP + ":GetItemUpgradeStatus", itemClass=klass, ItemUpgrade=oc, characterID=who)
    g.br("brForged", g.and_(forged, g.owned(oc_status)))
    g.put("setOc", P + "OcGuid", g.guid(oc))
    g.incr("countOc", A + "Applied")
    g.incr("skipOc", A + "Skipped")
    g.node("write", "setfields", struct=SELECTION, fields=["EquippedUpgrades", "EquippedOverclock"])
    g.pins("write", {"StructRef": g.var(P + "Sel"), "EquippedUpgrades": g.var(P + "Ups"),
                     "EquippedOverclock": g.var(P + "OcGuid")})
    g.do("store", KMAP + ":Map_Add", TargetMap=g.var(A + "Map"), Key=g.var(P + "Guid"), Value=g.var(P + "Sel"))
    g.flow("tiers.Completed", "brOc", "brCanOc", "brForged", "setOc", "countOc", "write", "store")
    g.flow("brOc.else", "noOc", "write")
    g.ends(["brCanOc.else", "brForged.else"], "skipOc")
    g.flow("skipOc", "write")
    return g.data()


def g_apply_perks():
    """The code's perks into the current loadout of ApplyCode_Class (ApplyCode has switched to the target slot and
    written the gear). Per kind (passive, active, proficiency) at most the class's available slots
    (GetPerkEquipSlots). A code perk is taken when it is owned (GetOwnedPerks, for proficiencies also
    GetOwnedPerksByType), a proficiency only when unlocked (FSDSaveGame.HasUnlockProficiency), and only while a slot of
    its kind is free. Free slots then keep the
    slot's own perks, in their order. A code without known perks changes nothing. ApplyPerks_Skips gets
    "<title> (why)" for each code perk not taken; ApplyPerks_Unknown counts the code's perks this game does not
    have."""
    g = D()
    P, A = "ApplyPerks_", "ApplyCode_"
    klass = g.var(A + "Class")
    g.clear("chosen0", g.var(P + "Chosen"))
    g.do("code", "PerksOfCode", Code="@entry.Code")
    g.put("keepCode", P + "Code", "@code.Perks")
    g.put("keepUnknown", P + "Unknown", g.var("PerksOfCode_Unknown"))
    g.br("brAny", "@code.Found")
    hero = g.val(CHARID + ":GetCharacterClass", target=klass)
    g.node("slots", "makearray", n=len(KINDS))
    for k, kind in enumerate(KINDS):
        nid = "slots%d" % k
        g.call(nid, PFL + ":GetPerkEquipSlots", InType=kind, InCharacterClass=hero)
        g.link(nid + ".OutAvailableSlots", "slots.[%d]" % k)
    g.put("keepSlots", P + "Slots", "@slots.Array")
    g.node("used", "makearray", n=len(KINDS))
    g.pins("used", {"[%d]" % k: "0" for k in range(len(KINDS))})
    g.put("keepUsed", P + "Used", "@used.Array")
    g.put("keepOwned", P + "Owned", g.val(PFL + ":GetOwnedPerks"))
    # The game lists proficiencies with GetOwnedPerksByType(Proficiency): count those as owned too.
    g.do("ownedProf", KARR + ":Array_Append", TargetArray=g.var(P + "Owned"),
         SourceArray=g.val(PFL + ":GetOwnedPerksByType", InType="Proficiency"))
    g.put("keepOld", P + "Old", g.val(PFL + ":GetCharacterEquippedPerks", characterID=klass))
    g.flow("entry", "chosen0", "code", "keepCode", "keepUnknown", "brAny", "keepSlots", "keepUsed", "keepOwned", "ownedProf", "keepOld",
           "codePerks.Exec")

    def free(kind):
        return g.cmp("Less", g.at(g.var(P + "Used"), kind), g.at(g.var(P + "Slots"), kind))

    def take(nid, perk, kind):
        """Chosen += perk, Used[kind] += 1. Returns the last node."""
        g.append(nid, g.var(P + "Chosen"), perk)
        g.do(nid + "Used", KARR + ":Array_Set", TargetArray=g.var(P + "Used"), Index=kind,
             Item=g.add(g.at(g.var(P + "Used"), kind), "1"), bSizeToFit="false")
        g.flow(nid, nid + "Used")
        return nid + "Used"

    # The code's perks, in code order.
    perk, _ = g.each("codePerks", g.var(P + "Code"))
    g.put("keepPerk", P + "Perk", perk)
    mine = g.var(P + "Perk")
    g.do("kind", "PerkKind", Perk=mine)
    g.put("keepKind", P + "Kind", "@kind.Kind")
    kind = g.var(P + "Kind")
    g.br("brNew", g.not_(g.val(KARR + ":Array_Contains", TargetArray=g.var(P + "Chosen"), ItemToFind=mine)))
    g.br("brOwned", g.val(KARR + ":Array_Contains", TargetArray=g.var(P + "Owned"), ItemToFind=mine))
    g.br("brFree", free(kind))
    g.br("brProf", g.cmp("EqualEqual", kind, "2"))
    prof = g.cast_("asProf", PROFASSET, mine)
    unlocked = g.val(SAVEGAME + ":HasUnlockProficiency", target=g.var(A + "Save"),
                     Proficiency=g.var("Proficiency", PROFASSET, prof))
    g.br("brUnlocked", unlocked)
    last = take("take", mine, kind)
    g.incr("countTake", A + "Applied")
    g.flow(last, "countTake")
    title = g.ttos(g.var("Title", PERKASSET, mine))
    for name, why in (("NotOwned", "not owned"), ("NoSlot", "no free slot"), ("Locked", "locked")):
        g.append("skip" + name, g.var(P + "Skips"), g.cat(title, " (%s)" % why))
    # Owned, then (proficiency) unlocked, then a free slot: a locked proficiency says "locked", not "no free slot".
    g.flow("codePerks.LoopBody", "keepPerk", "kind", "keepKind", "brNew", "brOwned", "brProf", "asProf",
           "brUnlocked", "brFree", "take")
    g.flow("brProf.else", "brFree")
    # Not a ProficiencyPerkAsset (cannot be checked): only the slot counts.
    g.flow("asProf.CastFailed", "brFree")
    g.flow("brOwned.else", "skipNotOwned")
    g.flow("brFree.else", "skipNoSlot")
    g.flow("brUnlocked.else", "skipLocked")

    # Free slots keep the slot's own perks.
    old, _ = g.each("oldPerks", g.var(P + "Old"))
    g.br("brOld", g.valid(old))
    g.do("oldKind", "PerkKind", Perk=old)
    g.put("keepOldKind", P + "OldKind", "@oldKind.Kind")
    absent = g.not_(g.val(KARR + ":Array_Contains", TargetArray=g.var(P + "Chosen"), ItemToFind=old))
    g.br("brKeep", g.and_(absent, free(g.var(P + "OldKind"))))
    take("keepOldPerk", old, g.var(P + "OldKind"))
    g.flow("codePerks.Completed", "oldPerks.Exec")
    g.flow("oldPerks.LoopBody", "brOld", "oldKind", "keepOldKind", "brKeep", "keepOldPerk")

    # Passive, active, proficiency, then into the loadout.
    g.clear("final0", g.var(P + "Final"))
    g.flow("oldPerks.Completed", "final0", "final0Loop.Exec")
    for k in range(len(KINDS)):
        each, _ = g.each("final%dLoop" % k, g.var(P + "Chosen"))
        g.do("finalKind%d" % k, "PerkKind", Perk=each)
        g.br("brFinal%d" % k, g.cmp("EqualEqual", "@finalKind%d.Kind" % k, str(k)))
        g.append("addFinal%d" % k, g.var(P + "Final"), each)
        g.flow("final%dLoop.LoopBody" % k, "finalKind%d" % k, "brFinal%d" % k, "addFinal%d" % k)
        if k:
            g.flow("final%dLoop.Completed" % (k - 1), "final%dLoop.Exec" % k)
    g.do("set", PERKASSET + ":SetCharacterPerks", characterID=klass, perks=g.var(P + "Final"))
    g.flow("final%dLoop.Completed" % (len(KINDS) - 1), "set")
    return g.data()


def g_clear_tier():
    """Removes the upgrades of ApplyPart_TierUps from ApplyPart_Ups."""
    g = D()
    up, _ = g.each("ups", g.var("ApplyPart_TierUps"))
    g.br("brUp", g.valid(up))
    g.do("remove", KARR + ":Array_RemoveItem", TargetArray=g.var("ApplyPart_Ups"), Item=g.guid(up))
    g.flow("entry", "ups.Exec")
    g.flow("ups.LoopBody", "brUp", "remove")
    return g.data()


TEXTURE_LOADS = [("HexBg", TEX_HEX_BG), ("HexOutline", TEX_HEX_OUTLINE)] + \
    [("OcFrame" + kind, TEX_OC_FRAME[kind]) for kind in ("Clean", "Balanced", "Unstable")]


def share_events(g, after):
    """The sharing part of DB_Data's event graph. After `after` (BeginPlay) and on every ShareCheck (a custom event
    run by the SHARE_SECONDS timer): the world's links again (ShareScan), the game's events bound (binding again
    is harmless: the engine keeps one binding per event), then HostSync on the host or SendOwn on a client.
    The events: for the local player a changed loadout or perks (SaveGameStateComponent), a changed class
    (PlayerState), the end of the class selection (game instance) and the last game window closing (window
    manager: the equipment and perk terminals are windows) run SendOwn; a player joining or leaving (game state)
    runs HostSync. The stubs do not say on which machine and when each of them fires, so none is relied on alone:
    several cover the same change and ShareCheck covers them all. An event only starts a one-shot timer
    (EVENT_DELAY): the game may fire it in the middle of one of this mod's own functions (ApplyCode writes the
    loadout), and SendOwn run right there would overwrite that function's working variables (BPForge has no
    locals). The timer also folds a burst of events into one call. EndPlay unbinds from the game instance, which
    outlives the level. Needs the "me" self node of the graph."""
    g.node("check", "customevent", name="ShareCheck")
    g.do("scan", "ShareScan")
    g.flow(after, "scan")
    g.flow("check", "scan")
    handlers = [  # (node, owner of the delegate, delegate, what runs)
        ("evSelStop", GAMEINSTANCE, "OnCharacterSelectionStop", "SendOwn"),
        ("evWindows", WINDOWMANAGER, "OnLastWindowClosed", "SendOwn"),
        ("evLoadout", SGSC, "OnLoadoutChangedEvent", "SendOwn"),
        ("evPerks", SGSC, "OnEquippedPerksChanged", "SendOwn"),
        ("evClass", PS, "OnSelectedCharacterChanged", "SendOwn"),
        ("evJoined", GAMESTATE, "OnPlayerJoined", "HostSync"),
        ("evLeft", GAMESTATE, "OnPlayerLeave", "HostSync"),
    ]
    owners = {}
    for event, owner, prop, runs in handlers:
        g.node(event, "customevent", name="DB_" + prop, signature="%s:%s" % (owner, prop))
        g.do(event + "Run", KSL + ":K2_SetTimer", Object="@me.self", FunctionName=runs, Time=EVENT_DELAY,
             bLooping="false")
        g.flow(event, event + "Run")
        owners[event] = (owner, prop)

    def bind(event, source, kind="adddelegate"):
        nid = ("bind" if kind == "adddelegate" else "unbind") + event[2:]
        owner, prop = owners[event]
        g.node(nid, kind, name=prop, **{"class": owner})
        g.link(raw(source), nid + ".self")
        g.link(event + ".OutputDelegate", nid + ".Delegate")
        return nid

    instance = g.val(GFL + ":GetFSDGameInstance")
    windows = g.val(GFL + ":GetWindowManager")
    state = g.val(GFL + ":GetFSDGameState")
    g.br("brInstance", g.valid(instance))
    g.br("brWindows", g.valid(windows))
    g.br("brGameState", g.valid(state))
    g.do("hookLocal", "LocalPS")
    local = "@hookLocal.PS"
    g.br("brHookPs", g.valid(local))
    comp = g.var("SaveGameStateComponent", PS, local)
    g.br("brHookComp", g.valid(comp))
    g.br("brHost", g.val(KSL + ":IsServer"))
    g.do("hostSync", "HostSync")
    g.do("sendOwn", "SendOwn")
    g.flow("scan", "brInstance", bind("evSelStop", instance), "brWindows")
    g.flow("brInstance.else", "brWindows")
    g.flow("brWindows", bind("evWindows", windows), "brGameState")
    g.flow("brWindows.else", "brGameState")
    g.flow("brGameState", bind("evJoined", state), bind("evLeft", state), "hookLocal")
    g.flow("brGameState.else", "hookLocal")
    g.flow("hookLocal", "brHookPs", bind("evClass", local), "brHookComp", bind("evLoadout", comp),
           bind("evPerks", comp), "brHost")
    g.ends(["brHookPs.else", "brHookComp.else"], "brHost")
    g.flow("brHost", "hostSync")
    g.flow("brHost.else", "sendOwn")
    g.node("end", "event", name="ReceiveEndPlay", **{"class": ACTOR})
    gone = g.val(GFL + ":GetFSDGameInstance")
    g.br("brEnd", g.valid(gone))
    g.flow("end", "brEnd", bind("evSelStop", gone, "removedelegate"))


def g_data_events():
    """BeginPlay: loads the settings (LoadSettings), starts the ShareCheck timer and runs the check once
    (share_events), then starts an async load (KismetSystemLibrary LoadAsset, as the Async Load Asset node) of
    each texture of TEXTURE_LOADS. Its custom event sets the variable when the load is done; it stays None if it
    fails."""
    g = D()
    g.node("begin", "event", name="ReceiveBeginPlay", **{"class": ACTOR})
    g.node("seq", "seq", n=len(TEXTURE_LOADS) + 1)
    g.do("settings", "LoadSettings")
    g.node("me", "self")
    g.do("shareTimer", KSL + ":K2_SetTimer", Object="@me.self", FunctionName="ShareCheck", Time=SHARE_SECONDS,
         bLooping="true")
    g.flow("begin", "seq")
    g.flow("seq.then_0", "settings", "shareTimer")
    share_events(g, "shareTimer")
    for k, (name, path) in enumerate(TEXTURE_LOADS, 1):
        soft = g.val(KSL + ":Conv_SoftObjPathToSoftObjRef",
                     SoftObjectPath=g.val(KSL + ":MakeSoftObjectPath", PathString=path))
        g.do("load" + name, KSL + ":LoadAsset", Asset=soft)
        g.node("on" + name, "customevent", name="On%sLoaded" % name, signature=KSL + ":LoadAsset:OnLoaded")
        g.link("on%s.OutputDelegate" % name, "load%s.OnLoaded" % name)
        g.put("set" + name, name, g.cast_("as" + name, TEXTURE, "@on%s.Loaded" % name))
        g.flow("seq.then_%d" % k, "load" + name)
        g.flow("on" + name, "as" + name, "set" + name)
    return g.data()


# ============================================================================ DB_BuildShare_v2

def link_set(g, nid, link, name, value=None, default=None):
    """Sets a variable of a link."""
    g.set(nid, name, LINK_C, raw(link), raw(value) if value else None, default)
    return nid


def g_link_for():
    """See contract (LinkFor). LinkMap: the link of each player (Reindex)."""
    g = D()
    P = "LinkFor_"
    player = "@entry.Player"
    g.put("none", P + "Link")
    g.br("brPlayer", g.valid(player))
    g.do("local", "LocalPS")
    g.br("brLocal", g.same(player, "@local.PS"))
    g.call("find", KMAP + ":Map_Find", TargetMap=g.var("LinkMap"), Key=player)
    g.put("keep", P + "Found", "@find.Value")
    found = g.var(P + "Found")
    g.br("brFound", g.valid(found))
    usable = g.val(KML + ":BooleanOR", A=g.not_(g.val(KSL + ":IsServer")), B=g.var("FromPlayer", LINK_C, found))
    g.br("brUsable", g.and_(g.cmp("Greater", g.strlen(g.var("Code", LINK_C, found)), "0"), usable))
    g.put("set", P + "Link", found)
    g.flow("entry", "none", "brPlayer", "local", "brLocal")
    g.flow("brLocal.else", "keep", "brFound", "brUsable", "set", "result")
    g.ends(["brPlayer.else", "brLocal", "brFound.else", "brUsable.else"], "result")
    g.out("Link", g.var(P + "Link"))
    return g.data()


def g_share_scan():
    """Links: every link of this world, found again (the safety net: links also tell DB_Data when they arrive)."""
    g = D()
    g.do("find", GS + ":GetAllActorsOfClass", ActorClass=LINK_C)
    g.clear("clear", g.var("Links"))
    actor, _ = g.each("found", "@find.OutActors")
    g.append("add", g.var("Links"), g.cast_("asLink", LINK_C, actor))
    g.do("reindex", "Reindex")
    g.flow("entry", "find", "clear", "found.Exec")
    g.flow("found.LoopBody", "asLink", "add")
    g.flow("found.Completed", "reindex")
    return g.data()


def g_reindex():
    """LinkMap from Links: player -> their link (the last one wins, so every reader and the host agree); dead links
    leave Links. A link whose player has not reached this machine yet is kept and mapped later (OnRep_Player)."""
    g = D()
    P = "Reindex_"
    g.do("clearMap", KMAP + ":Map_Clear", TargetMap=g.var("LinkMap"))
    g.clear("clearKeep", g.var(P + "Keep"))
    link, _ = g.each("links", g.var("Links"))
    g.br("brLink", g.valid(link))
    g.append("keep", g.var(P + "Keep"), link)
    g.br("brPlayer", g.valid(g.var("Player", LINK_C, link)))
    g.do("map", KMAP + ":Map_Add", TargetMap=g.var("LinkMap"), Key=g.var("Player", LINK_C, link), Value=link)
    g.put("set", "Links", g.var(P + "Keep"))
    g.flow("entry", "clearMap", "clearKeep", "links.Exec")
    g.flow("links.LoopBody", "brLink", "keep", "brPlayer", "map")
    g.flow("links.Completed", "set")
    return g.data()


def g_link_changed():
    """A link tells DB_Data that it is here or that its player is known now (DB_BuildShare_v2.Tell): it joins Links,
    and when it is the local player's own, the build is sent through it at once."""
    g = D()
    link = "@entry.Link"
    g.br("brLink", g.valid(link))
    g.do("add", KARR + ":Array_AddUnique", TargetArray=g.var("Links"), NewItem=link)
    g.do("reindex", "Reindex")
    g.do("local", "LocalPS")
    g.br("brMine", g.and_(g.valid("@local.PS"), g.same(g.var("Player", LINK_C, link), "@local.PS")))
    g.do("own", "SendOwn")
    g.flow("entry", "brLink", "add", "reindex", "local", "brMine", "own")
    return g.data()


def g_send_own():
    """The local player's build into their own link, when it is not there already. The host writes it; a client
    sends it (Server_SetCode) once per code and link, and only through a link it owns (a server RPC needs the
    owner's connection). LocalCode is cheap while the save did not change (SaveCode, CodeOf).
    The write or the RPC is the last step: on the host a link may answer it by calling LinkChanged, which runs this
    function again before the first call returns."""
    g = D()
    P = "SendOwn_"
    g.do("local", "LocalPS")
    g.br("brLocal", g.valid("@local.PS"))
    g.call("find", KMAP + ":Map_Find", TargetMap=g.var("LinkMap"), Key="@local.PS")
    g.put("keepLink", P + "Link", "@find.Value")
    link = g.var(P + "Link")
    g.br("brLink", g.valid(link))
    g.do("code", "LocalCode")
    g.put("keepOwn", P + "Own", "@code.Code")
    own = g.var(P + "Own")
    g.br("brCode", g.cmp("Greater", g.strlen(own), "0"))
    g.br("brServer", g.val(KSL + ":IsServer"))
    g.flow("entry", "local", "brLocal", "keepLink", "brLink", "code", "keepOwn", "brCode", "brServer")
    # The host.
    g.br("brNew", g.val(KSTR + ":NotEqual_StrStr", A=g.var("Code", LINK_C, link), B=own))
    link_set(g, "hostKnown", link, "PerksKnown", default="true")
    link_set(g, "hostFrom", link, "FromPlayer", default="true")
    link_set(g, "hostCode", link, "Code", own)
    g.do("hostPush", ACTOR + ":ForceNetUpdate", target=link)
    g.flow("brServer", "brNew", "hostKnown", "hostFrom", "hostCode", "hostPush")
    # A client.
    owner = g.same(g.val(ACTOR + ":GetOwner", target=link), g.val(GS + ":GetPlayerController", PlayerIndex="0"))
    g.br("brOwner", owner)
    unsent = g.val(KML + ":BooleanOR", A=g.val(KSTR + ":NotEqual_StrStr", A=own, B=g.var("SentCode")),
                   B=g.val(KML + ":NotEqual_ObjectObject", A=link, B=g.var("SentLink")))
    g.br("brSend", unsent)
    g.put("keepSent", "SentCode", own)
    g.put("keepSentLink", "SentLink", link)
    g.do("send", LINK_C + ":Server_SetCode", target=link, NewCode=own)
    g.flow("brServer.else", "brOwner", "brSend", "keepSent", "keepSentLink", "send")
    return g.data()


def g_host_sync():
    """The host: one link per player, owned by the player's controller so the player can send through it; links of
    players who left are destroyed; then the host's own build (SendOwn). Alone: no links are made. A link starts
    empty and stays so for a player without the mod.
    Spawning a link makes it call LinkChanged while this function runs: this function keeps its own variables
    (HostSync_...) and reads LinkMap again for each player."""
    g = D()
    P = "HostSync_"
    g.br("brServer", g.val(KSL + ":IsServer"))
    g.put("keepState", P + "State", g.val(GS + ":GetGameState"))
    g.br("brState", g.valid(g.var(P + "State")))
    g.put("keepPlayers", P + "Players", g.var("PlayerArray", GSBASE, g.var(P + "State")))
    g.br("brMany", g.cmp("Greater", g.length(g.var(P + "Players")), "1"))
    player, _ = g.each("players", g.var(P + "Players"))
    g.put("keepPs", P + "PS", g.cast_("asPs", PS, player))
    ps = g.var(P + "PS")
    g.call("find", KMAP + ":Map_Find", TargetMap=g.var("LinkMap"), Key=ps)
    g.put("keepLink", P + "Link", "@find.Value")
    link = g.var(P + "Link")
    g.put("keepOwner", P + "Owner", g.val(ACTOR + ":GetOwner", target=ps))
    g.br("brHas", g.valid(link))
    g.do("spawn", GS + ":BeginDeferredActorSpawnFromClass", ActorClass=LINK_C,
         SpawnTransform=g.val(KML + ":MakeTransform"), CollisionHandlingOverride="AlwaysSpawn",
         Owner=g.var(P + "Owner"))
    g.put("keepNew", P + "Link", g.cast_("asNew", LINK_C, "@spawn.ReturnValue"))
    link_set(g, "setPlayer", link, "Player", ps)
    g.do("finish", GS + ":FinishSpawningActor", Actor=link, SpawnTransform=g.val(KML + ":MakeTransform"))
    g.do("addNew", KARR + ":Array_AddUnique", TargetArray=g.var("Links"), NewItem=link)
    g.do("mapNew", KMAP + ":Map_Add", TargetMap=g.var("LinkMap"), Key=ps, Value=link)
    moved = g.and_(g.valid(g.var(P + "Owner")),
                   g.val(KML + ":NotEqual_ObjectObject", A=g.val(ACTOR + ":GetOwner", target=link),
                         B=g.var(P + "Owner")))
    g.br("brMoved", moved)
    g.do("setOwner", ACTOR + ":SetOwner", target=link, NewOwner=g.var(P + "Owner"))
    g.do("pushOwner", ACTOR + ":ForceNetUpdate", target=link)
    g.flow("entry", "brServer", "keepState", "brState", "keepPlayers", "brMany", "players.Exec")
    g.flow("players.LoopBody", "asPs", "keepPs", "keepLink", "keepOwner", "brHas")
    g.flow("brHas.else", "spawn", "asNew", "keepNew", "setPlayer", "finish", "addNew", "mapNew")
    g.flow("brHas", "brMoved", "setOwner", "pushOwner")
    # Links of players who left, then the host's own build.
    stale, _ = g.each("stale", g.var("Links"))
    g.br("brStaleOk", g.valid(stale))
    g.br("brStale", g.valid(g.var("Player", LINK_C, stale)))
    g.do("destroy", ACTOR + ":K2_DestroyActor", target=stale)
    g.do("reindex", "Reindex")
    g.do("own", "SendOwn")
    g.ends(["brState.else", "brMany.else", "players.Completed"], "stale.Exec")
    g.flow("stale.LoopBody", "brStaleOk", "brStale")
    g.flow("brStale.else", "destroy")
    g.flow("stale.Completed", "reindex", "own")
    return g.data()


def g_link_tell():
    """Tells this machine's DB_Data about this link (LinkChanged). No DB_Data yet: it finds the link itself when
    it spawns (ShareScan)."""
    g = D()
    g.do("find", GS + ":GetActorOfClass", ActorClass=DATA_C)
    g.node("me", "self")
    g.do("tell", DATA_C + ":LinkChanged", target=g.cast_("asData", DATA_C, "@find.ReturnValue"), Link="@me.self")
    g.flow("entry", "find", "asData", "tell")
    return g.data()


def g_link_on_rep_player():
    """Player reached this machine (on a client the player state may come after the link)."""
    g = D()
    g.do("tell", "Tell")
    g.flow("entry", "tell")
    return g.data()


def g_link_events():
    """BeginPlay (on every machine the link reaches): Tell.
    Server_SetCode(NewCode): a reliable server RPC (a custom event), so it runs on the host and only when the
    link's owner calls it: the engine sends a server RPC through the owner's connection. Ignored: a code that does
    not start with DB1:, is longer than any build, or holds a character no build code has (CODE_CHARS), so a
    player cannot put arbitrary text into what others copy with COPY CODE. The readers parse the rest like a
    pasted code. The code is set last and pushed to the clients at once (the link itself replicates rarely)."""
    g = D()
    g.node("begin", "event", name="ReceiveBeginPlay", **{"class": ACTOR})
    g.do("tell", "Tell")
    g.flow("begin", "tell")
    g.node("set", "customevent", name="Server_SetCode", net="server", reliable=True, outputs=[t("NewCode", S)])
    code = "@set.NewCode"
    ok = g.and_(g.cmp("LessEqual", g.strlen(code), CODE_MAX),
                g.val(KSTR + ":StartsWith", SourceString=code, InPrefix=CODE_VERSION + ":", SearchCase="CaseSensitive"))
    g.br("brOk", ok)
    g.put("keepChars", "SetCode_Chars", g.val(KSTR + ":GetCharacterArrayFromString", SourceString=code))
    g.put("clean", "SetCode_Clean", "true")
    char, _ = g.each("chars", g.var("SetCode_Chars"), brk=True)
    g.br("brChar", g.cmp("GreaterEqual",
                         g.val(KSTR + ":FindSubstring", SearchIn=CODE_CHARS, Substring=char, bUseCase="true"), "0"))
    g.put("dirty", "SetCode_Clean", "false")
    g.br("brClean", g.var("SetCode_Clean"))
    g.put("known", "PerksKnown", "true")
    g.put("fromPlayer", "FromPlayer", "true")
    g.put("setCode", "Code", code)
    g.do("push", ACTOR + ":ForceNetUpdate")
    g.flow("set", "brOk", "keepChars", "clean", "chars.Exec")
    g.flow("chars.LoopBody", "brChar")
    g.flow("brChar.else", "dirty", "chars.Break")
    g.flow("chars.Completed", "brClean", "known", "fromPlayer", "setCode", "push")
    return g.data()


# ============================================================================ DB_PerkShare_v1

def g_share_find():
    """Entry k: player Ids[k] with class Classes[k]; its perks are Counts[k] items after those of the entries before."""
    g = D()
    P = "Find_"
    g.clear("perks0", g.var(P + "Perks"))
    g.clear("ranks0", g.var(P + "Ranks"))
    g.put("found0", P + "Found", "false")
    g.put("offset0", P + "Offset", "0")
    pid, k = g.each("ids", g.var("Ids"), brk=True)
    g.br("brCount", g.cmp("Less", k, g.length(g.var("Counts"))))
    g.put("setCount", P + "Count", g.at(g.var("Counts"), k))
    g.put("noCount", P + "Count", "0")
    # An entry without its class or count (arrays not fully replicated yet) does not match.
    known = g.and_(g.cmp("Less", k, g.length(g.var("Classes"))), g.cmp("Less", k, g.length(g.var("Counts"))))
    g.br("brId", g.and_(g.cmp("EqualEqual", pid, "@entry.PlayerId"), known))
    g.br("brClass", g.same(g.at(g.var("Classes"), k), "@entry.Class"))
    j = g.fori("copy", "0", g.sub(g.var(P + "Count"), "1"))
    index = g.add(g.var(P + "Offset"), j)
    g.br("brIndex", g.and_(g.cmp("Less", index, g.length(g.var("Perks"))), g.cmp("Less", index, g.length(g.var("Ranks")))))
    g.append("addPerk", g.var(P + "Perks"), g.at(g.var("Perks"), index))
    g.append("addRank", g.var(P + "Ranks"), g.at(g.var("Ranks"), index))
    g.put("setFound", P + "Found", "true")
    g.put("next", P + "Offset", g.add(g.var(P + "Offset"), g.var(P + "Count")))
    g.flow("entry", "perks0", "ranks0", "found0", "offset0", "ids.Exec")
    g.flow("ids.LoopBody", "brCount", "setCount", "brId", "brClass", "copy")
    g.flow("brCount.else", "noCount", "brId")
    g.flow("copy.LoopBody", "brIndex", "addPerk", "addRank")
    g.flow("copy.Completed", "setFound", "ids.Break")
    g.ends(["brId.else", "brClass.else"], "next")
    g.flow("ids.Completed", "result")
    g.out("Perks", g.var(P + "Perks"))
    g.out("Ranks", g.var(P + "Ranks"))
    g.out("Found", g.var(P + "Found"))
    return g.data()


def g_share_collect():
    """Server: every player's class and equipped perks into the replicated arrays. The host's own perks come from
    the save; the others' from SaveGameStateComponent.EquippedPerks. Unchanged values are not sent again.
    Solo (one player): nothing to share, no work."""
    g = D()
    P = "Collect_"
    names = ("Ids", "Classes", "Perks", "Ranks", "Counts")
    g.put("keepState", P + "State", g.val(GS + ":GetGameState"))
    g.br("brState", g.valid(g.var(P + "State")))
    g.put("keepPlayers", P + "Players", g.var("PlayerArray", GSBASE, g.var(P + "State")))
    g.br("brMany", g.cmp("Greater", g.length(g.var(P + "Players")), "1"))
    for name in names:
        g.clear("clear" + name, g.var(P + name))
    g.put("local0", P + "Local")
    pc = g.val(GS + ":GetPlayerController", PlayerIndex="0")
    g.br("brPc", g.valid(pc))
    g.put("setLocal", P + "Local", g.var("PlayerState", CONTROLLER, pc))
    g.flow("entry", "keepState", "brState", "keepPlayers", "brMany", *["clear" + name for name in names])
    g.flow("clearCounts", "local0", "brPc", "setLocal", "players.Exec")
    g.flow("brPc.else", "players.Exec")
    player, _ = g.each("players", g.var(P + "Players"))
    g.put("keepPs", P + "PS", g.cast_("asPs", PS, player))
    ps = g.var(P + "PS")
    g.put("keepClass", P + "Class", g.val(PS + ":GetSelectedCharacterID", target=ps))
    g.br("brClass", g.valid(g.var(P + "Class")))
    g.put("keepStart", P + "Start", g.length(g.var(P + "Perks")))
    g.br("brLocal", g.same(ps, g.var(P + "Local")))
    g.flow("players.LoopBody", "asPs", "keepPs", "keepClass", "brClass", "keepStart", "brLocal", "keepOwn", "own.Exec")
    # The host's own perks: the save.
    g.put("keepOwn", P + "Own", g.val(PFL + ":GetCharacterEquippedPerks", characterID=g.var(P + "Class")))
    perk, _ = g.each("own", g.var(P + "Own"))
    g.br("brOwn", g.valid(perk))
    g.append("addOwn", g.var(P + "Perks"), perk)
    g.append("addOwnRank", g.var(P + "Ranks"), g.val(PERKASSET + ":GetCurrentRank", target=perk))
    g.flow("own.LoopBody", "brOwn", "addOwn", "addOwnRank")
    g.flow("own.Completed", "addId")
    # Other players: what their client sent to the server.
    comp = g.var("SaveGameStateComponent", PS, ps)
    g.br("brComp", g.valid(comp))
    g.put("keepItems", P + "Items", g.var("EquippedPerks", SGSC, comp))
    item, _ = g.each("items", g.var(P + "Items"))
    fields = g.brk(PERKITEM, item)
    g.br("brItem", g.valid(fields("Perk")))
    g.append("addItem", g.var(P + "Perks"), fields("Perk"))
    g.append("addItemRank", g.var(P + "Ranks"), g.val(KML + ":Conv_ByteToInt", InByte=fields("Rank")))
    g.flow("brLocal.else", "brComp", "keepItems", "items.Exec")
    g.flow("items.LoopBody", "brItem", "addItem", "addItemRank")
    g.ends(["items.Completed", "brComp.else"], "addId")
    # The entry.
    g.append("addId", g.var(P + "Ids"), g.var("PlayerId", PLAYERSTATE, ps))
    g.append("addClass", g.var(P + "Classes"), g.var(P + "Class"))
    g.append("addCount", g.var(P + "Counts"), g.sub(g.length(g.var(P + "Perks")), g.var(P + "Start")))
    g.flow("addId", "addClass", "addCount")
    # Publish.
    publish = []
    for name in names:
        publish.append(g.put("publish" + name, name, g.var(P + name)))
    g.flow("players.Completed", *publish)
    return g.data()


def g_share_events():
    g = D()
    g.node("begin", "event", name="ReceiveBeginPlay", **{"class": ACTOR})
    g.br("brAuthority", g.and_(g.val(ACTOR + ":HasAuthority"), g.val(KSL + ":IsServer")))
    g.node("me", "self")
    g.do("timer", KSL + ":K2_SetTimer", Object="@me.self", FunctionName="Collect", Time="3.0", bLooping="true")
    g.do("collect", "Collect")
    g.flow("begin", "brAuthority", "timer", "collect")
    return g.data()


# ============================================================================ module interface

def _data_members():
    sel_map = {"type": "struct", "class": SELECTION}
    variables = [
        t("ZeroGuid", "struct", GUID), t("ZeroSel", "struct", SELECTION),
        # Overclock frames by type, loaded at BeginPlay (None until loaded).
        obj("OcFrameClean", TEXTURE), obj("OcFrameBalanced", TEXTURE), obj("OcFrameUnstable", TEXTURE),
        obj("LocalPS_PS", PS),
        obj("SlotItems_List", INVLIST), obj("SlotItems_Items", ITEMID, array=True), t("SlotItems_Ids", "struct", GUID, array=True),
        obj("GearOf_Gear", GEARCOMP), t("GearOf_Class", "class", ITEM),
        obj("OverclocksOf_List", OVERCLOCK, array=True), obj("OverclocksOf_Gear", GEARCOMP), obj("OverclocksOf_Bank", OCBANK),
        t("EncodePart_Digits", S), t("EncodePart_OC", I), t("EncodePart_Class", "class", ITEM),
        t("EncodePart_Tiers", "struct", UPGRADETIER, array=True), t("EncodePart_Equipped", "struct", GUID, array=True),
        t("EncodePart_Digit", I), obj("EncodePart_Ups", UPGRADE, array=True), obj("EncodePart_OCs", OVERCLOCK, array=True),
        t("EncodePart_Part", S),
        t("SaveCode_Loadout", "struct", LOADOUTCOPY), t("SaveCode_Map", "struct", GUID, map=sel_map),
        t("SaveCode_Guids", "struct", GUID, array=True), t("SaveCode_Code", S), obj("SaveCode_Items", ITEMID, array=True),
        t("SaveCode_Ids", "struct", GUID, array=True), t("SaveCode_Found", I), obj("SaveCode_Item", ITEMID),
        t("RemoteCode_Sels", "struct", SELECTION, array=True), t("RemoteCode_Code", S),
        obj("RemoteCode_Items", ITEMID, array=True), t("RemoteCode_Ids", "struct", GUID, array=True),
        t("RemoteCode_Found", I), obj("RemoteCode_Item", ITEMID), t("RemoteCode_Sel", "struct", SELECTION),
        t("RemoteCode_Any", B),
        t("CodeOf_Code", S), obj("CodeOf_Class", CHARID), obj("CodeOf_Perks", PERKASSET, array=True),
        # Perk IDs: names from perk_ids.json and the perk asset of each (None when this game has no such perk).
        t("PerkNames", S, array=True), obj("PerkTable", PERKASSET, array=True), t("PerkTableDone", B),
        obj("PerkTable_All", PERKASSET, array=True), t("PerkTable_Index", I), t("PerkId_Id", I),
        t("PerksPart_Part", S), obj("PerksPart_Perks", PERKASSET, array=True),
        t("PerkIds_Ids", I, array=True), t("PerkIds_Pieces", S, array=True), t("PerkIds_Id", I),
        obj("PerksOfCode_Perks", PERKASSET, array=True), t("PerksOfCode_Ranks", I, array=True),
        t("PerksOfCode_Ids", I, array=True), obj("PerksOfCode_Perk", PERKASSET), t("PerksOfCode_Rank", I),
        t("PerkIds_Bad", I), t("PerksOfCode_Unknown", I),
        t("LocalCode_Code", S),
        t("ParseCode_Code", S), t("ParseCode_Parts", S, array=True), t("ParseCode_Valid", B), obj("ParseCode_Class", CHARID),
        obj("ParseCode_Data", GAMEDATA), obj("ParseCode_Settings", CHARSETTINGS), obj("ParseCode_IDs", CHARID, array=True),
        obj("DecodeSlot_Item", ITEMID), obj("DecodeSlot_Overclock", OVERCLOCK), t("DecodeSlot_Digits", S),
        t("DecodeSlot_Found", B), t("DecodeSlot_Choices", I, array=True), t("DecodeSlot_Sub", S, array=True),
        obj("DecodeSlot_Items", ITEMID, array=True), t("DecodeSlot_Index", I), t("DecodeSlot_Class", "class", ITEM),
        t("DecodeSlot_Tiers", "struct", UPGRADETIER, array=True), t("DecodeSlot_TierText", S), t("DecodeSlot_Digit", I),
        t("DecodeSlot_Choice", I), t("DecodeSlot_OcIndex", I), obj("DecodeSlot_OCs", OVERCLOCK, array=True),
        obj("TierOptions_Upgrades", UPGRADE, array=True), t("TierOptions_Class", "class", ITEM),
        t("TierOptions_Tiers", "struct", UPGRADETIER, array=True),
        obj("GetPlayers_State", GAMESTATE), obj("GetPlayers_Players", PS, array=True),
        t("HeaderOf_Name", S), t("HeaderOf_Sub", S), t("HeaderOf_Color", "struct", LINEAR), obj("HeaderOf_Icon", TEXTURE),
        t("HeaderOf_IsYou", B), t("HeaderOf_IsHost", B), obj("HeaderOf_Class", CHARID), t("HeaderOf_Promos", I),
        t("HeaderOf_Hero", "class", PLAYERCHAR),
        t("HeaderOfCode_Sub", S), t("HeaderOfCode_Color", "struct", LINEAR), obj("HeaderOfCode_Icon", TEXTURE),
        t("HeaderOfCode_Hero", "class", PLAYERCHAR),
        obj("PerksOf_Perks", PERKASSET, array=True), t("PerksOf_Ranks", I, array=True), t("PerksOf_State", I),
        obj("PerksOf_Class", CHARID), obj("PerksOf_Own", PERKASSET, array=True),
        t("PerksOf_Items", "struct", PERKITEM, array=True),
        # DB_BuildShare_v2. Links: every link in this world; LinkMap: player -> link (Reindex); SentCode, SentLink:
        # what this client last sent and through which link. (PerksOf_Share is public: contract.)
        obj("Links", LINK_C, array=True), t("LinkMap", "object", PS, map={"type": "object", "class": LINK_C}),
        t("SentCode", S), obj("SentLink", LINK_C), obj("LinkFor_Link", LINK_C), obj("LinkFor_Found", LINK_C),
        obj("Reindex_Keep", LINK_C, array=True), obj("SendOwn_Link", LINK_C), t("SendOwn_Own", S),
        obj("HostSync_State", GSBASE), obj("HostSync_Players", PLAYERSTATE, array=True), obj("HostSync_PS", PS),
        obj("HostSync_Link", LINK_C), obj("HostSync_Owner", ACTOR), obj("PerksOf_Link", LINK_C),
        # What SaveCode and CodeOf last worked a code out from (they return the last code while it is the same).
        obj("SaveCode_LastClass", CHARID), t("SaveCode_LastGuids", "struct", GUID, array=True),
        t("SaveCode_LastKeys", "struct", GUID, array=True), t("SaveCode_LastVals", "struct", SELECTION, array=True),
        t("CodeOf_Local", B), obj("CodeOf_Now", PERKASSET, array=True), obj("CodeOf_LastPerks", PERKASSET, array=True),
        t("CodeOf_Gear", S), t("CodeOf_LastGear", S), t("CodeOf_LastFull", S),
        obj("SortPerks_Perks", PERKASSET, array=True), t("SortPerks_Ranks", I, array=True),
        t("ItemTexts_Name", TX), t("ItemTexts_Category", TX), t("ItemTexts_Description", TX),
        obj("ItemTexts_Line", TEXTURE), obj("ItemTexts_Fill", TEXTURE), obj("ItemTexts_Data", ITEMDATA),
        obj("ItemTexts_Gear", GEARCOMP),
        t("StatBody_Text", S), t("StatBody_Stats", "struct", STATTEXT, array=True), t("StatBody_Line", S),
        t("UpgradeTip_Title", TX), t("UpgradeTip_Category", TX), t("UpgradeTip_Body", TX), obj("UpgradeTip_Icon", TEXTURE),
        obj("UpgradeTip_Cat", UPGCAT), t("UpgradeTip_ExtraTitle", TX), t("UpgradeTip_Extra", TX),
        # Registered tips (soft references: they do not keep a tip alive).
        t("TipRefs", "softobject", OBJECT, array=True), t("RegisterTip_Keep", "softobject", OBJECT, array=True),
        t("ToggleMoreInfo_Refs", "softobject", OBJECT, array=True), t("ToggleMoreInfo_On", B), t("MoreInfo_On", B),
        t("OpenKey_Key", "struct", KEY),
        # The mod's settings (LoadSettings at BeginPlay).
        obj("Settings", SETTINGS_C),
        obj("LiveTip_Obj", OBJECT), obj("LiveTip_Tip", TIP_C),
        t("OverclockTip_Title", TX), t("OverclockTip_Body", TX), t("OverclockTip_CatText", S), t("OverclockTip_CatName", S),
        t("OverclockTip_Key", S), obj("OverclockTip_TypeFrame", TEXTURE), obj("OverclockTip_Icon", TEXTURE),
        t("OverclockTip_Color", "struct", LINEAR), obj("OverclockTip_Frame", TEXTURE), obj("OverclockTip_Cat", UPGCAT),
        obj("OverclockTip_Scat", SCHEMCAT),
        t("PerkTip_Title", TX), t("PerkTip_Category", TX), t("PerkTip_Body", TX), obj("PerkTip_Icon", TEXTURE),
        t("PerkTip_Color", "struct", LINEAR),
        t("StripTags_Out", S), t("StripTags_Pieces", S, array=True), t("StripTags_Close", I),
        t("CanTake_Ok", B), t("CanTake_Reason", S),
        t("SlotInfo_Count", I), t("SlotInfo_Current", I), obj("SlotInfo_Save", SAVEGAME), t("SlotInfo_Id", "struct", GUID),
        t("SlotInfo_Saves", "struct", CHARSAVE, array=True),
        t("ApplyCode_Applied", I), t("ApplyCode_Skipped", I), t("ApplyCode_Unknown", I), t("ApplyCode_Message", S),
        obj("ApplyCode_Class", CHARID),
        obj("ApplyCode_Save", SAVEGAME), t("ApplyCode_Old", I), t("ApplyCode_Loadout", "struct", LOADOUTCOPY),
        t("ApplyCode_Map", "struct", GUID, map=sel_map), t("ApplyCode_Guids", "struct", GUID, array=True),
        obj("ApplyPart_Item", ITEMID), t("ApplyPart_Choices", I, array=True), obj("ApplyPart_Overclock", OVERCLOCK),
        t("ApplyPart_Class", "class", ITEM), t("ApplyPart_Guid", "struct", GUID), t("ApplyPart_Sel", "struct", SELECTION),
        t("ApplyPart_Ups", "struct", GUID, array=True), t("ApplyPart_OcGuid", "struct", GUID),
        t("ApplyPart_Tiers", "struct", UPGRADETIER, array=True), obj("ApplyPart_TierUps", UPGRADE, array=True),
        t("ApplyPart_Choice", I), obj("ApplyPart_Upgrade", UPGRADE),
        obj("ApplyPerks_Code", PERKASSET, array=True), obj("ApplyPerks_Chosen", PERKASSET, array=True),
        obj("ApplyPerks_Owned", PERKASSET, array=True), obj("ApplyPerks_Old", PERKASSET, array=True),
        obj("ApplyPerks_Final", PERKASSET, array=True), obj("ApplyPerks_Perk", PERKASSET),
        t("ApplyPerks_Slots", I, array=True), t("ApplyPerks_Used", I, array=True), t("ApplyPerks_Kind", I),
        t("ApplyPerks_OldKind", I), t("ApplyPerks_Skips", S, array=True), t("ApplyPerks_Unknown", I),
    ]
    functions = [
        {"name": "ClassLetter", "inputs": [obj("Class", CHARID)], "outputs": [t("Letter", S), t("Name", S)]},
        {"name": "SlotItems", "inputs": [obj("Class", CHARID), t("Slot", I)],
         "outputs": [obj("Items", ITEMID, array=True), t("Ids", "struct", GUID, array=True)]},
        {"name": "GearOf", "inputs": [obj("Item", ITEMID)], "outputs": [obj("Gear", GEARCOMP)]},
        {"name": "OverclocksOf", "inputs": [obj("Item", ITEMID)], "outputs": [obj("Overclocks", OVERCLOCK, array=True)]},
        {"name": "EncodePart", "inputs": [obj("Item", ITEMID), t("Index", I), t("Sel", "struct", SELECTION)],
         "outputs": [t("Part", S)]},
        {"name": "SaveCode", "inputs": [obj("Class", CHARID)], "outputs": [t("Code", S)]},
        {"name": "RemoteCode", "inputs": [obj("Player", PS), obj("Class", CHARID)], "outputs": [t("Code", S)]},
        {"name": "ParseCode", "inputs": [t("Code", S)], "outputs": [t("Valid", B)]},
        {"name": "SortPerks"},
        {"name": "ItemTexts", "inputs": [obj("Item", ITEMID)],
         "outputs": [t("Name", TX), t("Category", TX), t("Description", TX), obj("Line", TEXTURE), obj("Fill", TEXTURE)]},
        {"name": "StatBody", "inputs": [obj("Upgrade", UPGRADE)], "outputs": [t("Body", TX)]},
        {"name": "StripTags", "inputs": [t("Source", S)], "outputs": [t("Out", S)]},
        {"name": "ApplyPart", "inputs": [t("Code", S), t("CodeSlot", I)]},
        {"name": "ApplyPerks", "inputs": [t("Code", S)]},
        {"name": "EnsurePerkNames"}, {"name": "EnsurePerkTable"},
        {"name": "PerkId", "inputs": [obj("Perk", PERKASSET)], "outputs": [t("Id", I)]},
        {"name": "PerksPart", "inputs": [obj("Perks", PERKASSET, array=True)], "outputs": [t("Part", S)]},
        {"name": "PerkIds", "inputs": [t("Part", S)], "outputs": [t("Ids", I, array=True)]},
        {"name": "PerkKind", "inputs": [obj("Perk", PERKASSET)], "outputs": [t("Kind", I)]},
        {"name": "ClearTier"},
        {"name": "LiveTip", "inputs": [t("Ref", "softobject", OBJECT)], "outputs": [obj("Tip", TIP_C)]},
        {"name": "LoadSettings"},
        {"name": "ShareScan"}, {"name": "Reindex"}, {"name": "SendOwn"}, {"name": "HostSync"},
        {"name": "LinkChanged", "inputs": [obj("Link", LINK_C)]},
    ]
    return {"variables": variables, "functions": functions}


def _share_members():
    variables = [
        t("Find_Perks", "object", PERKASSET, array=True), t("Find_Ranks", I, array=True), t("Find_Found", B),
        t("Find_Offset", I), t("Find_Count", I),
        t("Collect_Ids", I, array=True), obj("Collect_Classes", CHARID, array=True),
        obj("Collect_Perks", PERKASSET, array=True), t("Collect_Ranks", I, array=True), t("Collect_Counts", I, array=True),
        obj("Collect_State", GSBASE), obj("Collect_Players", PLAYERSTATE, array=True), obj("Collect_Local", PLAYERSTATE),
        obj("Collect_PS", PS), obj("Collect_Class", CHARID), t("Collect_Start", I),
        obj("Collect_Own", PERKASSET, array=True), t("Collect_Items", "struct", PERKITEM, array=True),
    ]
    return {"variables": variables, "functions": [{"name": "Collect"}]}


def _link_members():
    """Server_SetCode's working values; Tell and the RepNotify of Player (contract)."""
    return {"variables": [t("SetCode_Chars", S, array=True), t("SetCode_Clean", B)],
            "functions": [{"name": "Tell"}, {"name": "OnRep_Player"}]}


def members():
    return {DATA: _data_members(), SHARE: _share_members(), LINK: _link_members()}


def graphs():
    data = {
        "EventGraph": g_data_events(),
        "LocalPS": g_local_ps(), "ClassLetter": g_class_letter(), "SlotItems": g_slot_items(), "GearOf": g_gear_of(),
        "OverclocksOf": g_overclocks_of(), "EncodePart": g_encode_part(), "SaveCode": g_save_code(),
        "RemoteCode": g_remote_code(), "ParseCode": g_parse_code(), "SortPerks": g_sort_perks(),
        "ItemTexts": g_item_texts(), "StatBody": g_stat_body(), "StripTags": g_strip_tags(),
        "ApplyPart": g_apply_part(), "ClearTier": g_clear_tier(), "ApplyPerks": g_apply_perks(),
        "EnsurePerkNames": g_ensure_perk_names(), "EnsurePerkTable": g_ensure_perk_table(), "PerkId": g_perk_id(),
        "PerksPart": g_perks_part(), "PerkIds": g_perk_ids(), "PerkKind": g_perk_kind(),
        "PerksOfCode": g_perks_of_code(),
        "GetPlayers": g_get_players(), "CodeOf": g_code_of(), "LocalCode": g_local_code(), "HeaderOf": g_header_of(),
        "HeaderOfCode": g_header_of_code(), "PerksOf": g_perks_of(), "ClassOfCode": g_class_of_code(),
        "DecodeSlot": g_decode_slot(), "TierOptions": g_tier_options(), "ItemVisual": g_item_visual(),
        "ItemTip": g_item_tip(), "UpgradeTip": g_upgrade_tip(), "OverclockTip": g_overclock_tip(),
        "PerkTip": g_perk_tip(), "CanTake": g_can_take(), "SlotInfo": g_slot_info(), "ApplyCode": g_apply_code(),
        "MoreInfo": g_more_info(), "ToggleMoreInfo": g_toggle_more_info(),
        "OpenKey": g_open_key(), "SetOpenKey": g_set_open_key(), "RegisterTip": g_register_tip(),
        "HideTips": g_hide_tips(), "LiveTip": g_live_tip(), "LoadSettings": g_load_settings(),
        "LinkFor": g_link_for(), "ShareScan": g_share_scan(), "Reindex": g_reindex(), "SendOwn": g_send_own(),
        "HostSync": g_host_sync(), "LinkChanged": g_link_changed(),
        
    }
    share = {"EventGraph": g_share_events(), "Find": g_share_find(), "Collect": g_share_collect()}
    link = {"EventGraph": g_link_events(), "Tell": g_link_tell(), "OnRep_Player": g_link_on_rep_player()}
    return {DATA: data, SHARE: share, LINK: link}


def class_defaults():
    net = {"bReplicates": "True", "bAlwaysRelevant": "True", "NetUpdateFrequency": "2.0"}
    # A link changes a few times a session and every change is pushed (ForceNetUpdate), so the engine need not look
    # at each link for each connection twice a second.
    return {SHARE: net, LINK: dict(net, NetUpdateFrequency="0.5")}
