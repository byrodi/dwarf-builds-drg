"""Writes the BPForge spec (JSON) of the Dwarf Builds mod.

Usage: python Tools/dwarfbuilds_spec.py <out.json> [--only data|widgets|shell|scan|hub] [--transient]
The mod is split into modules (Tools/dwarfbuilds/<module>.py), each owning some assets (contract.ASSETS).
A module may define: trees() -> {path: widget tree}, members() -> {path: {"variables", "functions"}} (private),
graphs() -> {path: {graph name: graph}}, class_defaults() -> {path: {property: value}}.
--only <module> keeps the trees, private members and graphs of that module only (the others' assets are
declared with their public members and empty bodies), so one module can be compiled while others change.
"""
import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dwarfbuilds import contract  # noqa: E402

MODULES = ["data", "widgets", "shell", "scan", "hub"]


def load(name):
    try:
        return importlib.import_module("dwarfbuilds." + name)
    except ModuleNotFoundError as error:
        if error.name == "dwarfbuilds." + name:
            return None
        raise


def part(module, fn):
    if module is None or not hasattr(module, fn):
        return {}
    return getattr(module, fn)()


def build(only=None, transient=False):
    parts = {}
    for name in MODULES:
        module = load(name) if only in (None, name) else None
        parts[name] = {fn: part(module, fn) for fn in ("trees", "members", "graphs", "class_defaults")}

    def owned(path, fn):
        return parts[contract.ASSETS[path][2]][fn].get(path)

    assets = []
    for path in contract.DECLARE_ORDER:
        kind, parent, _ = contract.ASSETS[path]
        entry = {"kind": kind, "path": path, "parent": parent}
        if path in contract.INTERFACES:
            entry["interfaces"] = contract.INTERFACES[path]
        tree = owned(path, "trees")
        if tree:
            entry["tree"] = tree
        defaults = owned(path, "class_defaults")
        if defaults:
            entry["class_defaults"] = defaults
        if transient:
            entry["transient"] = True
        assets.append(entry)
    for path in contract.DECLARE_ORDER:
        public = contract.PUBLIC.get(path, {})
        private = owned(path, "members") or {}
        variables = public.get("variables", []) + private.get("variables", [])
        functions = public.get("functions", []) + private.get("functions", [])
        if variables or functions:
            assets.append({"kind": "members", "path": path, "variables": variables, "functions": functions})
    for path in contract.DECLARE_ORDER:
        graphs = owned(path, "graphs")
        if graphs:
            assets.append({"kind": "graphs", "path": path, "graphs": graphs})
    return assets


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        only = args[args.index("--only") + 1]
        del args[args.index("--only"):args.index("--only") + 2]
        if only not in MODULES:
            sys.exit("--only takes one of " + ", ".join(MODULES))
    transient = "--transient" in args
    args = [a for a in args if a != "--transient"]
    if len(args) != 1:
        sys.exit(__doc__)
    assets = build(only, transient)
    with open(args[0], "w", encoding="utf-8") as out:
        json.dump({"assets": assets}, out, indent=1)
    print("wrote %s (%d entries)" % (args[0], len(assets)))


if __name__ == "__main__":
    main()
