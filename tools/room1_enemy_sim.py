#!/usr/bin/env python3
"""Reference simulation of the 1-1 room-1 enemies (goombas), checked frame-by-frame against the WR dump.

P2.5a: the enemy rules as read from smbdis.asm, driven by the real player trajectory and screen scroll taken
from the FCEUX full-RAM dump (data/wr/fceux_wr.ram, 2048 B per row, row r = fm2 frame r-1, F25). Every frame
the simulated enemy slots (flag, id, state, x16, x speed, move force, moving dir, interval timer, offscreen mask,
enemy-data parser state) are compared with the dump; mismatches are printed. Also predicts the player-enemy
overlaps (stomp frames) and checks them against StompTimer, and checks the scroll law.

Rules (smbdis.asm labels):
- spawn: EnemiesAndLoopsCore per slot 0..4 with Enemy_Flag 0 (slot 5 only takes id $2E) when
  AreaParserTaskNum & 7 != 7 -> ProcessEnemyData: object (column<<4 on EnemyObjectPageLoc) loads iff
  ScreenRight <= x <= (ScreenRight + 48) & ~15 (16-bit, CheckRightBounds/CheckRightExtBounds); objects already
  left of ScreenRight are consumed without loading; next-page bit / page-skip row $0F via EnemyObjectPageSel.
  Single enemy -> the current slot (x = col<<4, y = row<<4 + 8); group id $37..$3E (HandleGroupEnemies) ->
  the first free slots, x = ScreenRight (+24 each), y = $B0/$70 (+8). Goomba init: X speed $F8, dir 2 (left),
  bbox ctrl 9; Enemy_X_MoveForce and Enemy_CollisionBits are NOT initialised (stale slot memory).
- per live slot, in order (RunNormalEnemies): offscreen bits/mask (GetXOffscreenBits, GetMaskedOffScrBits),
  bounding box (BoundBoxCtrlData[9] = x+3..x+13, y+14..y+20, screen-relative, only when mask == 0),
  EnemyToBGCollisionDet (ground under -> DoEnemySideCheck: block at (x+0|x+16, y+20) in the moving direction
  solid -> EnemyTurnAround), EnemiesCollision (odd FrameCounter; against lower slots; Enemy_CollisionBits
  pair bit; both turn around), PlayerEnemyCollision (even FrameCounter, F59), movement (MoveObjectHorizontally:
  force += $80, x += -1/0 + carry for speed -8; +0/+1 for +8), state 4: erased when EnemyIntervalTimer == 14
  (ChkKillGoomba), OffscreenBoundsCheck (erase when x16 < SL16 - 73 or x16 >= SR16 + 72/73).
- interval timers decrement on the frames where IntervalTimerControl wraps to 20 (NMI, before the logic).

Usage: tools/room1_enemy_sim.py [RAMFILE] [FIRST] [LAST]   (defaults: data/wr/fceux_wr.ram 197 565)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ram_trace import load_symbols  # noqa: E402
from area_data import read_block  # noqa: E402

SYMS = load_symbols()

def A(name, n=0):
    return SYMS[name] + n

# Room 1 solids at the goomba side-check row (y+20 = 204 -> block row 10) and the ground (row 11): the pipes.
# L_GroundArea6: pipes at page1 col12 (len 1: rows 9-10), page2 col6 (len 2: rows 8-10), page2 col14 (len 3:
# rows 7-10), page3 col9 warp (len 3). Each pipe is 2 blocks (32 px) wide.
PIPES_X = [(448, 480), (608, 640), (736, 768), (912, 944)]

def side_solid(x16):
    assert x16 < 1100, "room-1 solid map only covers x < 1100"
    return any(lo <= x16 < hi for lo, hi in PIPES_X)

SETBITS = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02]
XOFF = [0x7f, 0x3f, 0x1f, 0x0f, 0x07, 0x03, 0x01, 0x00, 0x80, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc, 0xfe, 0xff]

def x_offscreen_bits(x16, sl16):
    """GetXOffscreenBits for an object at x16 with the screen left edge sl16 (ScreenRight = sl16 + 255)."""
    sr16 = sl16 + 255
    for y, edge in ((1, sr16), (0, sl16)):
        diff = edge - x16
        lo = diff & 0xff
        hi = diff >> 8  # signed page difference (python floor division keeps the sign)
        if hi < 0:
            idx = (0x0f if y == 1 else 0x07)
        elif hi >= 1:
            idx = (0x07 if y == 1 else 0x0f)
        else:
            idx = (0x07 if y == 1 else 0x0f)
            if lo < 0x38:
                idx = (lo >> 3) & 7
                if y == 0:
                    idx += 8
        bits = XOFF[idx]
        if bits:
            return bits
    return 0

class Slot:
    def __init__(self):
        self.flag = 0; self.id = 0; self.state = 0; self.x = 0; self.y = 0; self.spd = 0; self.force = 0
        self.dir = 0; self.itimer = 0; self.masked = 0; self.cbits = 0; self.box = None

class Sim:
    def __init__(self, data, edata):
        self.data = data
        self.edata = edata
        self.slots = [Slot() for _ in range(6)]
        self.stomp_timer = 0
        self.events = []

    def ram(self, row, addr):
        return self.data[(row - 1) * 2048 + addr]

    def load_from_dump(self, row):
        for i, s in enumerate(self.slots):
            s.flag = self.ram(row, A('Enemy_Flag', i)); s.id = self.ram(row, A('Enemy_ID', i))
            s.state = self.ram(row, A('Enemy_State', i))
            s.x = self.ram(row, A('Enemy_PageLoc', i)) * 256 + self.ram(row, A('Enemy_X_Position', i))
            s.y = self.ram(row, A('Enemy_Y_Position', i)); s.spd = self.ram(row, A('Enemy_X_Speed', i))
            s.force = self.ram(row, A('Enemy_X_MoveForce', i)); s.dir = self.ram(row, A('Enemy_MovingDir', i))
            s.itimer = self.ram(row, A('EnemyIntervalTimer', i)); s.masked = self.ram(row, A('EnemyOffscrBitsMasked', i))
            s.cbits = self.ram(row, A('Enemy_CollisionBits', i))
        self.eoff = self.ram(row, A('EnemyDataOffset')); self.epage = self.ram(row, A('EnemyObjectPageLoc'))
        self.epsel = self.ram(row, A('EnemyObjectPageSel'))

    # ---- spawning (ProcessEnemyData) ----
    def process_enemy_data(self, slot, sl16):
        sr16 = sl16 + 255
        ext16 = (sr16 + 48) & ~15
        while True:
            if self.eoff >= len(self.edata):
                return
            b0 = self.edata[self.eoff]
            if b0 == 0xff:
                return
            row = b0 & 0x0f
            if row != 0x0e and slot >= 5:
                if (self.edata[self.eoff + 1] & 0x3f) != 0x2e:
                    return
            b1 = self.edata[self.eoff + 1]
            if b1 & 0x80 and not self.epsel:
                self.epsel = 1; self.epage += 1
            if row == 0x0f:
                if not self.epsel:
                    self.epage = b1 & 0x3f; self.eoff += 2; self.epsel = 1
                    continue  # jmp ProcLoopCommand -> ProcessEnemyData again
                # page select already set: fall through to PositionEnemyObj with this object (as the code does)
            x16 = self.epage * 256 + (b0 & 0xf0)
            if x16 < sr16:
                # already behind the right edge: consumed without loading (row $0E: area change handled)
                self.eoff += 3 if row == 0x0e else 2; self.epsel = 0
                return
            if x16 > ext16:
                return  # beyond the extended boundary: wait
            if row == 0x0e:
                self.eoff += 3; self.epsel = 0
                return
            if b1 & 0x40:  # hard-mode-only object (SecondaryHardMode is 0 here)
                self.eoff += 2; self.epsel = 0
                return
            eid = b1 & 0x3f
            if 0x37 <= eid < 0x3f:
                self.spawn_group(eid, sr16, row)
            else:
                s = self.slots[slot]
                s.flag = 1; s.id = eid; s.state = 0; s.x = x16; s.y = (row << 4) + 8
                self.init_goomba(s)
                self.events.append(('spawn', slot, x16))
            self.eoff += 2; self.epsel = 0
            return

    def spawn_group(self, eid, sr16, row):
        v = eid - 0x37
        n = 3 if v & 1 else 2
        y = 0x70 if v & 2 else 0xb0
        gid = 6 if v < 4 else 0  # goomba, or green koopa for $3B-$3E
        x16 = sr16
        for k in range(n):
            free = next((i for i in range(5) if not self.slots[i].flag), None)
            if free is None:
                return
            s = self.slots[free]
            s.flag = 1; s.id = gid; s.state = 0; s.x = x16; s.y = y + 8
            self.init_goomba(s)
            self.events.append(('spawn', free, x16))
            x16 += 24

    def init_goomba(self, s):
        assert s.id == 6, "only goombas are modelled"
        s.masked = 1            # CheckpointEnemyID
        s.spd = 0xf8; s.dir = 2  # InitNormalEnemy / SetBBox

    # ---- per-frame ----
    def step(self, row):
        r = self.ram
        fc = r(row, A('FrameCounter')); itc = r(row, A('IntervalTimerControl'))
        px = r(row, A('Player_PageLoc')) * 256 + r(row, A('Player_X_Position'))
        py = r(row, A('Player_Y_Position')); pys = r(row, A('Player_Y_Speed'))
        sl16 = r(row, A('ScreenLeft_PageLoc')) * 256 + r(row, A('ScreenLeft_X_Pos'))
        sr16 = sl16 + 255
        aptn = r(row, A('AreaParserTaskNum'))
        ges = r(row, A('GameEngineSubroutine'))
        dump_stomp = r(row, A('StompTimer'))
        if itc == 20:
            for s in self.slots:
                if s.itimer:
                    s.itimer -= 1
        self.stomp_timer = 0
        prev_pys = r(row - 1, A('Player_Y_Speed'))
        pys_signed = pys - 256 if pys >= 128 else pys
        # the dump holds the post-collision y speed; at a stomp frame it is -4 ($FC) while the pre-collision
        # value was positive (F59) -> recover it from the previous frame's value (+ gravity keeps the sign)
        if pys == 0xfc and dump_stomp == 1:
            pys_signed = 1
        for i in range(6):
            s = self.slots[i]
            if not s.flag:
                if (aptn & 7) != 7:
                    self.process_enemy_data(i, sl16)
                continue
            if s.id != 6:
                raise SystemExit(f"row {row}: slot {i} holds id {s.id}, only goombas are modelled")
            # RunNormalEnemies
            bits = x_offscreen_bits(s.x, sl16) >> 4  # Y bits are 0 for y 184 on screen (high nybble 0)
            offbits = bits  # Enemy_OffscreenBits low nybble = X bits' high nybble; Y bits (high nybble) = 0
            mask = 0x44 if s.x <= sl16 else 0x48
            s.masked = offbits & mask
            relx = (s.x - sl16) & 0xff
            if s.masked:
                s.box = None
            else:
                s.box = ((relx + 3) & 0xff, s.y + 14, (relx + 13) & 0xff, s.y + 20)
            # EnemyToBGCollisionDet: ground under (room 1 has no holes) -> side check in the moving direction
            if s.y >= 0x20 and (s.state & 0x20) == 0:
                probe = s.x + (0 if s.dir == 2 else 16)
                if side_solid(probe):
                    self.turn_around(s)
                    self.events.append(('bgturn', row, i, s.x))
            # EnemiesCollision (odd FrameCounter)
            if fc & 1 and s.id < 0x15 and not s.masked:
                for j in range(i - 1, -1, -1):
                    t = self.slots[j]
                    if not t.flag or t.id >= 0x15 or t.masked or t.box is None or s.box is None:
                        continue
                    if self.overlap(s.box, t.box):
                        if (s.state | t.state) & 0x80 == 0:
                            if t.cbits & SETBITS[i]:
                                continue
                            t.cbits |= SETBITS[i]
                        if ((s.state | t.state) & 0x20) == 0 and s.state < 6 and t.state < 6:
                            self.turn_around(t); self.turn_around(s)
                            self.events.append(('eeturn', row, i, j))
                    else:
                        t.cbits &= ~SETBITS[i] & 0xff
            # PlayerEnemyCollision (even FrameCounter)
            if fc & 1 == 0 and py < 0xd0 and not s.masked and ges == 8 and (s.state & 0x20) == 0 and s.box:
                prelx = (px - sl16) & 0xff
                pbox = ((prelx + 3) & 0xff, py + 20, (prelx + 13) & 0xff, py + 32)
                if self.overlap(pbox, s.box):
                    if not (s.cbits & 1):
                        s.cbits |= 1
                        if s.state == 4:
                            pass  # stomped goomba: harmless (state 4 is handled by EnemyStomped's checks)
                        elif pys_signed > 0 or self.stomp_timer:
                            s.state = 4; s.itimer = 16; self.stomp_timer += 1
                            self.events.append(('stomp', row, i))
                        else:
                            self.events.append(('death', row, i))
                else:
                    s.cbits &= 0xfe
            # EnemyMovementSubs -> MoveNormalEnemy
            if s.state == 0:
                self.move(s)
            elif s.state == 4:
                if s.itimer == 14:
                    self.erase(s)
                    continue
            # OffscreenBoundsCheck
            left = sl16 - 73
            right = sr16 + 72 + (1 if left >= 0 else 0)
            if s.x < left or s.x >= right:
                self.erase(s)
                self.events.append(('offscreen', row, i))

    @staticmethod
    def overlap(a, b):
        # CollisionCoreLoop on 8-bit screen coordinates, inclusive edges; no wrapping in the cases we see
        al, at, ar, ab = a; bl, bt, br, bb = b
        return al <= br and bl <= ar and at <= bb and bt <= ab

    @staticmethod
    def turn_around(s):
        s.spd = (-s.spd) & 0xff
        s.dir ^= 3

    @staticmethod
    def move(s):
        lo = (s.spd << 4) & 0xff
        hi = s.spd >> 4
        if hi >= 8:
            hi |= 0xf0
        page_adj = -1 if hi >= 0x80 else 0
        total = s.force + lo
        carry = 1 if total > 0xff else 0
        s.force = total & 0xff
        delta = (hi - 256 if hi >= 0x80 else hi) + carry
        s.x = s.x + delta  # page carry/borrow folds into the 16-bit value
        del page_adj

    @staticmethod
    def erase(s):
        s.flag = 0; s.id = 0; s.state = 0; s.itimer = 0; s.box = None

    def compare(self, row):
        diffs = []
        for i in range(5):
            s = self.slots[i]
            d = {}
            d['flag'] = self.ram(row, A('Enemy_Flag', i))
            if not d['flag'] and not s.flag:
                continue
            d['id'] = self.ram(row, A('Enemy_ID', i)); d['state'] = self.ram(row, A('Enemy_State', i))
            d['x'] = self.ram(row, A('Enemy_PageLoc', i)) * 256 + self.ram(row, A('Enemy_X_Position', i))
            d['spd'] = self.ram(row, A('Enemy_X_Speed', i)); d['force'] = self.ram(row, A('Enemy_X_MoveForce', i))
            d['dir'] = self.ram(row, A('Enemy_MovingDir', i)); d['itimer'] = self.ram(row, A('EnemyIntervalTimer', i))
            d['masked'] = self.ram(row, A('EnemyOffscrBitsMasked', i))
            for k, v in d.items():
                if getattr(s, k) != v:
                    diffs.append(f"slot{i}.{k} sim {getattr(s, k)} dump {v}")
        for k, sym in (('eoff', 'EnemyDataOffset'), ('epage', 'EnemyObjectPageLoc'), ('epsel', 'EnemyObjectPageSel')):
            v = self.ram(row, A(sym))
            if getattr(self, k) != v:
                diffs.append(f"{k} sim {getattr(self, k)} dump {v}")
        return diffs

def check_scroll(data, first, last):
    """ScrollHandler: scroll = Player_X_Scroll (this frame) if Player_Pos_ForScroll (previous frame) >= $50 and
    SideCollisionTimer == 0 and the amount > 0; decremented by 1 when the amount >= 2 and the position < $70."""
    r = lambda row, a: data[(row - 1) * 2048 + a]
    bad = 0
    for row in range(first, last + 1):
        sl_prev = r(row - 1, A('ScreenLeft_PageLoc')) * 256 + r(row - 1, A('ScreenLeft_X_Pos'))
        sl = r(row, A('ScreenLeft_PageLoc')) * 256 + r(row, A('ScreenLeft_X_Pos'))
        amt = r(row, A('Player_X_Scroll')); amt = amt - 256 if amt >= 128 else amt
        pos = r(row - 1, A('Player_Pos_ForScroll'))
        sct = r(row, A('SideCollisionTimer'))
        pred = 0
        if pos >= 0x50 and sct == 0 and amt > 0:
            pred = amt - 1 if (amt >= 2 and pos < 0x70) else amt
        if sl != sl_prev + pred:
            bad += 1
            if bad <= 10:
                print(f"scroll mismatch row {row}: SL {sl_prev}->{sl}, predicted +{pred} (amt {amt} pos {pos} sct {sct})")
    print(f"scroll law: {bad} mismatches over rows {first}-{last}")

def main():
    ramfile = sys.argv[1] if len(sys.argv) > 1 else 'data/wr/fceux_wr.ram'
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 197
    last = int(sys.argv[3]) if len(sys.argv) > 3 else 565
    data = open(ramfile, 'rb').read()
    edata = read_block('E_GroundArea6')
    sim = Sim(data, edata)
    sim.load_from_dump(first - 1)
    check_scroll(data, first, last)
    nbad = 0
    for row in range(first, last + 1):
        sim.step(row)
        diffs = sim.compare(row)
        if diffs:
            nbad += 1
            if nbad <= 40:
                print(f"row {row}: " + "; ".join(diffs))
    stomps = [e for e in sim.events if e[0] == 'stomp']
    dump_stomps = [row for row in range(first, last + 1) if data[(row - 1) * 2048 + A('StompTimer')] == 1 and data[(row - 2) * 2048 + A('StompTimer')] == 0]
    print("events:", sim.events)
    print(f"predicted stomp rows {[e[1] for e in stomps]} vs dump {dump_stomps}")
    print(f"{nbad} rows with enemy-state mismatches over rows {first}-{last}")

if __name__ == '__main__':
    main()
