#!/usr/bin/env bash
set -euxo pipefail

export DISPLAY=:99
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export XDG_CONFIG_HOME="$RUNNER_TEMP/kicad-config"
export XDG_CACHE_HOME="$RUNNER_TEMP/kicad-cache"
export XDG_DATA_HOME="$RUNNER_TEMP/kicad-data"

mkdir -p "$XDG_CONFIG_HOME/kicad/10.0" "$XDG_CONFIG_HOME/kicad/10.99"
cp scripts/kicad_common.json "$XDG_CONFIG_HOME/kicad/10.0/kicad_common.json"
cp scripts/kicad_common.json "$XDG_CONFIG_HOME/kicad/10.99/kicad_common.json"
rm -f screenshots/move-aligned-dialog.png screenshots/axis-constrained-move.png

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

display_ready=false
for _ in $(seq 1 30); do
  if xdotool getmouselocation >/dev/null 2>&1; then
    display_ready=true
    break
  fi
  sleep 0.2
done
test "$display_ready" = true

pcbnew examples/alignment-demo.kicad_pcb &
pcbnew_pid=$!

pcb_window=
for _ in $(seq 1 60); do
  blocked=false
  for window in $(xdotool search --onlyvisible --pid "$pcbnew_pid" 2>/dev/null || true); do
    name=$(xdotool getwindowname "$window" 2>/dev/null || true)
    if [[ "$name" == *"PCB Editor"* ]]; then
      pcb_window=$window
    elif [[ "$name" == "KiCad Setup" ]]; then
      blocked=true
      xdotool key --window "$window" Return || true
    else
      blocked=true
      xdotool key --window "$window" Escape || true
    fi
  done
  test -n "$pcb_window" && test "$blocked" = false && break
  sleep 1
done
test -n "${pcb_window:-}"
sleep 3
xdotool windowsize "$pcb_window" 1600 900
xdotool windowmove "$pcb_window" 0 0
xdotool windowfocus "$pcb_window"

# The editor window appears before the board API handler is ready. Probe the
# same IPC call the plugin makes so a fast runner cannot race PCB Editor startup.
api_ready=false
for _ in $(seq 1 60); do
  if python -c 'from kipy import KiCad; KiCad().get_board()' >/dev/null 2>&1; then
    api_ready=true
    break
  fi
  sleep 1
done
test "$api_ready" = true

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
xdotool windowfocus "$pcb_window"
xdotool mousemove 745 452 click 1
xdotool keydown ctrl mousemove 852 452 click 1 keyup ctrl
sleep 2
scrot screenshots/move-aligned-dialog.png

# Same X is the default: align centres on X and leave vertical movement free.
xdotool windowfocus "$plugin_window"
xdotool key Return
sleep 2
xdotool mousemove 745 560
sleep 1
scrot screenshots/axis-constrained-move.png
xdotool key Escape
