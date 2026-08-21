#!/bin/sh
# Run FCEUX (2.6.6 Qt/SDL, Lua 5.1) headless under Xvfb, natively if `fceux` is on PATH,
# otherwise inside the rootless toolbox container `smb1` (see docs/experiments/P0.1-tooling.md).
# Usage: tools/fceux_run.sh [VAR=VAL ...] [fceux args...] ROM.nes
#   e.g. tools/fceux_run.sh OUT=/tmp/x.csv --loadlua script.lua --playmov movie.fm2 "roms/Super Mario Bros. (W) [!].nes"
# Leading VAR=VAL arguments become environment variables visible to the Lua script via
# os.getenv (toolbox does NOT forward the caller's environment, so this is the only channel).
# Notes:
# - Scripts should call emu.speedmode("nothrottle") for full speed (default is real-time 60 fps)
#   and write results to files; end with emu.exit() (which segfaults on shutdown in 2.6.6 —
#   exit status is NOT meaningful; check the output files).
# - FCEUX_TIMEOUT (seconds, default 900) kills a hung run.
set -u
TIMEOUT="${FCEUX_TIMEOUT:-900}"
ENVARGS="SDL_AUDIODRIVER=dummy"
while [ $# -gt 0 ]; do
  case "$1" in
    -*) break ;;
    *=*) ENVARGS="$ENVARGS $1"; shift ;;
    *) break ;;
  esac
done
if command -v fceux >/dev/null 2>&1 && command -v xvfb-run >/dev/null 2>&1; then
  exec env $ENVARGS timeout "$TIMEOUT" xvfb-run -a fceux "$@"
else
  exec toolbox run -c smb1 env $ENVARGS timeout "$TIMEOUT" xvfb-run -a fceux "$@"
fi
