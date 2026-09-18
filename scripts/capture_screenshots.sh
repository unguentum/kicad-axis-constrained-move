#!/usr/bin/env bash
set -euo pipefail

export DISPLAY=:99
export XDG_CONFIG_HOME="$RUNNER_TEMP/kicad-config"
export XDG_CACHE_HOME="$RUNNER_TEMP/kicad-cache"
export XDG_DATA_HOME="$RUNNER_TEMP/kicad-data"

mkdir -p "$XDG_CONFIG_HOME/kicad/10.0" "$XDG_CONFIG_HOME/kicad/10.99"
cp scripts/kicad_common.json "$XDG_CONFIG_HOME/kicad/10.0/kicad_common.json"
cp scripts/kicad_common.json "$XDG_CONFIG_HOME/kicad/10.99/kicad_common.json"

Xvfb "$DISPLAY" -screen 0 1600x900x24 -ac -nolisten tcp &
xvfb_pid=$!
pcbnew_pid=
plugin_pid=
cleanup() {
  test -z "$plugin_pid" || kill "$plugin_pid" 2>/dev/null || true
  test -z "$pcbnew_pid" || kill "$pcbnew_pid" 2>/dev/null || true
  kill "$xvfb_pid" 2>/dev/null || true
}
trap cleanup EXIT

pcbnew examples/alignment-demo.kicad_pcb &
pcbnew_pid=$!

for _ in $(seq 1 60); do
  pcb_window=$(xdotool search --onlyvisible --name "PCB Editor" 2>/dev/null | head -1 || true)
  test -n "$pcb_window" && break
  sleep 1
done
test -n "${pcb_window:-}"
xdotool windowactivate "$pcb_window"
xdotool key Return
sleep 2
xdotool windowactivate "$pcb_window"
xdotool key Return
sleep 3
xdotool windowsize "$pcb_window" 1600 900
xdotool windowmove "$pcb_window" 0 0
xdotool windowactivate "$pcb_window"

# Select both footprints in the moving set.
xdotool mousemove 480 345 click 1
xdotool keydown ctrl mousemove 558 345 click 1 keyup ctrl
sleep 1

python main.py &
plugin_pid=$!
for _ in $(seq 1 30); do
  plugin_window=$(xdotool search --onlyvisible --name "Move Aligned To" 2>/dev/null | head -1 || true)
  test -n "$plugin_window" && break
  sleep 1
done
test -n "${plugin_window:-}"
xdotool windowmove "$plugin_window" 18 175

# Select both reference footprints while the companion window remains open.
xdotool windowactivate "$pcb_window"
xdotool mousemove 745 452 click 1
xdotool keydown ctrl mousemove 852 452 click 1 keyup ctrl
sleep 2
scrot screenshots/move-aligned-dialog.png

# Same X is the default: align centres on X and leave vertical movement free.
xdotool windowactivate "$plugin_window"
xdotool key Return
sleep 2
xdotool mousemove 745 560
sleep 1
scrot screenshots/axis-constrained-move.png
xdotool key Escape
