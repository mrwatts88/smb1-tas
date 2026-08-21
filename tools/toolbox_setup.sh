#!/bin/sh
# Reproduce the emulator tooling on a fresh Fedora box WITHOUT root on the host:
# a rootless `toolbox` container (shares $HOME, /tmp, display) holds FCEUX (RPM Fusion),
# Xvfb, mono (for BizHawk) and dev tools; Mesen2 and BizHawk are prebuilt tarballs in ~/opt.
# Idempotent. Native alternative (needs sudo on the host) is listed in docs/experiments/P0.1-tooling.md.
set -eu
S=${SMB1_DL:-$HOME/opt/dl}; mkdir -p "$S" "$HOME/opt"
# 1. container
if ! toolbox list -c 2>/dev/null | grep -q ' smb1 '; then toolbox create -y -c smb1; fi
toolbox run -c smb1 sudo dnf install -y -q https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-43.noarch.rpm || true
toolbox run -c smb1 sudo dnf install -y -q --skip-unavailable fceux xorg-x11-server-Xvfb xorg-x11-server-utils \
  mono-core mono-devel libgdiplus lsb_release compat-lua SDL2 cmake clang gdb strace mesa-dri-drivers \
  ImageMagick xwd xdotool xwininfo xprop
# 2. Mesen 2.1.1 (self-contained .NET binary; runs natively on the host)
if [ ! -x "$HOME/opt/mesen2/Mesen" ]; then
  curl -sL -o "$S/Mesen_2.1.1_Linux_x64.zip" https://github.com/SourMesen/Mesen2/releases/download/2.1.1/Mesen_2.1.1_Linux_x64.zip
  echo "7a9947575cc198209f743fef83fb2b702b786ea705506bdf3f2aea01ab7c1ce9  $S/Mesen_2.1.1_Linux_x64.zip" | sha256sum -c -
  mkdir -p "$HOME/opt/mesen2"; unzip -q -o "$S/Mesen_2.1.1_Linux_x64.zip" -d "$HOME/opt/mesen2"
fi
mkdir -p "$HOME/.config/Mesen2"
[ -f "$HOME/.config/Mesen2/settings.json" ] || printf '%s\n' '{"Debug":{"ScriptWindow":{"AllowIoOsAccess":true,"AllowNetworkAccess":false,"ScriptTimeout":3600}},"Preferences":{"AutomaticallyCheckForUpdates":false}}' > "$HOME/.config/Mesen2/settings.json"
# 3. BizHawk 2.11.1 (mono)
if [ ! -f "$HOME/opt/bizhawk/BizHawk-2.11.1-linux-x64/EmuHawk.exe" ]; then
  curl -sL -o "$S/BizHawk-2.11.1-linux-x64.tar.gz" https://github.com/TASEmulators/BizHawk/releases/download/2.11.1/BizHawk-2.11.1-linux-x64.tar.gz
  echo "38c9c12287e337a0a6923fd527767c853457d61d71e7d8ad1a772d64ce8bc93f  $S/BizHawk-2.11.1-linux-x64.tar.gz" | sha256sum -c -
  mkdir -p "$HOME/opt/bizhawk"; tar -xzf "$S/BizHawk-2.11.1-linux-x64.tar.gz" -C "$HOME/opt/bizhawk"
fi
[ -f "$HOME/opt/bizhawk/BizHawk-2.11.1-linux-x64/config.ini" ] || cat > "$HOME/opt/bizhawk/BizHawk-2.11.1-linux-x64/config.ini" <<'JSON'
{
  "LastWrittenFrom": "2.11.1",
  "SoundOutputMethod": "Dummy",
  "SoundEnabled": false,
  "UpdateAutoCheckEnabled": false,
  "SkipSuperuserPrivsCheck": true,
  "PreferredCores": { "NES": "NesHawk" },
  "Movies": { "MovieEndAction": "Finish" }
}
JSON
echo "toolbox setup done. Versions:"; toolbox run -c smb1 sh -c 'rpm -q fceux mono-core xorg-x11-server-Xvfb'
