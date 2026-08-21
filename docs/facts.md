# Facts ledger

Status: **V** = verified by us (cite script/experiment). **S** = sourced from the community
(cite URL) — a claim to verify, not a fact we own. Add a row for every number we rely on.

| ID | Fact | Status | Source / verification |
|---|---|---|---|
| F1 | The TASVideos "warps" record is HappyLee's movie #1715M: 17,868 frames = 4:57.31 (power-on → last input, 60.0988 fps), published 2011-01-06, made in FCEUX 2.2.3 on `Super Mario Bros. (W) [!].nes`. It obsoleted klmz's 4:57.33 by exactly 1 frame. | S | https://tasvideos.org/1715M |
| F2 | RTA-timing equivalent of #1715M is 4:54.032. | S | https://en.wikipedia.org/wiki/Super_Mario_Bros._speedrunning |
| F3 | Maru's "warps, RTA rules" (no Left+Right) TAS is 4:54.265 (4:57.54 TAS timing) — 14 frames slower than #1715M. | S | https://tasvideos.org/HomePages/Maru |
| F4 | Human any% WR: averge11 4:54.415 (2025-12-18). Humans match the TAS framerule in every level except 8-4 since Niftski's "Lightning 4-2" (Sept 2023). | S | https://gamerant.com/super-mario-bros-new-world-record-speedrun-january-2025/ ; Wikipedia |
| F5 | Level completion is quantized to a global 21-frame framerule; the time from flagpole to next level rounds up to the next boundary. 8-4 ends on the axe touch with no rounding. | S | https://tasvideos.org/GameResources/NES/SuperMarioBros |
| F6 | Fireworks fire when the timer's last digit is 1, 3, or 6 at the flagpole; they cost frames. This is why the TAS avoids the flagpole glitch in 8-3. | S | Game Resources page |
| F7 | TASVideos also publishes 12 other SMB1 branches, incl. warpless 18:36.78 (HappyLee & Mars608, 2018), warps (Europe/PAL) 4:55.16, walkathon variants, minimum presses, max score/coins, FDS "-3 stage ending" 2:44.61, FDS "game end glitch" 5:29.957, and "arbitrary code execution" 4:52.65. | S | https://tasvideos.org/1G |
| F8 | The ACE movie (OnehundredthCoin, 4:52.65) requires a cartridge hot-swap from SMB3 to seed RAM $07FD so SMB1 boots into "World N" (world index 22). Mechanism: world index ≥ 8 → Bowser-replacement table OOB read → object ID $C9 → behavior jump table → $D007 → state machine value 4 → jump to unmapped $53AE → open bus executes SRE ($0A),Y → RTI → PC lands at uninitialized $1181 → controller-driven payload. | S | https://tasvideos.org/8991S |
| F9 | Community belief: the NES Minus World (-1, world index 36) is a water level whose exit pipe loops back to itself; on FDS the minus worlds differ and allow a -3 ending and ACE. | S (belief, not proof) | TASVideos publications; re-examine under H6 |
| F10 | Pressing Left+Right for one frame makes Mario walk backward in the opposite direction, giving instant deceleration. Enemy hitboxes affect Mario only every other frame. 16 subpixels per pixel. | S | Game Resources page |
| F11 | A known 8-4 micro-improvement (RTA-rules TAS): in the turnaround room, stop on the floor one frame earlier while still scrolling far enough for the wrong warp; depends on subspeed (RAM $705). | S | https://www.speedrun.com/smb1/forums/1wd01 |
| F12 | zdoroviy_antony's 2019 "perfect subpixel optimization" .fm3 rewrite ends on exactly frame 17868 — no improvement. flamexx's 2025 rewrite from 4-2 and cpt32's 2025 warps TAS are both slower than #1715M. | S | https://tasvideos.org/Forum/Topics/1337?CurrentPage=59 ; https://tasvideos.org/userfiles/game/1 |
| F13 | The TASVideos SMB1 forum thread has 63 pages (1,558 posts); the last posts (Oct–Nov 2025) are about warpless 5-1 manipulation; no active warps-improvement effort is visible on pp.59–63. | S | https://tasvideos.org/Forum/Topics/1337?CurrentPage=63 |
| F14 | Known community bots were narrow: DaSmileKat's enemy-mechanics brute forcer, a vertical-physics model + brute forcer for "minimum A presses", a Cheep-spawn optimizer. No public full-state exhaustive level search found yet (P0.8 verifies). | S | https://tasvideos.org/7094S ; https://tasvideos.org/GameResources/NES/SuperMarioBros |
| F15 | Expected ROM: `Super Mario Bros. (W) [!].nes`, MD5 811b027eaf99c2def7b933c5208636de (recollection; believed identical to (JU) PRG0). | unverified | P0.2 confirms from the .fm2 header |
