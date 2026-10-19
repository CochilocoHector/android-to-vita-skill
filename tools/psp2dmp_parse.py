#!/usr/bin/env python3
"""解析 PS Vita 崩溃 dump（psp2core-*.psp2dmp）。

用法: python3 psp2dmp_parse.py <dump> [dump2 ...]

输出: 应用信息、游戏内存分区、线程寄存器中落在模块地址范围的候选值。
两次 dump 对比时，寄存器完全一致 = 确定性崩溃。
"""
import gzip, struct, sys, re

def load(path):
    d = open(path, 'rb').read()
    if d[:2] == b'\x1f\x8b':
        d = gzip.decompress(d)
    return d

def notes(d):
    phoff = struct.unpack_from('<I', d, 28)[0]
    n = struct.unpack_from('<H', d, 44)[0]
    es = struct.unpack_from('<H', d, 42)[0]
    out = {}
    for i in range(n):
        t, off, va, pa, fs, ms, fl, al = struct.unpack_from('<IIIIIIII', d, phoff + i * es)
        if t != 4:
            continue
        p, end = off, off + fs
        while p + 12 <= end:
            namesz, descsz, ntype = struct.unpack_from('<III', d, p); p += 12
            name = d[p:p + namesz].rstrip(b'\0').decode('latin1'); p += (namesz + 3) & ~3
            desc = d[p:p + descsz]; p += (descsz + 3) & ~3
            out.setdefault(name, desc)
    return out

def strings(b, minlen=5):
    return [m.group().decode('latin1') for m in re.finditer(rb'[ -~]{%d,}' % minlen, b)]

def show(path):
    d = load(path)
    nt = notes(d)
    print('==', path.split('/')[-1])
    app = nt.get('APP_INFO', b'')
    s = strings(app)
    if s:
        print('  app:', ' | '.join(s[:3]))
    b = nt.get('BUDGET_INFO')
    if b:
        i = b.find(b'ScePhyMemPartGame\x00')
        if i >= 0:
            vals = struct.unpack_from('<8I', b, i + 40)
            # 布局: [0]=? [1]=基址 [2]=总量 [3]=已用 [4]=剩余
            total, used, free = vals[2] / 1048576.0, vals[3] / 1048576.0, vals[4] / 1048576.0
            print(f'  game partition: total {total:.1f} MB  used {used:.1f} MB  free {free:.1f} MB')
    reg = nt.get('THREAD_REG_INFO', b'')
    cands = []
    for off in range(0, max(0, len(reg) - 3), 4):
        v = struct.unpack_from('<I', reg, off)[0]
        if 0x81000000 <= v < 0x82000000 or 0x94000000 <= v < 0x94100000 or 0x98000000 <= v < 0x99000000:
            cands.append((off, v))
    if cands:
        print('  寄存器候选:', ', '.join(f'+{o:#x}=0x{v:08x}' for o, v in cands[:8]))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    for p in sys.argv[1:]:
        show(p)
