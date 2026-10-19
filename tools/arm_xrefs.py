#!/usr/bin/env python3
"""地址符号化 + 交叉引用（Thumb BL 扫描 + 字面量池扫描）。

用法:
  python3 arm_xrefs.py libGame.so 0x13b9ac
  python3 arm_xrefs.py libGame.so 0x13b9ac --base 0x98000000

说明:
  - 直接调用: 扫描可执行段的 Thumb BL，解出目标地址
  - 间接引用: 搜索文件中等于该地址的 4 字节字面量（GOT/常量池）
"""
import sys, struct

def load_elf(path):
    d = open(path, 'rb').read()
    if d[:4] != b'\x7fELF':
        raise SystemExit('不是 ELF')
    phoff = struct.unpack_from('<I', d, 28)[0]
    shentsize_off = 46
    phentsize = struct.unpack_from('<H', d, 42)[0]
    phnum = struct.unpack_from('<H', d, 44)[0]
    shoff = struct.unpack_from('<I', d, 32)[0]
    shentsize = struct.unpack_from('<H', d, 46)[0]
    shnum = struct.unpack_from('<H', d, 48)[0]
    segs = []
    for i in range(phnum):
        t, off, va, pa, fs, ms, fl, al = struct.unpack_from('<IIIIIIII', d, phoff + i * phentsize)
        segs.append(dict(type=t, off=off, va=va, filesz=fs, memsz=ms, flags=fl))
    secs = []
    for i in range(shnum):
        o = shoff + i * shentsize
        nm, typ, fl, addr, off, size, link, info, al, ent = struct.unpack_from('<IIIIIIIIII', d, o)
        secs.append(dict(type=typ, addr=addr, off=off, size=size, link=link))
    dsym = next((s for s in secs if s['type'] == 11), None)
    syms = []
    if dsym:
        strt = secs[dsym['link']]
        def cstr(off):
            e = d.index(b'\0', off); return d[off:e].decode('latin1')
        for i in range(dsym['size'] // 16):
            o = dsym['off'] + i * 16
            nameoff, value, size, info, other, shndx = struct.unpack_from('<IIIBBH', d, o)
            if shndx != 0 and (info & 0xf):
                syms.append((value, cstr(strt['off'] + nameoff)))
    syms.sort()
    return d, segs, syms

def symbolize(syms, addr):
    a = addr & ~1
    best = None
    for v, n in syms:
        if v & ~1 <= a:
            best = (v & ~1, n)
        else:
            break
    if not best:
        return f'0x{a:08x}'
    return f'{best[1]}+0x{a - best[0]:x}'

def scan_thumb_bl(d, segs, target):
    hits = []
    t = target & ~1
    for s in segs:
        if s['type'] != 1 or not (s['flags'] & 1):
            continue
        base, off, size = s['va'], s['off'], s['filesz']
        for i in range(0, size - 4, 2):
            a = base + i
            hw1 = struct.unpack_from('<H', d, off + i)[0]
            if (hw1 & 0xF800) != 0xF000:
                continue
            hw2 = struct.unpack_from('<H', d, off + i + 2)[0]
            if (hw2 & 0xD000) != 0xD000:
                continue
            sbit = (hw1 >> 10) & 1
            imm10 = hw1 & 0x3FF
            j1 = (hw2 >> 13) & 1
            j2 = (hw2 >> 11) & 1
            imm11 = hw2 & 0x7FF
            i1 = (~(j1 ^ sbit)) & 1
            i2 = (~(j2 ^ sbit)) & 1
            imm = (sbit << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
            if imm & (1 << 24):
                imm -= (1 << 25)
            dst = a + 4 + imm
            if (dst & ~1) == t:
                hits.append(a)
    return hits

def scan_literals(d, target):
    pat = struct.pack('<I', target)
    hits = []
    i = 0
    while True:
        i = d.find(pat, i)
        if i < 0:
            break
        if i % 4 == 0:
            hits.append(i)
        i += 1
    return hits

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    path, addr = sys.argv[1], int(sys.argv[2], 0)
    base = 0
    if '--base' in sys.argv:
        base = int(sys.argv[sys.argv.index('--base') + 1], 0)
    d, segs, syms = load_elf(path)
    print(f'目标 0x{addr:08x}: {symbolize(syms, addr)}')
    if base:
        print(f'  运行时地址 0x{base + addr:08x}')
    calls = scan_thumb_bl(d, segs, addr)
    print(f'直接调用（Thumb BL）: {len(calls)} 处')
    for a in calls[:20]:
        print(f'  0x{a:06x}  ({symbolize(syms, a)})')
    lits = scan_literals(d, addr)
    print(f'字面量引用（可能间接）: {len(lits)} 处')
    for off in lits[:10]:
        va = None
        for s in segs:
            if s['type'] == 1 and s['off'] <= off < s['off'] + s['filesz']:
                va = s['va'] + (off - s['off'])
                break
        print(f'  file 0x{off:06x}' + (f'  va 0x{va:08x}' if va else ''))

if __name__ == '__main__':
    main()
