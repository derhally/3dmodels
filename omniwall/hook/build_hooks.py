# build123d script for create_model (no params file needed).
# Takes one of the owner's measured hooks, keeps what sits behind and inside the
# panel, and replaces its half-dovetail tongue with the shared dovetail front
# (spine and symmetric head with snap notches; values in ../panel.yaml,
# dovetail_mount). Every hook gets the same head in the same place relative to
# the panel, so one pocket fits them all, and two copies of a hook are identical.
# HOOK = "bridge" (two in-line slots) or "slot_1" (fills one slot).
# MODE = "print" lays it on its flat side; "model" keeps hook coordinates.
from pathlib import Path
import yaml

HOOK = "bridge"
MODE = "print"
ROOT = Path(r"E:\source\3dmodels\omniwall")
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())


part = bridge_hook(panel, ROOT) if HOOK == "bridge" else slot_hook_1(panel, ROOT)
if MODE == "print":
    part = Rot(Y=-90) * part
    bb = part.bounding_box()
    part = Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * part
result = part
