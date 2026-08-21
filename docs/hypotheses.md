# Hypotheses ledger

Every idea for saving time lives here. Statuses: **untested → in-progress → confirmed /
refuted / parked**. *Refuted requires a proof artifact* (search record or code-level argument
with a reproducing script). "Nobody has done it" is never evidence. Parked = deprioritized,
say why. Link each status change to the experiment file or script.

| ID | Hypothesis | Track | Status | Evidence / notes |
|---|---|---|---|---|
| H1 | **Ending-input coast.** The movie ends at last input; a final jump from farther away (or an enemy/fireball bounce) could make the last input earlier while Mario still reaches the axe. Measure #1715M's coast length first. | A | untested | Measure in P0.4; search in P2.2 |
| H2 | **Lag frames.** #1715M contains lag frames that could be removed via object/scroll management; each is a frame in 8-4 or a possible framerule flip elsewhere. | A | untested | Count in P0.4 |
| H3 | **Framerule-phase manipulation.** Some action (pause, Select, area transition, pipe, vine, death, soft reset, lag) shifts IntervalTimerControl's phase relative to the level timeline, letting a level with slack k be re-aligned. | A/B | untested | P0.5 timing model; then search |
| H4 | **Time-bonus countdown.** If the end-of-level countdown burns ~1 frame per remaining timer unit before framerule rounding, the remaining-timer value (and the 24-frame tick phase at flagpole touch) is a lever; also check whether any glitch lowers/zeroes the timer. | A | untested | P0.5 |
| H5 | **Warp table indexing.** WarpZoneControl × pipe-index into WarpZoneNumbers: which values are reachable beyond the normal {2..8, 36}? Pipe index 3 (the $00 padding) and WarpZoneControl values ≥ 3 would read other bytes — possibly a direct warp to world 8 or a castle. | B | untested | P0.6, P3.1 |
| H6 | **NES Minus World is not a dead end.** With WorldNumber = 36 many table reads are OOB (area lists, hard-mode tables, Bowser replacement); the exit pipe, vines, death/continue, or a Game Over continue may lead somewhere. Established only by hand so far. | B | untested | P3.5 |
| H7 | **WorldNumber write-reachability.** Some in-game indexed write (enemy slot overflow, object ID overflow, buffer overrun) can set WorldNumber ($075F) / LevelNumber to reach world 8 or flag the ending in an earlier castle. | B | untested | P3.1–P3.3 (RAM oracle finds the jackpot cells; audit finds the writes) |
| H8 | **Cart-swap-free ACE.** Object ID $C9 (or any OOB object/state value) can be produced in worlds 1–8 without cart swap, e.g., via another OOB index into the Bowser-replacement or enemy tables, or via uninitialized-RAM reads at power-on. | B | untested | P3.1, P3.4 |
| H9 | **Cross-level DP.** A slower framerule in an earlier level changes RNG / framerule phase enough to save more later (8-3 Hammer Bros, 8-4 Bowser). | A | untested | P2.4 |
| H10 | **8-4 full-state exhaustive search** finds ≥ 1 frame (wall clip, turnaround room, water, Bowser pattern, L+R usage). | A | untested | P2.2 |
| H11 | **Per-level threshold search** reaches framerule N−1 in at least one of the 7 framerule levels (priority = smallest slack first). | A | untested | P0.4 then P2.3 |
| H12 | **L+R / U+D semantics** contain effects beyond the known 1-frame reversal (e.g., interactions with walls, vines, pipes, flagpole, swimming) that enable new clips. | B | untested | P0.7 |
| H13 | **Alternate pipe glitch** (entry point variable loads per screen): a pipe in 1-2, 4-2, or 8-4 can be made to lead somewhere useful — e.g., an 8-4 pipe into the Bowser room. | B | untested | P0.6 |
| H14 | **Vine teleport / screen-edge tricks** skip a section of 8-4 or 4-2. | B | untested | P0.6, P2.x |
| H15 | **Soft reset exploitation.** If TASVideos rules allow mid-movie resets: resetting during a specific write leaves the warm-boot/continue path ($07FD/$07FF) in a state that starts later than 1-1 faster than playing there. Cost: title screen again. | B | untested | Check rules; P0.6 |
| H16 | **Sprite-0 / PPU timing.** Lag frames can be prevented (or the NMI-overrun threshold moved) by controlling what the game renders. | A | untested | P0.5 |
| H17 | **Object-slot spawn suppression.** 5+ active sprites prevent spawns (documented for 4-4 Bowser). In 8-4, suppressing Bowser (or hammers/fire) may give a faster axe. | A/B | untested | P0.6, P2.2 |
| H18 | **Power-up usage.** A power-up somewhere (fire, super) nets frames despite pickup cost (e.g., fireballs vs Bowser, big-Mario clip geometry). Low prior. | A | untested | P2.x |
| H19 | **Start-press / power-on alignment.** The first Start press frame and emulator initial-RAM convention are fixed by rules; confirm #1715M presses Start on the first accepted frame and that nothing in the boot path can be shortened. | A | untested | P0.4 |
| H20 | **Uninitialized-RAM reads.** The game reads RAM the boot routine does not clear (the ACE lands at $1181 for this reason). Under the emulator's defined initial RAM, any such read that affects gameplay is a lever. | B | untested | P3.1 |
