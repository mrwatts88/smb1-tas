#!/usr/bin/env python3
"""P2.5c — reference simulation of the 4-2 main-area enemies, checked frame-by-frame against the WR dump.

Generalizes tools/room1_enemy_sim.py (validated goomba rules, P2.5a) to world 4-2's main area: the enemy data
E_UndergroundArea2 (page-skip to page 2, the $3A goomba group at col 46 y $70, the lift $27, the green koopa $00 at
col 77, the buzzy beetles $02 at cols 83/88), the block buffer BB42 (data/blockmaps/w42_main.txt) for the enemies'
wall/ground checks, and the objects the area parser inserts (piranha plants in pipes A/B/C). Slots holding object
ids the sim does not model (lift $27, mushroom $2E, vine $2F) are copied from the dump every frame ("external"),
so their slot occupancy still shapes the spawns of the modelled ones.

Rules: goombas as in P2.5a §Rules (smbdis.asm refs there); koopa/beetle/plant rules from
docs/experiments/P2.5c-notes-koopa-beetle.md and P2.5c-notes-piranha.md.

Usage: tools/w42_enemy_sim.py [RAMFILE] [FIRST] [LAST]   (defaults: data/wr/fceux_wr.ram 6585 7172)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ram_trace import load_symbols  # noqa: E402
_argv = sys.argv; sys.argv = sys.argv[:1]   # area_data.py parses sys.argv at import time
from area_data import read_block  # noqa: E402
sys.argv = _argv

SYMS = load_symbols()


def A(name, n=0):
    return SYMS[name] + n


def load_blockmap(path='data/blockmaps/w42_main.txt'):
    """Parse the `blockbuf!(BB42, W, [[...],...])` array in the block-map file -> rows[13][W] of metatile bytes."""
    txt = open(path).read()
    body = txt[txt.index('blockbuf!('):]
    rows = re.findall(r'\[((?:0x[0-9a-f]+|\d+)(?:,(?:0x[0-9a-f]+|\d+))*)\]', body)
    grid = [[int(v, 0) for v in r.split(',')] for r in rows]
    assert len(grid) == 13, len(grid)
    return grid


BLOCKS = load_blockmap()
WIDTH = len(BLOCKS[0])


def block_at(x16, ypx):
    """Metatile at screen-space point (x16, y): block row = (y - 32) >> 4 (rows 0..12), column = x16 >> 4."""
    if ypx < 32:
        return 0
    r = (ypx - 32) >> 4
    c = x16 >> 4
    if r < 0 or r > 12 or c < 0 or c >= WIDTH:
        return 0
    return BLOCKS[r][c]


def non_solid(cv):
    """ChkForNonSolids: blank $26 (vine blank), coins $c2/$c3, hidden coin block $5f are non-solid; 0 is empty."""
    return cv in (0, 0x26, 0xc2, 0xc3, 0x5f)


SETBITS = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02]
XOFF = [0x7f, 0x3f, 0x1f, 0x0f, 0x07, 0x03, 0x01, 0x00, 0x80, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc, 0xfe, 0xff]
EXTERNAL_IDS = {0x27, 0x2e, 0x2f}          # lift, mushroom, vine: copied from the dump
MODELLED_IDS = {0x00, 0x02, 0x06, 0x0d}    # green koopa, buzzy beetle, goomba, piranha plant
BBOX = {3: (1, 8, 15, 24), 9: (3, 14, 13, 20), 0x0a: None}  # BoundBoxCtrlData: (x1, y1, x2, y2) offsets; filled from the notes


def x_offscreen_bits(x16, sl16):
    sr16 = sl16 + 255
    for y, edge in ((1, sr16), (0, sl16)):
        diff = edge - x16
        lo = diff & 0xff
        hi = diff >> 8
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
    FIELDS = ('flag', 'id', 'state', 'x', 'y', 'spd', 'force', 'dir', 'itimer', 'masked', 'cbits', 'yspd', 'yforce', 'bbctl')

    def __init__(self):
        for f in self.FIELDS:
            setattr(self, f, 0)
        self.box = None
        self.external = False


class Sim:
    def __init__(self, data, edata):
        self.data = data
        self.edata = edata
        self.slots = [Slot() for _ in range(6)]
        self.stomp_timer = 0
        self.events = []
        self.eoff = self.epage = self.epsel = 0

    def ram(self, row, addr):
        return self.data[(row - 1) * 2048 + addr]

    def read_slot(self, row, i):
        d = {}
        d['flag'] = self.ram(row, A('Enemy_Flag', i)); d['id'] = self.ram(row, A('Enemy_ID', i))
        d['state'] = self.ram(row, A('Enemy_State', i))
        d['x'] = self.ram(row, A('Enemy_PageLoc', i)) * 256 + self.ram(row, A('Enemy_X_Position', i))
        d['y'] = self.ram(row, A('Enemy_Y_Position', i)); d['spd'] = self.ram(row, A('Enemy_X_Speed', i))
        d['force'] = self.ram(row, A('Enemy_X_MoveForce', i)); d['dir'] = self.ram(row, A('Enemy_MovingDir', i))
        d['itimer'] = self.ram(row, A('EnemyIntervalTimer', i)); d['masked'] = self.ram(row, A('EnemyOffscrBitsMasked', i))
        d['cbits'] = self.ram(row, A('Enemy_CollisionBits', i)); d['yspd'] = self.ram(row, A('Enemy_Y_Speed', i))
        d['yforce'] = self.ram(row, A('Enemy_Y_MoveForce', i)); d['bbctl'] = self.ram(row, A('Enemy_BoundBoxCtrl', i))
        return d

    def load_from_dump(self, row):
        for i, s in enumerate(self.slots):
            for k, v in self.read_slot(row, i).items():
                setattr(s, k, v)
            s.external = bool(s.flag) and s.id in EXTERNAL_IDS
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
                    continue
            x16 = self.epage * 256 + (b0 & 0xf0)
            if x16 < sr16:
                self.eoff += 3 if row == 0x0e else 2; self.epsel = 0
                return
            if x16 > ext16:
                return
            if row == 0x0e:
                self.eoff += 3; self.epsel = 0
                return
            if b1 & 0x40:
                self.eoff += 2; self.epsel = 0
                return
            eid = b1 & 0x3f
            if 0x37 <= eid < 0x3f:
                self.spawn_group(eid, sr16, row)
            else:
                s = self.slots[slot]
                s.flag = 1; s.id = eid; s.state = 0; s.x = x16; s.y = (row << 4) + 8
                self.init_enemy(s)
                self.events.append(('spawn', slot, eid, x16))
            self.eoff += 2; self.epsel = 0
            return

    def spawn_group(self, eid, sr16, row):
        v = eid - 0x37
        n = 3 if v & 1 else 2
        y = 0x70 if v & 2 else 0xb0
        gid = 6 if v < 4 else 0
        x16 = sr16
        for k in range(n):
            free = next((i for i in range(5) if not self.slots[i].flag), None)
            if free is None:
                return
            s = self.slots[free]
            s.flag = 1; s.id = gid; s.state = 0; s.x = x16; s.y = y + 8
            self.init_enemy(s)
            self.events.append(('spawn', free, gid, x16))
            x16 += 24

    def init_enemy(self, s):
        """InitEnemyObject dispatch for the ids we model (CheckpointEnemyID sets the masked bit first)."""
        s.masked = 1
        s.external = s.id in EXTERNAL_IDS
        if s.external:
            return
        if s.id == 6:                       # InitGoomba: InitNormalEnemy + SmallBBox
            s.spd = 0xf8; s.dir = 2; s.bbctl = 9; s.yspd = 0; s.yforce = 0
        elif s.id in (0x00, 0x02):          # InitNormalEnemy (-> TallBBox): koopa / buzzy beetle
            s.spd = 0xf8; s.dir = 2; s.bbctl = 3; s.yspd = 0; s.yforce = 0
        elif s.id == 0x0d:                  # piranha plant: InitPiranhaPlant (filled from the notes)
            raise SystemExit("piranha plant init not implemented yet")
        else:
            raise SystemExit(f"unmodelled enemy id {s.id:#x}")

    # ---- per-frame ----
    def step(self, row):
        r = self.ram
        fc = r(row, A('FrameCounter')); itc = r(row, A('IntervalTimerControl'))
        px = r(row, A('Player_PageLoc')) * 256 + r(row, A('Player_X_Position'))
        py = r(row, A('Player_Y_Position')); pys = r(row, A('Player_Y_Speed'))
        sl16 = r(row, A('ScreenLeft_PageLoc')) * 256 + r(row, A('ScreenLeft_X_Pos'))
        sr16 = sl16 + 255
        # the enemy loader (EnemiesAndLoopsCore, GameCoreRoutine) runs BEFORE the frame's area-parser task
        # (RunParser at the end of GameCoreRoutine), so its AreaParserTaskNum test sees the previous frame's value
        aptn = r(row - 1, A('AreaParserTaskNum'))
        ges = r(row, A('GameEngineSubroutine'))
        dump_stomp = r(row, A('StompTimer'))
        if itc == 20:
            for s in self.slots:
                if s.itimer and not s.external:
                    s.itimer -= 1
        self.stomp_timer = 0
        pys_signed = pys - 256 if pys >= 128 else pys
        if pys == 0xfc and dump_stomp == 1:
            pys_signed = 1
        for i in range(6):
            s = self.slots[i]
            # external objects (lift, mushroom, vine): the parser still places the lift (same slot/offset logic),
            # then the slot's fields are taken from the dump every frame, including its disappearance; objects
            # the loader does not produce (the bumped mushroom in slot 5, the vine) are copied when they appear
            d = self.read_slot(row, i)
            if s.external:
                for k, v in d.items():
                    setattr(s, k, v)
                s.external = bool(s.flag) and s.id in EXTERNAL_IDS
                s.box = None
                continue
            if not s.flag:
                if (aptn & 7) != 7:
                    self.process_enemy_data(i, sl16)
                if s.flag and s.external:
                    for k, v in d.items():
                        setattr(s, k, v)
                    s.external = bool(s.flag) and s.id in EXTERNAL_IDS
                elif not s.flag and d['flag'] and d['id'] in EXTERNAL_IDS:
                    for k, v in d.items():
                        setattr(s, k, v)
                    s.external = True
                continue
            if s.id not in MODELLED_IDS:
                raise SystemExit(f"row {row}: slot {i} holds id {s.id:#x}, not modelled")
            # RunNormalEnemies
            bits = x_offscreen_bits(s.x, sl16) >> 4
            mask = 0x44 if s.x <= sl16 else 0x48
            s.masked = bits & mask
            relx = (s.x - sl16) & 0xff
            if s.masked or BBOX.get(s.bbctl) is None:
                s.box = None
            else:
                x1, y1, x2, y2 = BBOX[s.bbctl]
                s.box = ((relx + x1) & 0xff, (s.y + y1) & 0xff, (relx + x2) & 0xff, (s.y + y2) & 0xff)
            self.bg_collision(s, row, i)
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
                        if s.id == 6 and s.state == 4:
                            pass
                        elif pys_signed > 0 or self.stomp_timer:
                            self.stomp(s, row, i)
                        else:
                            self.events.append(('death', row, i))
                else:
                    s.cbits &= 0xfe
            # EnemyMovementSubs
            if s.id == 0x0d:
                self.move_plant(s, row)
            elif s.state == 0:
                self.move(s)
            elif s.state & 7 == 1 or s.state & 0x40:   # falling
                self.move_vertical(s); self.move(s)
            elif s.id == 6 and s.state == 4:
                if s.itimer == 14:
                    self.erase(s)
                    continue
            # OffscreenBoundsCheck
            left = sl16 - 73
            right = sr16 + 72 + (1 if left >= 0 else 0)
            if s.x < left or s.x >= right:
                self.erase(s)
                self.events.append(('offscreen', row, i))

    def stomp(self, s, row, i):
        if s.id == 6:
            s.state = 4; s.itimer = 16; self.stomp_timer += 1
            self.events.append(('stomp', row, i))
        else:
            self.events.append(('stomp-unmodelled', row, i, s.id))

    def bg_collision(self, s, row, i):
        """EnemyToBGCollisionDet for walkers (ids < 7): ground under (x+8, y+24)? then side check, else fall."""
        if s.state & 0x20:
            return
        if (s.y + 62) & 0xff < 68:
            return
        if s.id >= 7:
            return
        under = block_at(s.x + 8, s.y + 24)
        if under and not non_solid(under):
            # LandEnemyProperly: TODO the $04 low-nybble test (from the koopa/beetle notes); provisional: landed
            if s.state & 0x40:
                self.land_init(s); return
            if s.state & 0x80:
                self.side_check(s, row, i); return
            if s.state == 0:
                self.side_check(s, row, i); return
            # other landed states (koopa/beetle stunned etc.): filled from the notes
            self.land_init(s)
        else:
            self.no_ground(s)

    def no_ground(self, s):
        """ChkForRedKoopa/Chk2MSBSt: green koopa/goomba/beetle: state <- EnemyBGCStateData[state] (0 -> 1: falling)."""
        if s.state & 0x80:
            s.state |= 0x40
        else:
            s.state = {0: 1, 1: 1}.get(s.state, s.state | 0x40)  # refine from the notes' EnemyBGCStateData

    def land_init(self, s):
        s.yspd = 0; s.yforce = 0
        s.y = (s.y & 0xf0) | 0x08
        if s.state & 0x80:
            s.state &= 0xbf
        else:
            s.state = 0

    def side_check(self, s, row, i):
        """DoEnemySideCheck: the block at (x+0 if moving left, x+16 if right; y+20) solid -> turn around."""
        if s.y < 0x20:
            return
        probe = s.x + (0 if s.dir == 2 else 16)
        cv = block_at(probe, s.y + 20)
        if cv and not non_solid(cv):
            self.turn_around(s)
            self.events.append(('bgturn', row, i, s.x))

    def move_plant(self, s, row):
        raise SystemExit("piranha plant movement not implemented yet")

    def move_vertical(self, s):
        """MoveD_EnemyVertically (filled from the notes): placeholder gravity."""
        raise SystemExit("enemy falling not implemented yet")

    @staticmethod
    def overlap(a, b):
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
        total = s.force + lo
        carry = 1 if total > 0xff else 0
        s.force = total & 0xff
        delta = (hi - 256 if hi >= 0x80 else hi) + carry
        s.x = s.x + delta

    @staticmethod
    def erase(s):
        s.flag = 0; s.id = 0; s.state = 0; s.itimer = 0; s.box = None; s.external = False

    def compare(self, row):
        diffs = []
        for i in range(6):
            s = self.slots[i]
            d = self.read_slot(row, i)
            if not d['flag'] and not s.flag:
                continue
            if s.external:
                continue
            for k in ('flag', 'id', 'state', 'x', 'y', 'spd', 'force', 'dir', 'itimer', 'masked'):
                if getattr(s, k) != d[k]:
                    diffs.append(f"slot{i}.{k} sim {getattr(s, k)} dump {d[k]}")
        for k, sym in (('eoff', 'EnemyDataOffset'), ('epage', 'EnemyObjectPageLoc'), ('epsel', 'EnemyObjectPageSel')):
            v = self.ram(row, A(sym))
            if getattr(self, k) != v:
                diffs.append(f"{k} sim {getattr(self, k)} dump {v}")
        return diffs


def main():
    ramfile = sys.argv[1] if len(sys.argv) > 1 else 'data/wr/fceux_wr.ram'
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 6585
    last = int(sys.argv[3]) if len(sys.argv) > 3 else 7172
    data = open(ramfile, 'rb').read()
    edata = read_block('E_UndergroundArea2')
    sim = Sim(data, edata)
    sim.load_from_dump(first - 1)
    nbad = 0
    for row in range(first, last + 1):
        sim.step(row)
        diffs = sim.compare(row)
        if diffs:
            nbad += 1
            if nbad <= 40:
                print(f"row {row}: " + "; ".join(diffs))
    print("events:", sim.events)
    print(f"{nbad} rows with enemy-state mismatches over rows {first}-{last}")


if __name__ == '__main__':
    main()
