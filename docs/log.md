# Session log (append-only; newest at the bottom)

## 2026-08-21 — Session 1: planning
**Did.** Researched the current state of the record (TASVideos publications, submission #8991S,
SMB1 Game Resources page, forum pp.59/62/63, user files, Wikipedia). Agreed target and
decisions with Matt (D1–D6). Wrote CLAUDE.md, PLAN.md, PROCESS.md, STATUS.md, docs/facts.md,
docs/hypotheses.md (H1–H20), docs/decisions.md, .gitignore, directory skeleton.

**Learned.** The warps record (#1715M, 17,868 frames) is from Jan 2011 and has survived
subpixel-perfect rewrites (2019) and two 2025 rewrites. Humans are 9 frames from the
RTA-rules TAS. ACE exists on NES only via cartridge swap; on FDS via the Minus World. No
public full-state exhaustive search exists (to verify in P0.8). Community bots were narrow.

Matt fixed the end-of-unit order: document → update STATUS → commit (last). Git initialized
and the scaffold committed.

**Next.** P0.1 (tooling), P0.2 (fetch the .fm2, verify 17,868 frames + ROM hash), P0.5/P0.6
(disassembly models) can all proceed without the ROM. P0.3+ need the ROM in `roms/`.
