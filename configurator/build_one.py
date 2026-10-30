"""Builds one configuration in a plain Python, the same way the page does in the
browser: writes the size folder and runs the builder's own build.py.

    uv run --no-project --python 3.12 --with build123d --with pyyaml python configurator/build_one.py tool-bin cells=4 rows=3 insert=hex

The size folder is <builder>/configured (git-ignored). Prints the checks and
the files it wrote.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import configure  # noqa: E402

if len(sys.argv) < 2 or sys.argv[1] not in configure.OPTIONS["types"]:
    sys.exit("usage: build_one.py <" + "|".join(configure.OPTIONS["types"]) + "> [field=value ...]")
kind = sys.argv[1]
values = {}
for a in sys.argv[2:]:
    k, v = a.split("=", 1)
    try:
        v = json.loads(v)
    except ValueError:
        pass
    values[k] = v
r = configure.build(HERE.parent, kind, values)
print(r["params"])
for c in r["checks"]:
    print(f"{c['status']:>4}  {c['label']}: {c['detail']}")
print(f"{len(r['files'])} files in {r['folder']}")
sys.exit(0 if r["ok"] and not any(c["status"] == "fail" for c in r["checks"]) else 1)
