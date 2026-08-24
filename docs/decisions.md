# Decisions log

Decisions the user has made. Don't re-litigate; if evidence argues for a change, raise it under
STATUS "Needs user input" and keep working on other units.

| ID | Date | Decision |
|---|---|---|
| D1 | 2026-08-21 | Primary target: NES `Super Mario Bros. (W) [!].nes`, "warps" route, beat 17,868 frames (TASVideos #1715M) under standard TASVideos rules. Left+Right allowed. A no-L+R result is a bonus, not a constraint. |
| D2 | 2026-08-21 | A category-creating glitch (wrong warp / level skip / cart-swap-free ACE) that finishes the game in < 17,868 frames counts as success, as a **secondary** goal. |
| D3 | 2026-08-21 | Other SMB1 branches (warpless, PAL, walkathon, …) are a fallback only, not the primary target. |
| D4 | 2026-08-21 | No community engagement for now (no forum posts, DMs, Discord, submissions). Reading public sources is fine. |
| D5 | 2026-08-21 | The project runs as a self-contained agentic loop (PROCESS.md + STATUS.md); "continue working" in a brand-new session must be a sufficient prompt. |
| D6 | 2026-08-21 | Small spend is acceptable; cloud cap $300 total without asking (PROCESS.md). |

- **2026-08-22 — Big searches go to the cloud, not the laptop.** Multi-hour/multi-day exhaustive searches (whole-room runs, P2.3c segment proofs) must run on a cloud box; the laptop is for the model, tools, short validations, and reading the code. Run 4 (P2.1b-m3) is the last laptop-hosted long search. Needed from the user before the next big search: a provider + authentication from this box (see STATUS "Blocked / Needs user input").
- **2026-08-22 — Priority: 4-2 before 1-1 room 1.** The next big (cloud) run is the 4-2 main area with the top route allowed (H36: "2 frames short" − the pipe-entry frame = 1 short, ending unexamined), then the 4-2 warp zone (≤ 15 frames, H35). The 1-1 room-1 bounce search (H29, low prior: a stomp adds no height) is queued behind the 4-2 work.
- **2026-08-23 — Local capacity is two boxes; the Mac is opportunistic overflow.** The
  2026-08-22 "big searches go to the cloud" decision was taken when the only local box was the
  i5-1335U. The Mac is ~2.8x that box per thread natively and has 3.3x the free disk
  (F105/F106), so multi-hour validation, ladder and segment work may run locally across both.
  It is an *addition* to the loop, not a new topology: normal process on the primary box, and
  when a unit contains independent work, a subagent starts it on the Mac (PROCESS.md "Parallel
  work on the second host"). Subagents report numbers and never write docs or commit, so there
  is a single writer. Exactly one machine edits the engine (the primary box). A single giant
  run still goes to the cloud — F110's 96.9 MB/s LAN rules out splitting one BFS across
  machines. The 2026-08-22 decision stands for that case.
- **2026-08-24 — The 8-4 campaign is the primary track (user decision, session 14 evening).**
  Rationale: 8-4 is unquantized — ONE frame = the record (vs 21-frame framerule cliffs with
  deficits 5–19 everywhere else), and per F17 an earlier LAST INPUT (a longer ending coast at
  the same axe) also wins. Order: H25 (Maru's turnaround stop) → H1 (ending coast) → the water
  room (no solved optimum exists) → room transitions/wrong-warp scroll (our 4-2 specialty) →
  Bowser/RNG. One Track B unit (P3.2 RAM oracle) interleaved every few sessions — the moonshot
  slot. 1-2/8-3 framerule levels demoted to third. Beam = the finder where a room explodes;
  proof-grade closes what it can (the 1-1/4-2 doctrine unchanged).
