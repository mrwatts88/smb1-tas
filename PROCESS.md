# PROCESS — the agentic work loop

This file makes the project resumable by a fresh session with zero memory. Read it fully.

## The loop (every session, every unit)

1. **Orient (≤ 10 min).** Read `STATUS.md`. Check "Running jobs" first: for each, read its
   `runs/<id>/` log and record the outcome. Then read the last 2–3 entries of `docs/log.md`
   and any file STATUS points to for the next unit.
2. **Pick one unit.** If STATUS has an "In progress" item with checkpoint notes, resume it.
   Otherwise take the first unblocked item in "Next up". Do not ask the user which — the list
   order *is* the decision. Stop only when no unblocked unit exists; then report what is in
   "Needs user input".
3. **Declare it.** Before working, write in STATUS "In progress": unit ID, goal, acceptance
   criterion, start date. A crash mid-unit must leave a trail.
4. **Work.** Persist early and often: code → `src/` or `tools/`; data → `data/`; experiment
   write-ups → `docs/experiments/<unit-id>-<slug>.md` (setup, exact command, result,
   conclusion). Long computations → background job under `runs/<id>/` (see below). Never hold
   an important result only in context.
5. **Document.** Make sure every piece of context the next session needs is in files:
   `docs/facts.md` (new verified facts + verification method), `docs/hypotheses.md` (status
   changes with proof artifacts), `docs/experiments/` (write-ups), `docs/log.md` (append a
   dated entry: did / learned / next).
6. **Update STATUS.** Move the unit to Done (one line + pointer to its artifact), add follow-up
   units to "Next up", refresh "Key numbers", re-order "Next up" if priorities changed.
7. **Commit — always the final step.** `git add -A` then `git commit` with a one-line message
   naming the unit. Nothing is "done" until it is committed. Then give the user a short recap
   and, if context budget remains, go back to step 2.

The end-of-unit order is fixed: **document → update STATUS → commit.** Never commit before
STATUS is current; never end a session with uncommitted work.

## Unit sizing
- A unit is something one session can finish *and write down*: ~1–3 hours of agent work.
- Bigger work is split into sub-units with explicit checkpoints (e.g., "P1.2a: CPU core passes
  nestest", "P1.2b: NMI/PPU timing model"). If a unit turns out too big mid-way, split it in
  STATUS and finish the first part properly rather than leaving both halves broken.
- Unit record format in STATUS: `ID | title | track | size S/M/L | depends on | acceptance`.
- Once P0 is done, keep at least one Track B (glitch-hunt) unit in the top 5 of "Next up" so
  the high-variance track never starves.

## Long-running jobs
- Launch detached (nohup, output redirected into `runs/<id>/stdout.log`), write
  `runs/<id>/README.md` (command, start time, expected duration, machine, how to read the
  results), and list it in STATUS "Running jobs" with the machine and how to check it. If
  nothing else is runnable, end the session — the next one checks on it.
- Cloud: budget cap **$300 total** without asking; record every spend in STATUS "Spend".
  Terminate instances before the session ends unless a job is running — then record the
  instance ID and an auto-shutdown deadline. Never leave an idle instance running.

## Evidence standards
- `docs/facts.md` entries carry a status: **V** (verified by us — cite the script/experiment)
  or **S** (sourced from the community — cite the URL; treat as a claim to verify).
- `docs/hypotheses.md` statuses: untested → in-progress → confirmed / refuted / parked.
  **Refuted requires a proof artifact**: a search record (state space, pruning assumptions,
  parameters, result) or a code-level argument citing disassembly labels/addresses, with a
  reproducing script where possible. "Nobody has done it" and "the community believes" are
  never evidence. Parked = not refuted, just deprioritized — say why.
- Anything that appears to beat the record must be re-verified in two emulators
  (BizHawk/NESHawk and FCEUX) before it is recorded as a result.
- Numbers in STATUS "Key numbers" must be reproducible by a script in `tools/`.

## Context is disposable — session-end checklist
Run this before the session ends, and whenever context is getting tight:
- [ ] STATUS "In progress" is empty or has checkpoint notes a stranger could resume from.
- [ ] Every new fact / hypothesis / experiment is in its file with pointers to artifacts.
- [ ] `docs/log.md` has today's entry.
- [ ] Running jobs are listed with how to check them; no idle cloud instances.
- [ ] Ask: "Would a fresh session with zero memory know exactly what to do next and where
      everything is?" If not, fix STATUS.
- [ ] Commit — last. `git status` must be clean when the session ends.

## Version control
- The repo is under git (initialized 2026-08-21). Commit at the end of every unit — always
  after documenting and updating STATUS — with a one-line message naming the unit. Never
  commit `roms/` or large `data/` (see `.gitignore`). No remote or pushing unless the user
  sets one up.

## Conduct
- Follow the non-negotiable rules in `CLAUDE.md` (no impossibility claims without proof, no
  community outreach, no ROM downloads, context disposability).
- Don't re-litigate `docs/decisions.md`. If new evidence argues for changing a decision, write
  it under STATUS "Needs user input" and continue with other work.
- Prefer dedicated tools over shell (per `~/.claude/CLAUDE.md`). Subagents are fine for parallel
  reading/searching, but their results must land in files, not just in the reply.
