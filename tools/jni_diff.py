#!/usr/bin/env python3
"""对比 DEX 中的 Java 方法与兼容层注册表，输出缺失/多余。

用法: python3 jni_diff.py classes.dex 'Lcom/x/Y;' registry.txt

registry.txt 每行:  name sig     或   name
  - 以 # 开头为注释
  - 有 sig 时按 (name,sig) 匹配，否则只按 name 匹配
"""
import sys, struct

def dex_methods(path, target):
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
        raise SystemExit('class not found: ' + target)
    out = []
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
                out.append((s(nm), sig(pr), 'native' if flags & 0x100 else 'java'))
            return p
        p = dump(dm, p, 'direct')
        p = u32(o + 24)
        sf, p = uleb(p); inf, p = uleb(p); dm2, p = uleb(p); vm2, p = uleb(p)
        for _ in range(sf): _, p = uleb(p); _, p = uleb(p)
        for _ in range(inf): _, p = uleb(p); _, p = uleb(p)
        for _ in range(dm2): _, p = uleb(p); _, p = uleb(p); _, p = uleb(p)
        dump(vm2, p, 'virtual')
        break
    return out

def read_registry(path):
    reg = []
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'): continue
        parts = line.split()
        reg.append((parts[0], parts[1] if len(parts) > 1 else None))
    return reg

def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    dex, cls, regf = sys.argv[1], sys.argv[2], sys.argv[3]
    methods = dex_methods(dex, cls)
    reg = read_registry(regf)
    reg_names = {n for n, _ in reg}
    reg_pairs = {(n, s) for n, s in reg if s}
    used = set()
    missing, matched = [], []
    for name, sig, kind in methods:
        if kind == 'native':
            continue
        hit = None
        if (name, sig) in reg_pairs: hit = (name, sig)
        elif name in reg_names:
            hit = next((r for r in reg if r[0] == name), None)
        if hit:
            matched.append((name, sig))
            used.add(hit)
        else:
            missing.append((name, sig))
    extra = [r for r in reg if r not in used]
    print(f'dex 方法（非 native）: {len([m for m in methods if m[2] != "native"])}')
    print(f'registry 条目: {len(reg)}')
    print(f'\nMISSING（dex 有、registry 没有）: {len(missing)}')
    for n, s in missing: print(f'  {n:28s} {s}')
    print(f'\nEXTRA（registry 有、dex 没有）: {len(extra)}')
    for n, s in extra: print(f'  {n:28s} {s or ""}')
    print(f'\nMATCH: {len(matched)}')

if __name__ == '__main__':
    main()
