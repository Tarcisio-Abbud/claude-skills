#!/usr/bin/env python3
"""Anchoring check for the mutation harnesses — the cheap half of a mutation run.

Run: python3 tk/tests/anchor_check.py

Every MUTATIONS entry names its defect with a literal SUBSTRING of the source it
mutates, and that substring has to match EXACTLY ONCE. Zero matches means the
code moved out from under the entry; more than one means the mutation applied is
not the one the label describes. Either way the entry proves nothing, and the
full harnesses call it UNRUNNABLE.

They do call it — but they call it after copying the tree and rerunning a suite
per entry, which is 6min25s for `mutations.py` alone. This command answers the
anchoring question ALONE: it reads the entries, counts substrings, spawns no
suite and copies nothing, and finishes in about a second. So a reflow of a
source can be checked at the moment it is made, instead of at the end of a
mutation campaign — which is what let `main` ship an anchor that had stopped
matching, hanging on a line break in `AFK.md`.

WHAT A GREEN RUN DOES NOT SAY. It says every entry can still be APPLIED, never
that any test notices when it is. Killing a mutant is still the full harness's
answer, and this command does not replace it.

SCOPE: the harnesses under `tk/tests` — found by globbing `mutations*.py`, so a
new one is covered by existing, and no hand-kept list can fall out of date. The
repository holds two more outside this directory (`bin/tests/mutations_tracker_gh.py`
and `githooks/tests/mutations_private_values.py`); they resolve their anchors
against the repo root rather than `tk/`, and are NOT checked here.

HOW A HARNESS'S BASE AND DEFAULT SOURCE ARE FOUND. An entry may name the file it
mutates as a 5th element, relative to the harness's base directory; when it does
not, the harness's own default applies. Both the base and the default are read
from the harness itself, in increasing order of authority: the defaults declared
by the `run()` it delegates to, then its module-level `TK_DIR` / `DEFAULT_SRC`,
then the arguments its `if __name__ == "__main__"` block actually passes. That
last step reads the call with `ast` and evaluates the arguments in the module's
own namespace — the harness is never executed, so no run of this command can
start a six-minute mutation campaign by accident.
"""

import ast
import glob
import importlib
import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TK_DIR = os.path.dirname(HERE)

# positional order of `mutations_tk_contract.run(mutations, module, tk_dir, default_src)`
RUN_POSITIONAL = ("mutations", "module", "tk_dir", "default_src")


class Harness:
    """One `mutations*.py`: its entries and where their anchors are resolved."""

    def __init__(self, name, path, mutations, base, default_src):
        self.name = name
        self.path = path
        self.mutations = mutations
        self.base = base
        self.default_src = default_src


def discover(tests_dir=HERE):
    """Every mutation harness beside this file, by glob and never by hand."""
    return sorted(glob.glob(os.path.join(tests_dir, "mutations*.py")))


def _is_main_guard(node):
    return (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and any(isinstance(c, ast.Constant) and c.value == "__main__"
                    for c in node.test.comparators))


