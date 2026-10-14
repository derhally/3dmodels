# P4 desk enclosure build

How to print and put together the 45° desk enclosure for the Waveshare
ESP32-P4-WIFI6-Touch-LCD-7B 7" touch display. It covers the parts to buy, the
files to print, and the assembly order for each variant, including wiring the
back-panel USB-C port.

An interactive version of this guide, with a variant switch, to-scale side
sections and a step checklist, is in [build-guide.html](build-guide.html).
Download it and open it in a browser.

## The two variants

| | Chin speaker | Compact ducted |
|---|---|---|
| Size (W × D × H) | 186 × 136 × 137 mm | 188 × 95 × 111 mm |
| Speaker | In the chin under the screen, aimed at you | At the back of the base; a duct carries the sound to a slot grille in the front lip |
| Printed parts | Front plate, body, 4 clamp tabs | Front plate, body, duct, 4 clamp tabs |
| Folder | [chin-speaker/](chin-speaker/) | [compact-ducted/](compact-ducted/) |

Both share the same front facade, display mounting, clamp tabs and back-panel
USB-C socket. The chin speaker sounds best because it points at you. The
compact one is about a third smaller in depth and height.

## Before you start

Two things haven't been confirmed by a print yet:

- **USB-C socket cutout.** It's a 14.1 × 5.75 mm rounded rectangle (R1.3) in
  the 2.4 mm back wall, from measurements. The socket's clips are rated for a
  2.5 mm panel, and a slightly thinner wall is fine for snap clips.
- **Speaker standoffs.** They're Ø7.5 mm and sit in the speaker's corner
  notches. The notches need to be at least 8 mm across.

The glass pocket and window are already confirmed with the facade test frame.
If you're printing in a new material or on another printer, print
`p4_7b_facade_test_frame` first. It takes a few minutes. Press the glass in from
behind and check for an even sliver of black glass around the screen.

## Hardware

