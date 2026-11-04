#!/usr/bin/env python3
"""One-time setup on the editing PC.

    python install.py [--package-root DIR]

1. Copies carrier.setting to Fusion/Templates/Edit/Titles/Stipech Motion/SM Carrier.setting
2. Adds Workspace > Scripts > Utility > "Stipech Motion - Place" (asks for a package folder)
Then, in Resolve: Effects > Titles > SM Carrier -> drag it into the Media Pool once (any bin).
"""
import os
import platform
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def support_dir():
    s = platform.system()
    if s == "Windows":
        return os.path.join(os.environ["APPDATA"], "Blackmagic Design", "DaVinci Resolve", "Support")
    if s == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Blackmagic Design/DaVinci Resolve")
    return os.path.expanduser("~/.local/share/DaVinciResolve")


MENU_SCRIPT = r'''# Stipech Motion - Place (installed by install.py)
import os, sys
LAST = os.path.join(os.path.expanduser("~"), ".stipech-motion", "last_package.txt")
start = open(LAST).read().strip() if os.path.exists(LAST) else os.path.expanduser("~")
try:
    pkg = fusion.RequestDir(start)  # noqa: F821
except Exception:
    pkg = start
if pkg:
    pkg = pkg.rstrip("/\\")
    os.makedirs(os.path.dirname(LAST), exist_ok=True)
    open(LAST, "w").write(pkg)
    sys.path.insert(0, pkg)
    import importlib.util
    spec = importlib.util.spec_from_file_location("sm_place", os.path.join(pkg, "place.py"))
    mod = importlib.util.module_from_spec(spec)
    mod.resolve = resolve  # noqa: F821
    spec.loader.exec_module(mod)
    mod.main([pkg])
'''


def main():
    sup = support_dir()
    titles = os.path.join(sup, "Fusion", "Templates", "Edit", "Titles", "Stipech Motion")
    os.makedirs(titles, exist_ok=True)
    shutil.copy2(os.path.join(HERE, "carrier.setting"), os.path.join(titles, "SM Carrier.setting"))
    print("installed title:", os.path.join(titles, "SM Carrier.setting"))
    scripts = os.path.join(sup, "Fusion", "Scripts", "Utility")
    os.makedirs(scripts, exist_ok=True)
    with open(os.path.join(scripts, "Stipech Motion - Place.py"), "w", encoding="utf-8") as f:
        f.write(MENU_SCRIPT)
    print("installed menu script:", os.path.join(scripts, "Stipech Motion - Place.py"))
    print("\nNow in Resolve (restart it first if it was open):\n"
          "  Edit page > Effects > Titles > 'SM Carrier' -> drag into the Media Pool once.\n"
          "  Install the series fonts from the package's kit/ folder.")


if __name__ == "__main__":
    sys.exit(main())