def main_call_arguments(path, module):
    """What the harness's `__main__` block passes to `run(...)`, by name.

    Read, not executed: the block's whole purpose is to start the six-minute
    campaign, and this command must never do that."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), path)
    args = {}
    for node in tree.body:
        if not _is_main_guard(node):
            continue
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                    and sub.func.id == "run"):
                continue
            for name, value in zip(RUN_POSITIONAL, sub.args):
                args[name] = value
            for kw in sub.keywords:
                if kw.arg:
                    args[kw.arg] = kw.value
    resolved = {}
    for name, node in args.items():
        if name == "mutations":  # the entries come from the module, not from here
            continue
        code = compile(ast.Expression(node), "<anchor_check>", "eval")
        resolved[name] = eval(code, vars(module))  # noqa: S307 — our own files
    return resolved


def load(path, tests_dir=HERE):
    """Import one harness and work out where its anchors are resolved."""
    name = os.path.splitext(os.path.basename(path))[0]
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    module = importlib.import_module(name)

    base, default_src = None, None
    run = getattr(module, "run", None)
    if run is not None:  # a harness that delegates: the seam's own defaults
        parameters = inspect.signature(run).parameters
        for key, attr in (("tk_dir", "base"), ("default_src", "default_src")):
            default = parameters[key].default if key in parameters else inspect.Parameter.empty
            if default is not inspect.Parameter.empty:
                if attr == "base":
                    base = default
                else:
                    default_src = default
    base = getattr(module, "TK_DIR", base)
    default_src = getattr(module, "DEFAULT_SRC", default_src)

    passed = main_call_arguments(path, module)
    base = passed.get("tk_dir", base)
    default_src = passed.get("default_src", default_src)

    return Harness(name, path, getattr(module, "MUTATIONS", None), base, default_src)


def _pairs(old, new):
    """`old`/`new` are either one anchor or equal-length lists of them."""
    if isinstance(old, (list, tuple)) or isinstance(new, (list, tuple)):
        if not isinstance(old, (list, tuple)) or not isinstance(new, (list, tuple)):
            return None
        if len(old) != len(new):
            return None
        return list(zip(old, new))
    return [(old, new)]


def check(harness, sources=None):
    """Everything wrong with this harness's anchors, one line each."""
    sources = {} if sources is None else sources
    found = []
    if harness.mutations is None:
        return [f"{harness.name}: no MUTATIONS list — this is not a harness "
                "the check knows how to read"]
    for position, entry in enumerate(harness.mutations, start=1):
        label = entry[0] if entry else f"entry {position}"
        if len(entry) < 4:
            found.append(f"{label}: entry {position} has {len(entry)} elements, "
                         "not the (label, old, new, tests) an entry is")
            continue
        old, new, tests = entry[1], entry[2], entry[3]
        if not tests:
            found.append(f"{label}: names no test, so nothing can prove the mutation dies")
        rel = entry[4] if len(entry) > 4 else harness.default_src
        if rel is None:
            found.append(f"{label}: names no source file, and the harness declares "
                         "no default one")
            continue
        if harness.base is None:
            found.append(f"{label}: the harness declares no base directory, so {rel!r} "
                         "cannot be resolved")
            continue
        path = os.path.normpath(os.path.join(harness.base, rel))
        if path not in sources:
            try:
                with open(path, encoding="utf-8") as fh:
                    sources[path] = fh.read()
            except OSError as exc:
                sources[path] = None
                found.append(f"{label}: its source {rel} cannot be read ({exc.strerror})")
        source = sources[path]
        if source is None:
            continue
        pairs = _pairs(old, new)
        if pairs is None:
            found.append(f"{label}: old and new are not one anchor nor two lists "
                         "of the same length")
            continue
        for index, (before, after) in enumerate(pairs, start=1):
            where = f" (anchor {index} of {len(pairs)})" if len(pairs) > 1 else ""
            if before == after:
                found.append(f"{label}: the mutation is a no-op, old == new{where}")
                continue
            count = source.count(before)
            if count != 1:
                found.append(f"{label}: anchor matched {count}x in {rel}, not once{where}")
    return found


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print(__doc__.strip())
        return 0 if argv == ["--help"] else 2
    paths = discover()
    if not paths:
        print(f"no mutation harness found beside {HERE} — the check proves nothing")
        return 1
    sources, entries, failures = {}, 0, 0
    for path in paths:
        harness = load(path)
        entries += len(harness.mutations or ())
        found = check(harness, sources)
        failures += len(found)
        for line in found:
            print(f"UNRUNNABLE {harness.name}\n           {line}")
    print(f"\n{len(paths)} harness(es), {entries} entries, {len(sources)} source file(s)"
          + (f" — {failures} anchor problem(s)" if failures
             else " — every anchor matches exactly once"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
