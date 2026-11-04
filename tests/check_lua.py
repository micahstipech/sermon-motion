"""Parse every generated .comp/.setting as Lua (needs `pip install lupa`). Catches syntax errors
before Resolve does. usage: python3 tests/check_lua.py FILE..."""
import sys
from lupa import LuaRuntime
CTORS = ["ordered", "Input", "OperatorInfo", "FuID", "Composition", "BezierSpline", "XYPath", "TextPlus", "Background",
         "Merge", "Transform", "RectangleMask", "Blur", "MediaOut", "Loader", "Clip", "MacroOperator", "InstanceOutput", "GroupInfo"]
bad = 0
for f in sys.argv[1:]:
    L = LuaRuntime()
    L.execute("function ordered() return function(t) return t end end\n" +
              "\n".join(f"function {c}(t) return t end" for c in CTORS if c != "ordered"))
    try:
        t = L.execute("return " + open(f, encoding="utf-8").read())
        n = sum(1 for _ in t["Tools"].keys())
        print(f"ok   {f} ({n} tools)")
    except Exception as e:
        bad += 1
        print(f"FAIL {f}: {e}")
sys.exit(1 if bad else 0)
