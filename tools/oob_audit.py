#!/usr/bin/env python3
"""Static audit of indexed memory accesses in SMB1 (P3.1, Track B).

Scans data/disasm/smbdis.asm for instructions with an indexed operand (`base,x`, `base,y`, `(zp),y`) and,
for each, finds where the index register was last set inside the same routine (ldx/ldy/tax/tay/txa…/inx/dex
chains are followed one step). An access is flagged PLAYER if the index chain reaches a RAM symbol in the
"player-influenceable" list (positions, object slots, world/level numbers, timers, RNG, joypad…), and STORE
if it is a write (sta/stx/sty/inc/dec/asl/lsr/rol/ror to memory). Output: a table (TSV on stdout) and a
summary; `--writes` restricts to stores, `--symbol NAME` restricts to accesses whose base is NAME.

Usage: tools/oob_audit.py [--writes] [--player] [--symbol Name] [--routine Label]
"""
import re, sys

DISASM = "data/disasm/smbdis.asm"
PLAYER_RAM = {
    # values the player controls or that depend on the player's actions within a level
    "Player_X_Position", "Player_PageLoc", "Player_Y_Position", "Player_Y_HighPos", "Player_X_Speed",
    "Player_Y_Speed", "Player_State", "Player_MovingDir", "PlayerFacingDir", "Player_XSpeedAbsolute",
    "Player_Rel_XPos", "Player_Rel_YPos", "Player_SprAttrib", "Player_CollisionBits", "PlayerSize",
    "PlayerStatus", "CrouchingFlag", "SavedJoypadBits", "SavedJoypad1Bits", "SavedJoypad2Bits",
    "A_B_Buttons", "Left_Right_Buttons", "Up_Down_Buttons", "PreviousA_B_Buttons", "JoypadBitMask",
    "Enemy_ID", "Enemy_State", "Enemy_X_Position", "Enemy_PageLoc", "Enemy_Y_Position", "Enemy_Y_HighPos",
    "Enemy_Flag", "Enemy_MovingDir", "Enemy_X_Speed", "Enemy_Y_Speed", "EnemyFrameTimer", "EnemyIntervalTimer",
    "ObjectOffset", "ScreenLeft_X_Pos", "ScreenLeft_PageLoc", "ScreenRight_X_Pos", "ScreenRight_PageLoc",
    "HorizontalScroll", "ScrollAmount", "Player_X_Scroll", "ScrollLock", "AreaObjectPageLoc", "EnemyObjectPageLoc",
    "AreaDataOffset", "EnemyDataOffset", "BlockBuffer_X_Adder", "Block_Buffer_1", "Block_Buffer_2",
    "WorldNumber", "LevelNumber", "AreaNumber", "AreaPointer", "AreaType", "EntrancePage", "AltEntranceControl",
    "WarpZoneControl", "HiddenLevel", "CoinTally", "CoinTallyFor1Ups", "NumberofLives", "StompChainCounter",
    "PseudoRandomBitReg", "FrameCounter", "IntervalTimerControl", "GameTimerDisplay", "ScoreAndCoinDisplay",
    "FireballCounter", "Fireball_X_Position", "Fireball_Y_Position", "Block_X_Position", "Block_Y_Position",
    "Misc_X_Position", "Misc_Y_Position", "Misc_State", "PowerUpType", "VineHeight", "VineObjOffset",
    "StarFlagTaskControl", "FlagpoleScore", "CurrentPlayer", "EnemyOffscrBitsMasked", "Enemy_OffscreenBits",
    "Player_OffscreenBits", "SprObject_X_Position", "SprObject_Y_Position", "SprObject_PageLoc",
    "SprObject_Y_HighPos", "SprObject_OffscrBits", "SprObject_Rel_XPos", "SprObject_Rel_YPos",
}
INDEXED = re.compile(r"^\s*([a-z]{3})\s+(?:\(\s*([A-Za-z_$][A-Za-z0-9_]*)(?:[+-]\d+)?\s*\)\s*,\s*y|([A-Za-z_$][A-Za-z0-9_]*)(?:[+-][$0-9A-Fa-f]+)?\s*,\s*([xy]))\b")
LABEL = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):")
SETX = re.compile(r"^\s*(ldx|tax|inx|dex|tsx|pla|plx)\b\s*(.*)$")
SETY = re.compile(r"^\s*(ldy|tay|iny|dey|ply)\b\s*(.*)$")
SETA = re.compile(r"^\s*(lda|pla|txa|tya|adc|sbc|and|ora|eor|asl|lsr|rol|ror)\b\s*(.*)$")
STORES = {"sta", "stx", "sty", "inc", "dec", "asl", "lsr", "rol", "ror"}

