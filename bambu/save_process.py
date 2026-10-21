# Saves one of Bambu Studio's own process presets, with everything it inherits
# filled in, as bambu/process/<name>.json. A design's params.yaml can then switch
# to it with print.project.print_settings_id: <name> (see README.md).
# Usage, from the repo root: save_process.py "0.12mm High Quality @BBL P2S"
import json
import os
import sys
from pathlib import Path

SYSTEM = Path(os.environ["APPDATA"]) / "BambuStudio" / "system" / "BBL" / "process"
META = {"name", "inherits", "from", "setting_id", "instantiation", "type", "description"}


def resolve(name):
    preset = json.loads((SYSTEM / f"{name}.json").read_text(encoding="utf-8"))
    values = resolve(preset["inherits"]) if preset.get("inherits") else {}
    values.update(preset)
    return values


name = sys.argv[1]
values = {k: v for k, v in resolve(name).items() if k not in META}
out = Path(__file__).resolve().parent / "process" / f"{name}.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(values, indent=4) + "\n", encoding="utf-8")
print(f"{out}: {len(values)} settings")
