#!/bin/sh
# Wrap the artifact-form page body into a standalone, self-hostable HTML document.
#
#   tools/build_page.sh
#
# Source of truth: docs/web/proving-mario-optimal.body.html — the exact file passed to
# the Artifact tool, which supplies its own <!doctype>/<head>/<body> wrapper plus a
# minimal CSS reset, so the body file must NOT contain those tags.
# Output: docs/web/index.html — the same page as a complete document, servable from any
# static host. Self-contained apart from the Google Fonts stylesheet it links.
#
# The body file is split at the first `<div class="shell">`: everything above it
# (<title>, font <link>s, <style>) goes in <head>, everything from it down in <body>.
set -eu

root=$(dirname "$0")/..
src="$root/docs/web/proving-mario-optimal.body.html"
out="$root/docs/web/index.html"

test -f "$src" || { echo "missing $src" >&2; exit 1; }
if grep -qi '<!doctype' "$src"; then echo "$src already looks like a full document" >&2; exit 1; fi
split=$(grep -n '<div class="shell">' "$src" | head -1 | cut -d: -f1)
test -n "$split" || { echo "no <div class=\"shell\"> marker in $src" >&2; exit 1; }

{
  cat <<'HEAD'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="How the SMB1 TAS project searches: framerules, frame-layered BFS, admissible bounds, the height gate, and the seams between segments.">
<style>
/* minimal reset — mirrors what the Artifact host injects, so the hosted copy matches */
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0}
img,svg,canvas{max-width:100%}
table{border-collapse:collapse}
dl,dd{margin:0}
</style>
HEAD
  sed -n "1,$((split - 1))p" "$src"
  echo '</head>'
  echo '<body>'
  sed -n "${split},\$p" "$src"
  cat <<'TAIL'
</body>
</html>
TAIL
} > "$out"

echo "wrote $out ($(wc -c < "$out") bytes)"
