# Community claims ledger (P0.9, mined 2026-08-21)

Status of every entry: **S** (sourced claim, not verified by us) unless marked. Each claim is
tied to a hypothesis (H-number) so nothing here is treated as evidence until we reproduce it.

## Sources read
- #1715M / submission #2964S (HappyLee, 2010-12-31) and its discussion thread Topics/10535 (3 pages).
- #1330M / submission #2362S (klmz, 2009-08-02) and its discussion thread Topics/8414 (2 pages).
- TASVideos SMB1 thread Topics/1337 pages 57, 59, 60, 62, 63; TASVideos UserFiles/Game/1.
- Maru's homepage (RTA-rules TAS 4:57.54); speedrun.com threads: 1wd01 (Maru's RTA-rules TAS
  notes), tk6gs ("another framerule in 4-2"), prtos ("Ultimate TAS to demonstrate the 21
  frame-rule system"), rla1w ("4 2 framerule"), 0jnl2 ("Perfect inputs for Any% TAS"), guide
  elaz6 ("Lightning 4-2 Explanation"); Vice, "The 33-Year Quest for the Perfect Run…".
  (speedrun.com blocks direct fetches; read via the r.jina.ai text proxy.)
- Not reachable this session: web.archive.org (blocked), thread 1337 pp. 1–56 and 58, 61
  (not yet read — see "Still to mine").

## Claims by level

### 1-1 — the missing frame (H21)
- **andrewg, 2009-08-03 (Topics/8414):** "I can't believe that we're 1 frame short of improving
  level 1-1 by 21 frames. And it's like impossible to improve it. I really doubt anyone will
  ever save that frame." — matches our F29 exactly (deficit 1 at T_set).
- **MUGG, 2009-08-03:** "we're only a pixel away from succeeding."
- **Scepheo / andrewg, 2009-08-04:** "Corner boosting perhaps?" — "corner boosting isn't possible."
- **Derakon, 2009-08-04:** naive brute-force estimate: "even 6^20 — every possible combination of
  the first twenty frames of input — is 3656158440062976. If you could simulate 100000 frames
  per second, you'd need 1160 years" (he notes the real space is smaller). **This is an
  intractability estimate for naive enumeration, not a proof of optimality.** No search record
  for 1-1 was found anywhere.
- **shadowdsfire, 2011-01-14 (Topics/10535):** "I think there is ONE possible more frame of
  improvement in world 1-1 that could break the 21 frames rule..." — no follow-up found.
- **zdoroviy_antony et al., 2019–2020 (speedrun.com 0jnl2; thread 1337 p.59–60):** the 2019
  "perfect subpixel" .fm3 rewrite still ends on frame 17868; in 1-1 "the third room required
  losing time to execute the flagpole glitch"; "1 subpixel saved at the turnaround by releasing
  left before final fast accel and manipulating subspeed." ⇒ the WR's 1-1 deliberately loses
  time before the flagpole to set up the FPG subpixel; the lost time is the obvious place to
  look for the frame (needs a FPG-feasible x-subpixel at the pole — rule not found in text form;
  "it's the x-subpixel that needs to be manipulated for FPG" (KnucklesMaster368, 2017);
  Game Resources page says the FPG needs specific subpixel values; Sockfolder found the RTA paths).
- **HappyLee, 2017-07-01 (p.57):** improvement "should be impossible... until someone discovers
  a new glitch that I haven't known."
- **Verdict for us:** the community *believes* 1-1 is maxed but has published no proof; the
  only quantitative argument is a naive brute-force size estimate. H21 stays **untested** and
  is the first search target (P2.1), with the explicit sub-question "is there any FPG-feasible
  approach to the 1-1 pole that arrives 1 frame earlier (grab + T ≤ 1658)?"

### 1-2 (H22)
- **Maru, 2019 (1wd01):** "There is a small improvement to 1-2 ... but those improvements do not
  mean anything due to the framerule" (RTA-rules TAS context). **Gaster319 (0jnl2):** "1-2 was
  improved by a subpixel." ⇒ in-framerule gains exist; nobody claims 8 frames. Our deficit: 8.

- **Maru370, 2024 (speedrun.com 75044 "The Limit of 1-2")**: a "perfect 1-2 TAS" 3 frames faster than HappyLee's, "5 frames away from the next framerule"; zdoroviy_antony saved 7 more subpixels, "not enough to save the frame"; "maybe it is not possible". No tool/search used. ⇒ best-known 1-2 deficit: 5 (P0.8).

### 4-1
- No claims found beyond subpixel tidying. Our deficit: 9. (Asumeh 2019: NTSC floor clip in 4-1
  impossible without a Koopa bounce as Big Mario; 4-1 has no Koopas.)

### 4-2 (H23, H13)
- **HappyLee, 2010-12-31 (#2964S):** "The fastest way ... is to enter the top floor of the bricks,
  but it is still 2 frames to the next 21 frame boundary. To increase the entertainment, I chose
  to go through the bottom." ⇒ a route that is ~11 frames faster than the WR's 4-2 exists (our
  deficit on the WR route is 13; on the top route it would be **2**).
- **HappyLee, 2019-08 (p.59):** "4-2 needs no further testing. It's not possible because 4-2 has
  no Bullet Bills" (in the context of enemy-assisted tricks).
- **Maru, 2019:** "several frames can be saved in 4-2, but ... do not mean anything due to the
  framerule." **flamexx 2025 (UserFiles):** "replaced mana clip with top clip ... (it doesnt even
  save a framerule)".
- speedrun.com (tk6gs, rla1w, elaz6): the human "Lightning 4-2" reaches the same framerule as
  the TAS ("zero frames to spare"); claimed faster variants (fast accel in the warp-zone room,
  wall-jump to x=132) were judged equal or slower; "A fast accel at best saves 2 frames";
  "A walljump gives 9-10 xpos AT MAX"; wrong warp needs x-position 132.
- **Verdict:** 4-2's real target is 2 frames on the top-floor route, not 13. Promote in H23.

### 8-1
- MarbleousDave 2020: "We need to find some way to improve 8-1 and 8-2 but how?" No ideas
  recorded. Our deficit: 18.

### 8-2 (deficit 19)
- **klmz 2009:** the half-pixel acceleration trick "helped bust the 21-frame rule" in 8-2 (the
  last 8-2 framerule gain). **GTAce99/HappyLee 2019:** the RTA plant-despawn (3 Bullet Bills on
  one frame) "is for RTA only, nothing to do with TAS"; **zdoroviy_antony:** 8-2 "theoretically
  perfect", "better spawn proven to not be possible by using cheat" (cheat = RAM editing the
  spawn — a genuine search over spawn outcomes, not over inputs).
