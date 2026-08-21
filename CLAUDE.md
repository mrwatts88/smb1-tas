# SMB1 TAS project — session bootstrap

Goal: produce a tool-assisted speedrun of NES Super Mario Bros. (standard ROM, NTSC,
power-on start, TASVideos rules, Left+Right allowed) that completes the game in fewer
than 17,868 frames — beating HappyLee's 2011 "warps" TAS (TASVideos #1715M).

## How every session starts
1. Read `PROCESS.md` (the work loop). It is short — read all of it.
2. Read `STATUS.md` (current state, running jobs, next unit of work, blockers).
3. Skim the last 2–3 entries of `docs/log.md`.
4. Follow the loop in PROCESS.md. When the user's prompt is just "continue working"
   (or similar), do NOT ask what to do — take the next unit of work from STATUS.md and do it.
5. Every unit ends in this fixed order: **document → update STATUS.md → commit (last)**.

## Files that matter
- `PLAN.md`            — strategy: target, where time can come from, tracks, phases, infra.
- `PROCESS.md`         — the agentic loop, unit sizing, evidence rules, session-end checklist.
- `STATUS.md`          — the only source of truth for "what's next". Keep it current.
- `docs/facts.md`      — verified facts (each with how it was verified / source).
- `docs/hypotheses.md` — ideas ledger; nothing is "impossible" without a proof artifact here.
- `docs/decisions.md`  — decisions the user has made (don't re-litigate).
- `docs/log.md`        — append-only session journal.
- `docs/experiments/`  — one file per experiment (setup, exact command, result, conclusion).
- `tools/`, `src/`, `data/`, `runs/`, `roms/` — scripts, engine code, data, long-job logs,
  user-supplied ROMs (never committed).

## Non-negotiable rules (from the user)
- Never assert something is impossible, exhausted, or already optimal until it has been
  reasoned through deeply or proven. Record the proof (search record or code-level argument)
  in `docs/hypotheses.md` before marking anything refuted.
- Do not assume something can't be done because humans never did it.
- Context is disposable: every result, decision, and next step must live in files before the
  session ends. A brand-new session must be able to continue with zero memory of the last.
- No community outreach (forums, Discord, DMs, submissions) without the user's explicit go-ahead.
  Reading public sources is fine.
- Do not download ROMs; the user supplies them in `roms/` (gitignored).

## Environment
- Primary host: Matt's Linux machine — sessions run there (record its specs in docs/facts.md
  during P0.1). A Mac exists too, but emulator/TAS tooling is Linux-first, so build, replay,
  and search on Linux.
- Cloud machines are allowed for search bursts; small spend is OK (cap in PROCESS.md).
- Remote: private GitHub repo (`git remote -v`). Commit after every unit, then push.
- If `~/.claude/CLAUDE.md` exists, follow it for Bash phrasing (prefer dedicated tools; no shell
  loops, command substitution, or cd chained with redirects).