def operand_symbol(op):
    m = re.match(r"^\s*#?\s*([A-Za-z_][A-Za-z0-9_]*)", op.split(";")[0])
    return m.group(1) if m else None

def load_symbols(lines):
    syms = {}
    for line in lines:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\$([0-9A-Fa-f]+)", line)
        if m: syms[m.group(1)] = int(m.group(2), 16)
    return syms

def target_mode(args):
    """--target $ADDR: every store base,x / base,y (absolute base) with 0 <= ADDR - base <= 255, i.e. a write that
    reaches ADDR when the index equals ADDR - base; with the index provenance."""
    tgt = int(args[args.index("--target") + 1].lstrip("$"), 16)
    lines = open(DISASM, encoding="utf-8", errors="replace").read().split("\n")
    syms = load_symbols(lines)
    routine, rstart = "?", 0
    print(f"# stores that can reach ${tgt:04X} (index needed = target - base)")
    print("line\troutine\top\tbase\tbase_addr\tindex_needed\tmode\tindex_from")
    for n, line in enumerate(lines, 1):
        m = LABEL.match(line)
        if m and "=" not in line.split(";")[0]:
            routine, rstart = m.group(1), n
        code = line.split(";")[0]
        mm = INDEXED.match(code)
        if not mm: continue
        op, zp_base, base, reg = mm.group(1), mm.group(2), mm.group(3), mm.group(4)
        if op not in STORES: continue
        if zp_base:   # (zp),y: pointer — base unknown statically
            base, reg, mode, baddr = zp_base, "y", "(zp),y", None
        else:
            mode = f",{reg}"
            off = re.search(r"[A-Za-z_][A-Za-z0-9_]*\s*([+-])\s*\$?([0-9A-Fa-f]+)", code)
            baddr = syms.get(base)
            if baddr is not None and off:
                d = int(off.group(2), 16 if "$" in code.split(base,1)[1][:4] else 10)
                baddr = baddr + d if off.group(1) == "+" else baddr - d
        if baddr is None:
            if mode == "(zp),y": print(f"{n}\t{routine}\t{op}\t({base}),y\t?\t?\t(zp),y\tpointer")
            continue
        dist = tgt - baddr
        if baddr < 0x100 and tgt >= 0x100: continue          # zero-page indexed wraps inside the zero page
        if 0 <= dist <= 255:
            # provenance (same walk as the table mode, simplified): last ldx/ldy/tax/tay in the routine
            prov = "?"
            k = n - 1
            while k > rstart:
                c = lines[k - 1].split(";")[0]
                ms = (SETX if reg == "x" else SETY).match(c)
                if ms:
                    prov = f"{ms.group(1)} {ms.group(2).strip()}"
                    if ms.group(1) in ("tax", "tay"):
                        kk = k - 1; ops = []
                        while kk > rstart and len(ops) < 8:
                            ma = SETA.match(lines[kk - 1].split(";")[0])
                            if ma:
                                ins2, oper2 = ma.group(1), ma.group(2).strip()
                                ops.append(f"{ins2} {oper2}".strip())
                                if ins2 in ("lda", "pla", "txa", "tya"): break
                            kk -= 1
                        prov += " <- " + " ; ".join(reversed(ops))
                    break
                k -= 1
            print(f"{n}\t{routine}\t{op}\t{base}\t${baddr:04X}\t{dist}\t{mode}\t{prov}")