- KnucklesMaster368 2017: "a flagpole glitch with the koopa at the end of 8-2" would save a
  framerule (theoretical limit then "4:56.96"); not achieved. The WR's 8-2 FPG already happens
  at the castle door (F32), so the target there is the approach, not the glitch.

### 8-3 (deficit 10)
- **zdoroviy_antony (0jnl2):** "8-3 with FPG and '242' is 3 frames faster then without FPG — 1
  frame from walking to the castle and 2 frames from timer countdown." The WR slides (timer
  244, F29). ⇒ 3 of the 10 frames are known; 7 remain. Fireworks rule (last digit 1/3/6)
  is why the WR avoided FPG here (F6) — with timer 242 there are none.

### 8-4 (unquantized, H10/H24)
- **HappyLee 2010:** the WR's 1 frame came from "a better way to slow down the speed in the fish
  scene"; feos: the pipe-corner jump ("shortcuts pipe's corner, goes through it") gained 1 frame
  that propagated to all following rooms.
- **Maru 2019 (1wd01):** RTA-rules TAS: "stopping on the floor one frame earlier [in the
  turnaround room] while still being able to scroll the screen far enough for the wrong warp";
  "depends on subspeed values ($705)"; "did not bother to optimize subpixels upon performing the
  8-4 walljump or accelerating towards the pipe in the turnaround room." ⇒ the RTA-rules 8-4 may
  contain a 1-frame idea the L+R WR lacks — **check by diffing Maru's 8-4 against the WR's**
  (needs Maru's movie file; TASVideos page only gives the time).
- zdoroviy_antony 2019: 8-4 second room 1 subpixel saved, fifth room subpixels saved,
  "insufficient for frame savings".

### Whole-run claims
- **zdoroviy_antony (prtos):** "without framerule system Super Mario Bros TAS could be at least 42
  frames faster." (Our slack table: sum of slacks = 20+13+12+8+3+2+11 = 69; the "42" likely
  counts differently — unverified.)
- Aknell 2024 user file matches 17868 exactly; cpt32 2025: 17885; flamexx 2025: 18392 — nobody
  has beaten 17868 in 15 years, and nobody has published a search-based proof for any level.
- Tools mentioned: Pellsson's practice ROM (framerule selection 0000–9999); Lua subpixel
  displays; "wall clipping is basically a tedious brute-force for me" (redatchyon2098, 2021) —
  i.e. manual, no automated full-state search.

## Still to mine (next P0.9 pass or P0.8)
- Thread 1337 pp. 1–56, 58, 61 (2004–2019): klmz/HappyLee-era posts on 8-1, 8-2 luck
  manipulation and the FPG discovery; Sockfolder's FPG subpixel analysis (speedrun.com guides);
  Maru's movie file (for the 8-4 diff); the ACE and FDS threads for Track B.
