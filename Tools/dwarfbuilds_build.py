"""Builds the Dwarf Builds Blueprints with the BPForge editor plugin.

Usage: python Tools/dwarfbuilds_build.py [--only data|widgets|shell|scan|hub] [--save] [--dev]
--dev makes a dev build (common.DEV: test helpers, version ...-dev). Never release or upload one.
Without --save every asset is transient: it compiles and nothing is written (a check).
--save regenerates Content/_DwarfBuilds from scratch (all modules; --only is not allowed with it), and imports the
art (Tools/dwarfbuilds/art/*.png -> Content/_DwarfBuilds/Art, Tools/dwarfbuilds_art.py) first.
Runs are serialised with a lock file (Saved/dwarfbuilds_build.lock), so several people or agents can call it.
Prints the BPForge lines of the log (errors and warnings in full).
"""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, "Saved", "dwarfbuilds_build.lock")
STALE = 30 * 60  # seconds after which a lock is taken over


def engine_dir():
    with open(os.path.join(ROOT, "DRGModdingAutomationScripts", "Configs", "LocalConfig.ini"), encoding="utf-8") as lines:
        for line in lines:
            key, _, value = line.strip().partition("=")
            if key == "UnrealEngineLocation":
                return value
    sys.exit("UnrealEngineLocation not found in LocalConfig.ini")


def acquire():
    waited = False
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK) > STALE:
                    os.remove(LOCK)
                    continue
            except FileNotFoundError:
                continue
            if not waited:
                print("waiting for another build to finish...")
                waited = True
            time.sleep(5)


def import_art(editor):
    """Tools/dwarfbuilds/art/*.png -> /Game/_DwarfBuilds/Art textures (Tools/dwarfbuilds_art.py, UE Python; the
    plugin is enabled for this run only). BPForge needs them first: widgets reference them."""
    log = os.path.join(ROOT, "Saved", "Logs", "dwarfbuilds_art.log")
    code = subprocess.call([editor, os.path.join(ROOT, "FSD.uproject"), "-run=pythonscript",
                            "-script=" + os.path.join(ROOT, "Tools", "dwarfbuilds_art.py"),
                            "-EnablePlugins=PythonScriptPlugin", "-unattended", "-nopause", "-nosplash",
                            "-abslog=" + log], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    done = False
    with open(log, encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if "DwarfBuildsArt" in line or ("LogPython: Error" in line):
                print(line.rstrip())
                done = done or "DwarfBuildsArt: done" in line
    if code or not done:
        raise SystemExit("art import failed (exit %s), see %s" % (code, log))


def main():
    args = sys.argv[1:]
    save = "--save" in args
    only = None
    if "--only" in args:
        only = args[args.index("--only") + 1]
    if save and only:
        sys.exit("--save builds all modules; do not combine it with --only")
    tag = only or ("save" if save else "all")
    spec = os.path.join(ROOT, "Saved", "dwarfbuilds_spec_%s.json" % tag)
    log = os.path.join(ROOT, "Saved", "Logs", "BPForge_dwarfbuilds_%s.log" % tag)
    os.makedirs(os.path.dirname(log), exist_ok=True)
    cmd = [sys.executable, os.path.join(ROOT, "Tools", "dwarfbuilds_spec.py"), spec]
    if only:
        cmd += ["--only", only]
    if not save:
        cmd.append("--transient")
    env = dict(os.environ)
    env.pop("DWARFBUILDS_DEV", None)   # only --dev makes a dev build
    if "--dev" in args:
        env["DWARFBUILDS_DEV"] = "1"
        print("DEV BUILD: test helpers are in. Do not release it.")
    subprocess.check_call(cmd, env=env)

    acquire()
    try:
        editor = os.path.join(engine_dir(), "Engine", "Binaries", "Win64", "UE4Editor-Cmd.exe")
        art = os.path.join(ROOT, "Content", "_DwarfBuilds", "Art")
        if save:
            # Generated assets are rebuilt from scratch; the imported art (Content/_DwarfBuilds/Art) is kept and
            # imported again below.
            for path in glob.glob(os.path.join(ROOT, "Content", "_DwarfBuilds", "**", "*.uasset"), recursive=True):
                if not os.path.normcase(path).startswith(os.path.normcase(art + os.sep)):
                    os.remove(path)
        if save or not glob.glob(os.path.join(art, "*.uasset")):
            import_art(editor)
        code = subprocess.call([editor, os.path.join(ROOT, "FSD.uproject"), "-run=BPForge", "-Spec=" + spec,
                                "-unattended", "-nopause", "-nosplash", "-AllowCommandletRendering", "-abslog=" + log],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.remove(LOCK)
    with open(log, encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if "LogBPForge" in line and ("Building " not in line or "Error" in line):
                print(line.rstrip())
    print("BPForge exit code", code)
    sys.exit(code)


if __name__ == "__main__":
    main()
