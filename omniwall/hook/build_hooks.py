# Builds the three official hooks from ../panel.yaml and ../hook_geometry.py.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build_hooks.py
# Every printed hook carries the same dovetail front (spine and symmetric head
# with snap notches; dovetail_mount in panel.yaml), so one pocket fits them all.
# Writes, for each hook:
#   print/<name>.step/.stl/.3mf  lying on its flat side, as printed (no supports)
#   step/<name>.step             as mounted: x across the slot (flat side at 0),
#                                y out from the wall (panel front face at 4.95),
#                                z up from the upper slot's bottom edge
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())
exec((ROOT / "core_3mf.py").read_text())

# Bridge hooks are modelled from the bottom of their foot with the panel front
# at bridge_hook.panel_front_y; move them into the slot hooks' frame.
bh, s1 = panel["bridge_hook"], panel["slot_hook_1u"]
to_slot_frame = Pos(0, s1["panel_front_y"] - bh["panel_front_y"], -bh["bar_bottom"])

HOOKS = {
    "bridge_hook_1u": ("Bridge hook 1U", lambda: to_slot_frame * bridge_hook(panel, ROOT)),
    "slot_hook_1u": ("Slot hook 1U", lambda: slot_hook_1u(panel, ROOT)),
    "slot_hook_2u": ("Slot hook 2U", lambda: slot_hook_2u(panel, ROOT)),
}

(HERE / "print").mkdir(exist_ok=True)
(HERE / "step").mkdir(exist_ok=True)
for stem, (name, build) in HOOKS.items():
    hook = build()
    hook.label = name
    export_step(hook, str(HERE / "step" / f"{stem}.step"))
    flat = Rot(Y=-90) * hook                       # on its flat side
    bb = flat.bounding_box()
    flat = Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * flat
    flat.label = name
    export_step(flat, str(HERE / "print" / f"{stem}.step"))
    export_stl(flat, str(HERE / "print" / f"{stem}.stl"))
    write_3mf([(name, *shape_mesh(flat))], HERE / "print" / f"{stem}.3mf")
    b = hook.bounding_box()
    print(f"{name}: {b.size.X:.2f} x {b.size.Y:.2f} x {b.size.Z:.2f} mm, z {b.min.Z:.2f} to {b.max.Z:.2f}, "
          f"volume {hook.volume:.1f} mm3, solids {len(hook.solids())}, valid {hook.is_valid}")
