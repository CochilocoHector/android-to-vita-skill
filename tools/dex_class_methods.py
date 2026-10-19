#!/usr/bin/env python3
"""从 classes.dex 提取指定类的方法表（名称/签名/static/native）。

用法: python3 dex_class_methods.py classes.dex 'Lcom/your/game/Main;'
"""
import struct, sys

def parse(path, target):
    d = open(path, 'rb').read()
    u32 = lambda o: struct.unpack_from('<I', d, o)[0]
    u16 = lambda o: struct.unpack_from('<H', d, o)[0]
    def uleb(o):
        r = s = 0
        while True:
            b = d[o]; o += 1; r |= (b & 0x7f) << s; s += 7
            if not b & 0x80: return r, o
    def s(idx):
        off = u32(u32(0x3c) + idx * 4); n, o = uleb(off)
        e = d.index(b'\0', o); return d[o:e].decode('utf-8', 'replace')
    types_n, types_off = u32(0x40), u32(0x44)
    proto_off, meth_off = u32(0x4c), u32(0x5c)
    cls_n, cls_off = u32(0x60), u32(0x64)
    tn = lambda i: s(u32(types_off + i * 4))
    def sig(i):
        o = proto_off + i * 12
        ret = tn(u32(o + 4)); par = u32(o + 8); ps = []
        if par:
            n = u32(par)
            for k in range(n): ps.append(tn(u16(par + 4 + k * 2)))
        return '(' + ''.join(ps) + ')' + ret
    tid = next((i for i in range(types_n) if tn(i) == target), None)
    if tid is None:
        print('class not found'); return
    for ci in range(cls_n):
        o = cls_off + ci * 32
        if u32(o) != tid: continue
        p = u32(o + 24)
        sf, p = uleb(p); inf, p = uleb(p); dm, p = uleb(p); vm, p = uleb(p)
        for _ in range(sf): _, p = uleb(p); _, p = uleb(p)
        for _ in range(inf): _, p = uleb(p); _, p = uleb(p)
        def dump(cnt, p, kind):
            idx = 0
            for _ in range(cnt):
                diff, p = uleb(p); flags, p = uleb(p); code, p = uleb(p)
                idx += diff
                mo = meth_off + idx * 8
                pr = u16(mo + 2); nm = u32(mo + 4)
                tag = []
                if flags & 0x100: tag.append('native')
                if flags & 0x8: tag.append('static')
                if flags & 0x1: tag.append('public')
                print(f'  {kind:7s} {s(nm):26s} {sig(pr):44s} {" ".join(tag)}')
            return p
        p = dump(dm, p, 'direct')
        p = u32(o + 24)
        sf, p = uleb(p); inf, p = uleb(p); dm2, p = uleb(p); vm2, p = uleb(p)
        for _ in range(sf): _, p = uleb(p); _, p = uleb(p)
        for _ in range(inf): _, p = uleb(p); _, p = uleb(p)
        for _ in range(dm2): _, p = uleb(p); _, p = uleb(p); _, p = uleb(p)
        dump(vm2, p, 'virtual')
        return

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    parse(sys.argv[1], sys.argv[2])
