#!/bin/sh
# Run Mesen2 (headless "test runner" mode) with a Lua script on a ROM.
# Usage: tools/mesen2_run.sh SCRIPT.lua ROM.nes [TIMEOUT_SECONDS]
# - The script must call emu.stop(code) to end the run; exit code = code (255 = timed out).
# - emu.log() does NOT reach stdout: have the script write files (io.* is enabled via
#   ~/.config/Mesen2/settings.json -> Debug.ScriptWindow.AllowIoOsAccess = true).
# - DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 is required on Fedora 43 (ICU 77): without it the
#   2.1.1 binary aborts with std::bad_cast before the core starts.
# - A settings.json must exist or Mesen opens the first-run GUI wizard instead (see docs/facts.md).
set -eu
MESEN="${MESEN:-$HOME/opt/mesen2/Mesen}"
SCRIPT="$1"; ROM="$2"; TIMEOUT="${3:-600}"
[ -f "$HOME/.config/Mesen2/settings.json" ] || { echo "missing ~/.config/Mesen2/settings.json" >&2; exit 2; }
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 DOTNET_EnableDiagnostics=0
exec "$MESEN" --testrunner --enablestdout --doNotSaveSettings --timeout="$TIMEOUT" "$SCRIPT" "$ROM"
