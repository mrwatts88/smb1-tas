#!/bin/sh
# P0.11 — run a command on the Mac overflow host inside the arm64 Linux container.
#
# The Mac cannot run smb-opt natively (see tools/Dockerfile.smbopt), so every invocation
# goes through here. This is also the Mac's answer to the "never start a search without a
# cgroup cap" rule at the top of STATUS "Running jobs": macOS has no `systemd-run --scope
# -p MemoryMax=`, but a container gets a real cgroup, and --memory-swap equal to --memory
# forbids swap the way MemorySwapMax=0 does.
#
# usage: tools/mac_run.sh [-m MEM] -- <command> [args...]     (paths relative to repo root)
#   -m MEM   hard memory cap, docker syntax (default 6g; the Docker VM itself has ~8.2g)
#
# example:
#   tools/mac_run.sh -m 6g -- third_party/smb-opt/target/release/smb-opt bfscx W42Main ...
set -e
MEM=6g
while [ $# -gt 0 ]; do
  case "$1" in
    -m) MEM=$2; shift 2 ;;
    --) shift; break ;;
    *)  echo "usage: $0 [-m MEM] -- <command> [args...]" >&2; exit 2 ;;
  esac
done
[ $# -gt 0 ] || { echo "$0: no command given" >&2; exit 2; }

REPO=$(cd "$(dirname "$0")/.." && pwd)
exec docker run --rm \
  --memory="$MEM" --memory-swap="$MEM" \
  --volume "$REPO":/work --workdir /work \
  --user "$(id -u):$(id -g)" \
  smb-opt-build:2018 "$@"
