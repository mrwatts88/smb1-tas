# docs/web — the search explainer page

A long-form, interactive explanation of **how this project's search actually works** —
framerules, frame-layered BFS, admissible bounds, the height gate, segment seams,
external-memory layers, and the verification discipline that backs all of it. Written for
a human reader, not for the loop; every number in it comes from `docs/facts.md`,
`docs/experiments/` or a log in `runs/`.

## Files

| file | what it is |
|---|---|
| `proving-mario-optimal.body.html` | **Source of truth.** Artifact-form: no `<!doctype>`, `<html>`, `<head>` or `<body>` tags, because the Artifact host injects those plus a minimal CSS reset. This is the file passed to the Artifact tool. |
| `index.html` | **Generated — do not edit.** The same page as a complete, self-hostable document. `sh tools/build_page.sh` regenerates it. |

## Hosting it ourselves

`index.html` is a single self-contained file: all CSS and JS are inline, all diagrams are
inline SVG or drawn on a canvas, no images, no build step, no framework. Drop it on any
static host (GitHub Pages, `python3 -m http.server`, an S3 bucket) and it works.

The one external request is the Google Fonts stylesheet for Bricolage Grotesque /
Source Serif 4 / IBM Plex Mono. Every face has a real fallback stack, so the page degrades
cleanly with no network — to make it fully offline, drop the two `<link rel="preconnect">`
tags and the `<link rel="stylesheet">` in the head, or inline the faces as `@font-face`
data URIs.

Local check:

```
sh tools/build_page.sh
python3 -m http.server -d docs/web 8000    # then open http://localhost:8000/
```

## Editing it

1. Edit `proving-mario-optimal.body.html` only.
2. `sh tools/build_page.sh` to refresh `index.html`.
3. To update the published Artifact **in place** (same URL), pass that URL to the Artifact
   tool along with the body file — publishing without the URL creates a *second* artifact.

Published Artifact: <https://claude.ai/code/artifact/bb10116b-13e3-4143-9b8e-7b6e3a91a469>
(private to the account that published it until shared from the page's share menu).

## What it deliberately does not cover

Track B (glitch hunting, the OOB audit, the RAM oracle) and Track C (knowledge mining).
The page is about Track A — the search — because that is where the compute goes. If the
glitch track produces something, it wants its own page rather than a section bolted here.
