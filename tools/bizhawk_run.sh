#!/bin/sh
# Run BizHawk 2.11.1 (EmuHawk on mono) headless under Xvfb inside the toolbox container `smb1`
# (mono is only installed there). See docs/experiments/P0.1-tooling.md.
# Usage: tools/bizhawk_run.sh [VAR=VAL ...] [EmuHawk args...] ROM.nes
#   e.g. tools/bizhawk_run.sh OUT=/tmp/x.csv --lua=script.lua --movie=movie.bk2 "roms/Super Mario Bros. (W) [!].nes"
# Leading VAR=VAL args become environment variables for the Lua script (os.getenv) — toolbox
# does not forward the caller's environment.
# Requires ~/opt/bizhawk/BizHawk-2.11.1-linux-x64/config.ini with SoundOutputMethod=Dummy,
# LastWrittenFrom=2.11.1 and PreferredCores NES=NesHawk (tools/toolbox_setup.sh writes it);
# without it EmuHawk blocks on a modal dialog that is invisible under Xvfb.
# Scripts end with client.exit(); exit status 0 on a clean exit, 124 on BIZHAWK_TIMEOUT (default 900 s).
set -u
BIZHAWK_DIR="${BIZHAWK_DIR:-$HOME/opt/bizhawk/BizHawk-2.11.1-linux-x64}"
TIMEOUT="${BIZHAWK_TIMEOUT:-900}"
ENVARGS="SDL_AUDIODRIVER=dummy"
while [ $# -gt 0 ]; do
  case "$1" in
    -*) break ;;
    *=*) ENVARGS="$ENVARGS $1"; shift ;;
    *) break ;;
  esac
done
cd "$BIZHAWK_DIR" || exit 2
exec toolbox run -c smb1 env $ENVARGS timeout "$TIMEOUT" xvfb-run -a ./EmuHawkMono.sh "$@"
