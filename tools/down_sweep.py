import subprocess, numpy as np, sys
sp="/tmp/claude-1000/-home-mattwatts-Documents-smb1-tas/34855d8b-c5d3-4b37-b00d-fca2485f383c/scratchpad"
wr=bytearray(open("data/wr/wr_inputs.bin","rb").read())
lo,hi=int(sys.argv[1]),int(sys.argv[2])
print(f"single-frame Down injection sweep, core frames {lo}..{hi}")
print("  f      -> GES3 at   x     SL   | destination after load: ap/entrpage/page/X")
for f in range(lo,hi+1):
    mod=bytearray(wr); mod[f+2]|=0x20
    open(f"{sp}/ds.bin","wb").write(bytes(mod))
    subprocess.run(["./build/harness","third_party/QuickNES_Core/quicknes_libretro.so",
                    "roms/Super Mario Bros. (W) [!].nes", f"{sp}/ds.bin",
                    "--frames",str(f+230),"--input-skip","2","--ram",f"{sp}/ds.ram","--quiet"],
                   check=True, capture_output=True)
    a=np.memmap(f"{sp}/ds.ram",dtype=np.uint8,mode="r").reshape(-1,2048)
    ent=None
    for g in range(f,min(f+8,a.shape[0])):
        if a[g,0x0e]==3: ent=g; break
    if ent is None: continue
    q=a[ent].astype(int); x=q[0x6d]*256+q[0x86]; sl=q[0x71a]*256+q[0x71c]
    dest=None
    for g in range(ent,a.shape[0]):
        p=a[g].astype(int)
        if p[0x0e]==7 and p[0x752]==2: dest=(p[0x750],p[0x751],p[0x6d],p[0x86],g); break
    ds = f"ap ${dest[0]:02x} entr {dest[1]:2d} page {dest[2]:2d} X {dest[3]:3d} at core {dest[4]}" if dest else "no load in window"
    print(f"  {f} -> GES3 at {ent}  x {x:5d} SL {sl:5d} rel {x-sl:4d} | {ds}")
