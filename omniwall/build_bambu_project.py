# Standalone script (run with uv run --no-project --python 3.12 --with build123d --with pyyaml python):
# packs the printed test parts into one Bambu Studio project, one part per plate.
# Reads the print-orientation STEP files that build_hooks.py and pocket_plate.py
# export, so run those first.
from pathlib import Path
from build123d import Pos, import_step

ROOT = Path(__file__).resolve().parent
exec((ROOT / "bambu_project.py").read_text())

PARTS = [
    ("cross-slot hook", ROOT / "hook/print/cross_slot_hook_dovetail.step"),
    ("one-slot hook", ROOT / "hook/print/one_slot_hook_dovetail.step"),
    ("pocket test plate", ROOT / "pocket-test/print/pocket_test_plate.step"),
]
plates = []
for name, step in PARTS:
    shape = import_step(str(step))
    c = shape.bounding_box().center()
    plates.append((name, [(name, Pos(-c.X, -c.Y, -shape.bounding_box().min.Z) * shape)]))
write_bambu_project(plates, ROOT / "print/omniwall_test_parts.3mf", bed=(330, 320))