### Electronics

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B (7" 1024 × 600, glass 164.28 × 99.17 mm) | The display |
| 1 | Box speaker, 100 × 45 × 20.75 mm, two cones, four Ø6.2 mm corner ears 10 mm behind the cone face, centres 91.2 × 36.2 mm | Audio, into the board's PH2.0 `SPK` header |
| 1 | Snap-in panel USB-C socket: 16.7 × 10.3 mm oval bezel, 14.1 × 5.75 mm panel cutout, 4 wires (V, D−, D+, G) to a PH2.0 plug | Power and data socket in the back wall, no screws |
| 1 | Right-angle USB-C cable with a flat ribbon (head 11.2 × 7.8 × 3.5 mm, ribbon 5 × 1 mm) | Board's middle `USB` port, spliced to the socket's wires |

### Screws

| Chin | Compact | Part | Used for |
|---|---|---|---|
| 4 | 4 | M2.5 × 6 screw | Clamp tabs into the display's threaded standoffs |
| 8 | 12 | M3 × 8 pan-head screw | 4 clamp tabs into the plate's columns, 4 speaker ears; compact also 4 duct lugs into the floor bosses |
| 4 | 4 | M3 × 8 countersunk screw, 90° head | Front plate to body, through the side walls |
| 4 | 4 | M3 washer, 7 mm OD or larger (9 mm fender washer is better) | Under the speaker-ear screws, bridging the 6.2 mm ear holes |

M3 × 8 is the only M3 pan-head length you need. All M3 screws self-tap into
2.5 mm pilot holes in the plastic.

### Optional

| Qty | Part | Used for |
|---|---|---|
| 4 | Rubber foot, 10 mm diameter | 1 mm recesses under the base |

You'll also need a screwdriver to match, a soldering iron and heat-shrink for
splicing the USB-C wires, and flush cutters.

## Printing

The easiest route is the Bambu Studio project, which has each part on its own
plate:

- Chin speaker: `chin-speaker/print/p4_7b_bambu_project.3mf`
- Compact ducted: `compact-ducted/print/p4_7b_compact_bambu_project.3mf`

Every part is already in its print orientation, and none need supports.

| Part | Orientation | Why it prints cleanly |
|---|---|---|
| Front plate | Facade on the bed | Smooth front face. The top cap rises at 45°, and the sideways pilot holes are teardrops. |
| Body | Standing on its floor | Open-topped, so there's no roof to bridge. The side holes and countersinks are teardrops. |
| Duct (compact only) | Mouth on the bed | The roof leans 35°. The standoffs and lugs grow from the bed or the duct wall. |
| Clamp tabs ×4 | Flat | Small flat parts. |

Use PLA or PETG, 0.2 mm layers and 3+ walls. Print the front plate in black:
the 0.5 mm of black glass around the screen then blends into the frame.

## Assembly: chin speaker

Work with the front plate lying face-down on a soft cloth.

1. **Mount the speaker on the plate.** Set the speaker into the ring on the
   back of the plate, cones toward the grille. Each corner ear drops over a
   standoff spigot. Fix each ear with an M3 × 8 and a washer.
   *Uses 4 × M3 × 8 pan, 4 × washer.*
2. **Seat the display in the pocket.** Lower the display into the pocket from
   behind, glass first, until it rests against the facade. The wider black
   border goes to the bottom, toward the speaker chin.
3. **Fit the four clamp tabs.** At each corner, lay a tab across the display's
   standoff and the column next to it. Drive an M2.5 × 6 into the standoff,
   then an M3 × 8 through the slot into the column. The tabs are identical,
   because the slot covers both column spacings. Snug them up evenly so the
   glass sits flat.
   *Uses 4 × clamp tab, 4 × M2.5 × 6, 4 × M3 × 8 pan.*
4. **Connect the speaker.** Plug the speaker lead into the PH2.0 `SPK` header
   at the top edge of the board. The lead needs about 12 cm to get there.
5. **Install the USB-C socket.** Feed the socket's wires through the cutout in
   the back wall from outside, then push the socket in until its clips snap
   behind the wall. Splice its wires to the right-angle cable (see
   [Wiring the USB-C port](#wiring-the-usb-c-port)).
6. **Plug in the right-angle cable.** Plug its head into the board's middle
   `USB` port, on the left edge seen from the front, with the ribbon pointing
   back toward the body.
7. **Close the enclosure.** Lower the plate onto the body. The top cap lands on
   the back wall, with its rib just inside it. Fit the four countersunk
   M3 × 8 through the side walls into the plate's bosses.
   *Uses 4 × M3 × 8 countersunk.*
8. **Add the feet.** Press the rubber feet into the four recesses under the
   base.

## Assembly: compact ducted

1. **Mount the speaker on the duct.** Hold the speaker's cones against the
   duct's rear rim. Each corner ear drops over a standoff spigot. Fix each ear
   from behind with an M3 × 8 and a washer.
   *Uses 4 × M3 × 8 pan, 4 × washer.*
2. **Fix the duct in the body.** Set the duct on the floor with its mouth
   pressed against the inside of the front lip, behind the slot grille. Screw
   its four lugs to the floor bosses.
   *Uses 4 × M3 × 8 pan.*
3. **Install the USB-C socket.** Feed the socket's wires through the cutout in
   the back wall from outside, then push the socket in until its clips snap
   behind the wall.
4. **Seat the display in the pocket.** Lay the plate face-down and lower the
   display into the pocket from behind, glass first, until it rests against the
   facade. The wider black border goes to the bottom.
5. **Fit the four clamp tabs.** At each corner, lay a tab across the display's
   standoff and the column beside it. Drive an M2.5 × 6 into the standoff, then
   an M3 × 8 into the column. Snug them up evenly so the glass sits flat.
   *Uses 4 × clamp tab, 4 × M2.5 × 6, 4 × M3 × 8 pan.*
6. **Connect the speaker and USB.** Plug the speaker lead into the `SPK` header
   at the top edge of the board. Splice the USB-C socket's wires to the
   right-angle cable (see [Wiring the USB-C port](#wiring-the-usb-c-port)), then
   plug the cable into the board's middle `USB` port with the ribbon pointing
   back.
7. **Close the enclosure.** Lower the plate onto the body. The top cap lands on
   the back wall, with its rib just inside it. Fit the four countersunk
   M3 × 8 through the side walls.
   *Uses 4 × M3 × 8 countersunk.*
8. **Add the feet.** Press the rubber feet into the four recesses under the
   base.

## Wiring the USB-C port

The socket comes with four wires ending in a 2.0 mm-pitch PH2.0 plug, in the
order V, D−, D+, G. The board's only USB input is its USB-C port, so splice the
socket's wires to the right-angle cable that plugs into it. Cut that cable to
length, leaving enough slack to reach the back wall. Join wire to matching
wire, solder, and cover each joint with heat-shrink.

| Pin | Signal | Typical colour |
|---|---|---|
| V | 5 V (VBUS) | Red |
| D− | Data − | White |
| D+ | Data + | Blue or green |
| G | Ground | Black |

> **Don't plug the PH2.0 plug into the board.** It looks exactly like the
> board's 4-pin I2C, UART, CAN and RS485 headers, but those carry signals, not
> USB. The socket's V wire would put 5 V where it doesn't belong.

> **Check before you power it.** Wire colours aren't standard across cables.
> Confirm each wire with a multimeter in continuity mode, against the plug pins,
> before soldering. With nothing connected, check there's no continuity between
> V and G.

The socket carries USB 2.0, which covers everything the board's middle port
uses: power, flashing and serial logs. Some USB-C sockets with only four wires
lack the 5.1 kΩ resistors a USB-C charger looks for. If a C-to-C cable doesn't
power it, use a USB-A to USB-C cable.

## After it's closed

| | |
|---|---|
| **Power switch** | It ends up inside the case. Leave it on before closing up. |
| **RESET / BOOT** | These are inside too. Flashing over USB normally works without them. |
| **Microphones** | The two mics face into the case. A 7-hole cluster in the bezel under each one lets sound in. |
| **Duct (compact)** | The speaker's sound stays inside the duct and comes out a 98 × 14 mm mouth, behind 17 slots in the front lip. That keeps the case from buzzing and keeps the speaker away from the mics. |
| **Vents** | Vertical slots near the top of the back wall let warm air out. |

Every dimension lives in `common/common.yaml` and each variant's `params.yaml`.
See the [device README](README.md) for how the models were made and how to
regenerate them.
