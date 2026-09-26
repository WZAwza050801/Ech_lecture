"""Make the test suite runnable from a standalone clone of any folder name.

Tests historically import the package as ``work.pipeline2.*`` (the layout of
the sister repository where this code lives under ``work/pipeline2/``). In this
repo the package directory IS the clone (e.g. ``Ech_lecture``) and
``pipeline2.py`` is a module of that package. Alias sys.modules accordingly:

    work                <- <PACKAGE>
    work.pipeline2      <- <PACKAGE>.pipeline2
    work.pipeline2.X    <- <PACKAGE>.X

Aliased entries are the same module objects, so no state is duplicated.
"""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.name

if PACKAGE != "work" and "work" not in sys.modules:
    try:
        # The package's parent directory must be importable for
        # importlib.import_module(PACKAGE) to work from any cwd.
        if str(ROOT.parent) not in sys.path:
            sys.path.insert(0, str(ROOT.parent))
        sys.modules["work"] = importlib.import_module(PACKAGE)
        # Import every top-level module of the package so each gets an alias.
        for path in sorted(ROOT.glob("*.py")):
            if path.stem != "__init__":
                importlib.import_module(f"{PACKAGE}.{path.stem}")
        sys.modules["work.pipeline2"] = sys.modules[f"{PACKAGE}.pipeline2"]
        sys.modules["work.pipeline2.pipeline2"] = sys.modules[f"{PACKAGE}.pipeline2"]
        for name, module in list(sys.modules.items()):
            if not name.startswith(PACKAGE + "."):
                continue
            rest = name[len(PACKAGE) + 1:]
            if rest == "pipeline2":
                continue
            sys.modules.setdefault("work.pipeline2." + rest, module)
    except ImportError:
        # Clone folder name is not a valid identifier; fall back to the
        # original import error at test collection time.
        pass
