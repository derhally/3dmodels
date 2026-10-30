"""Turns the configurator's choices into a size folder and builds it with the
builder's own build.py, the same way in the browser (Pyodide) and in a plain
Python (configurator/build_one.py, the tests).

    folder, prefix = configure.write_folder(root, "tool-bin", {"cells": 4, ...})
    result = configure.build(root, "tool-bin", {"cells": 4, ...})

options.yaml says which fields each type has and what each choice writes into
the size folder's params.yaml; the builder's shared params.yaml does the rest.
"""
import copy
import io
import json
import math
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
OPTIONS = yaml.safe_load((HERE / "options.yaml").read_text(encoding="utf-8"))


def _num(v):
    """65.0 -> 65 for names and the params file; other numbers as they are"""
    return int(v) if isinstance(v, float) and v.is_integer() else v


def _eval(expr, values):
    return eval(expr, {"__builtins__": {}, "math": math}, dict(values))


def _resolve(node, values):
    """a `set` block with its "= expression" strings worked out"""
    if isinstance(node, dict):
        return {k: _resolve(v, values) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, values) for v in node]
    if isinstance(node, str) and node.startswith("="):
        return _num(_eval(node[1:], values))
    return node


def _merge(into, add):
    for k, v in add.items():
        if isinstance(v, dict) and isinstance(into.get(k), dict):
            _merge(into[k], v)
        else:
            into[k] = copy.deepcopy(v)


def defaults(kind):
    return {f["id"]: f["default"] for f in OPTIONS["types"][kind]["fields"]}


def enabled(cond, values):
    return cond is None or bool(_eval(cond, values))


def normalise(kind, values):
    """the full set of field values: defaults filled in, numbers clamped, and a
    choice whose condition no longer holds moved to the first one that does"""
    t = OPTIONS["types"][kind]
    v = defaults(kind)
    v.update({k: x for k, x in (values or {}).items() if k in v})
    for f in t["fields"]:
        if f["kind"] in ("int", "number"):
            x = float(v[f["id"]])
            x = min(max(x, f["min"]), f["max"])
            v[f["id"]] = int(round(x)) if f["kind"] == "int" else _num(round(x / f.get("step", 1)) * f.get("step", 1))
    for f in t["fields"]:
        if f["kind"] == "choice":
            ok = [c["id"] for c in f["choices"] if enabled(c.get("when"), v)]
            if v[f["id"]] not in ok:
                v[f["id"]] = ok[0]
    return v


def params(kind, values):
    """(params.yaml dict for the size folder, file prefix) for these choices"""
    t = OPTIONS["types"][kind]
    v = normalise(kind, values)
    out = {}
    for f in t["fields"]:
        if f["kind"] == "choice":
            c = next(c for c in f["choices"] if c["id"] == v[f["id"]])
            _merge(out, _resolve(c.get("set", {}), v))
        else:
            _merge(out, _resolve(f.get("set", {}), v))
    for a in t.get("always", []):
        if enabled(a.get("when"), v):
            _merge(out, _resolve(a["set"], v))
    prefix = t["prefix"].format(**{k: str(_num(x)).replace("-", "_") for k, x in v.items()})
    out.setdefault("unit", {})["file_prefix"] = prefix
    return out, prefix, v


def tested(kind, values):
    """True when these choices are one of main's folders"""
    v = normalise(kind, values)
    return any(all(v.get(k) == x for k, x in s.items()) for s in OPTIONS["types"][kind].get("tested", []))


def write_folder(root, kind, values, folder="configured"):
    """writes <builder>/<folder>/params.yaml under the repo root; returns (folder path, prefix, values)"""
    p, prefix, v = params(kind, values)
    d = Path(root) / OPTIONS["types"][kind]["builder"] / folder
    d.mkdir(parents=True, exist_ok=True)
    for old in d.rglob("*"):
        if old.is_file():
            old.unlink()
    head = (f"# Written by the Omniwall configurator: {OPTIONS['types'][kind]['name']}, "
            + ", ".join(f"{k} {_num(x)}" for k, x in v.items()) + "\n"
            "# Everything not set here comes from ../params.yaml.\n")
    (d / "params.yaml").write_text(head + yaml.safe_dump(p, sort_keys=False, default_flow_style=None), encoding="utf-8")
    return d, prefix, v


def build(root, kind, values, folder="configured", echo=None):
    """runs the builder's build.py on a fresh size folder in this Python; returns
    a dict: prefix, values, ok, error, report, checks, files (path: bytes size)"""
    from checks import evaluate                       # noqa: E402 (next to this file)
    d, prefix, v = write_folder(root, kind, values, folder)
    script = Path(root) / OPTIONS["types"][kind]["builder"] / "build.py"
    argv = sys.argv
    sys.argv = [str(script), folder]
    buf = io.StringIO()
    ok, err = True, ""
    try:
        with redirect_stdout(buf if echo is None else _Tee(buf, echo)):
            runpy.run_path(str(script), run_name="__main__")
    except BaseException as e:                        # build.py asserts on bad geometry: report it, don't crash
        ok, err = False, f"{type(e).__name__}: {e}"
    finally:
        sys.argv = argv
    report = (d / "report.txt").read_text(encoding="utf-8") if (d / "report.txt").exists() else buf.getvalue()
    files = {str(p.relative_to(d)).replace("\\", "/"): p.stat().st_size for p in sorted(d.rglob("*")) if p.is_file()}
    return {"kind": kind, "prefix": prefix, "values": v, "folder": str(d), "ok": ok, "error": err,
            "report": report, "checks": evaluate(kind, report, OPTIONS["types"][kind].get("checks", {}), ok, err),
            "files": files, "tested": tested(kind, v),
            "params": (d / "params.yaml").read_text(encoding="utf-8")}


class _Tee:
    def __init__(self, *outs):
        self.outs = outs

    def write(self, s):
        for o in self.outs:
            o.write(s)
        return len(s)

    def flush(self):
        pass


def build_json(root, kind, values_json):
    """build() for the browser: JSON in, JSON out"""
    return json.dumps(build(root, kind, json.loads(values_json)))