def main():
    args = sys.argv[1:]
    if "--target" in args:
        return target_mode(args)
    want_writes = "--writes" in args
    want_player = "--player" in args
    sym = args[args.index("--symbol") + 1] if "--symbol" in args else None
    rout = args[args.index("--routine") + 1] if "--routine" in args else None
    lines = open(DISASM, encoding="utf-8", errors="replace").read().split("\n")
    routine, rstart = "?", 0
    rows = []
    for n, line in enumerate(lines, 1):
        m = LABEL.match(line)
        if m and not line.strip().endswith("=") and "=" not in line.split(";")[0]:
            routine, rstart = m.group(1), n
        code = line.split(";")[0]
        m = INDEXED.match(code)
        if not m:
            continue
        op, zp_base, base, reg = m.group(1), m.group(2), m.group(3), m.group(4)
        if zp_base:
            base, reg, mode = zp_base, "y", "(zp),y"
        else:
            mode = f",{reg}"
        # provenance: walk back within the routine for the last instruction setting the index register
        setter = SETX if reg == "x" else SETY
        prov, prov_line, src_sym, depth = "?", None, None, 0
        k = n - 1
        cur_reg = reg
        while k > rstart and depth < 3:
            c = lines[k - 1].split(";")[0]
            ms = (SETX if cur_reg == "x" else SETY).match(c)
            if ms:
                ins, oper = ms.group(1), ms.group(2).strip()
                prov_line = prov_line or k
                if ins in ("ldx", "ldy"):
                    prov = f"{ins} {oper}"; src_sym = operand_symbol(oper) if not oper.startswith("#") else None
                    if src_sym and oper.strip().endswith((",x", ",y")):
                        src_sym = src_sym + "[]"
                    break
                elif ins in ("tax", "tay"):
                    prov = f"{ins}"; cur_reg = "a"; depth += 1
                    # find the last A setter
                    kk = k - 1
                    ops = []
                    while kk > rstart and len(ops) < 8:
                        ma = SETA.match(lines[kk - 1].split(";")[0])
                        if ma:
                            ins2, oper2 = ma.group(1), ma.group(2).strip()
                            if ins2 in ("lda", "pla", "txa", "tya"):
                                prov = f"{ins} <- {ins2} {oper2} " + " ".join(reversed(ops))
                                if ins2 == "lda" and not oper2.startswith("#"):
                                    src_sym = operand_symbol(oper2)
                                    if oper2.rstrip().endswith((",x", ",y")): src_sym = (src_sym or "") + "[]"
                                break
                            ops.append(f"{ins2} {oper2}".strip())
                        kk -= 1
                    else:
                        prov = f"{ins} <- " + " ".join(reversed(ops))
                    break
                elif ins in ("inx", "dex", "iny", "dey"):
                    depth += 1
                    k -= 1
                    continue
                else:
                    prov = ins; break
            k -= 1
        player = bool(src_sym and src_sym.rstrip("[]") in PLAYER_RAM)
        store = op in STORES
        if want_writes and not store: continue
        if want_player and not player: continue
        if sym and base != sym: continue
        if rout and routine != rout: continue
        rows.append((n, routine, op, base, mode, prov, src_sym or "", "STORE" if store else "", "PLAYER" if player else ""))
    print("line\troutine\top\tbase\tmode\tindex_from\tsrc_symbol\tstore\tplayer")
    for r in rows:
        print("\t".join(str(x) for x in r))
    n_all = len(rows); n_st = sum(1 for r in rows if r[7]); n_pl = sum(1 for r in rows if r[8]); n_plst = sum(1 for r in rows if r[7] and r[8])
    print(f"# {n_all} indexed accesses, {n_st} stores, {n_pl} player-indexed, {n_plst} player-indexed stores", file=sys.stderr)

if __name__ == "__main__":
    main()
