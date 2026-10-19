#!/usr/bin/env python3
"""ARM ELF 概览：依赖、导入、导出、重定位、PLT 桩映射。

用法: python3 elf_info.py libGame.so [--exports] [--plt strstr]
"""
import sys, struct

def parse(path):
    d = open(path, 'rb').read()
    if d[:4] != b'\x7fELF':
        raise SystemExit('不是 ELF')
    phoff = struct.unpack_from('<I', d, 28)[0]
    shoff = struct.unpack_from('<I', d, 32)[0]
    phentsize = struct.unpack_from('<H', d, 42)[0]
    phnum = struct.unpack_from('<H', d, 44)[0]
    shentsize = struct.unpack_from('<H', d, 46)[0]
    shnum = struct.unpack_from('<H', d, 48)[0]
    shstrndx = struct.unpack_from('<H', d, 50)[0]

    secs = []
    for i in range(shnum):
        o = shoff + i * shentsize
        nm, typ, fl, addr, off, size, link, info, al, ent = struct.unpack_from('<IIIIIIIIII', d, o)
        secs.append(dict(name=nm, type=typ, addr=addr, off=off, size=size, link=link))
    shstr = secs[shstrndx]
    def sname(nm):
        e = d.index(b'\0', shstr['off'] + nm); return d[shstr['off'] + nm:e].decode('latin1')
    for sec in secs:
        sec['sname'] = sname(sec['name'])
    dyn = next((s for s in secs if s['type'] == 6), None)   # SHT_DYNAMIC
    dsym = next((s for s in secs if s['type'] == 11), None) # SHT_DYNSYM
    relplt = next((s for s in secs if s['sname'] == '.rel.plt'), None)
    if relplt is None:
        relplt = next((s for s in secs if s['type'] == 9), None)
    plts = next((s for s in secs if s['sname'] == '.plt'), None)
    strtab = secs[dsym['link']] if dsym else None

    def cstr(off):
        e = d.index(b'\0', off); return d[off:e].decode('latin1')

    needed, plt_syms = [], []
    if dyn:
        strv = secs[dyn['link']]
        for i in range(dyn['size'] // 8):
            tag, val = struct.unpack_from('<iI', d, dyn['off'] + i * 8)
            if tag == 1:
                needed.append(cstr(strv['off'] + val))
    exports, imports = [], []
    if dsym and strtab:
        n = dsym['size'] // 16
        for i in range(n):
            o = dsym['off'] + i * 16
            nameoff, value, size, info, other, shndx = struct.unpack_from('<IIIBBH', d, o)
            name = cstr(strtab['off'] + nameoff)
            if shndx == 0:
                imports.append((name, 0))
            elif info & 0xf:
                exports.append((name, value))
    if relplt and dsym and strtab:
        for i in range(relplt['size'] // 8):
            r_off, r_info = struct.unpack_from('<II', d, relplt['off'] + i * 8)
            sym = r_info >> 8
            o = dsym['off'] + sym * 16
            nameoff = struct.unpack_from('<I', d, o)[0]
            stub = (plts['addr'] + 20 + i * 12) if plts else 0
            plt_syms.append((stub, r_off, cstr(strtab['off'] + nameoff)))
    return dict(needed=needed, exports=exports, imports=imports, plt=plt_syms, secs=secs)

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    path = sys.argv[1]
    show_exports = '--exports' in sys.argv
    want_plt = None
    if '--plt' in sys.argv:
        want_plt = sys.argv[sys.argv.index('--plt') + 1]
    e = parse(path)
    print(f'== {path}')
    print('NEEDED:', ' '.join(e['needed']))
    print(f'导出符号: {len(e["exports"])}  导入符号: {len(e["imports"])}  PLT 桩: {len(e["plt"])}')
    if want_plt:
        print(f'--- 含 "{want_plt}" 的 PLT 桩 ---')
        for stub, got, name in e['plt']:
            if want_plt in name:
                print(f'  stub 0x{stub:06x}  GOT 0x{got:06x}  -> {name}')
    if show_exports:
        print('--- 导出（前 40） ---')
        for name, val in e['exports'][:40]:
            print(f'  0x{val:08x}  {name}')

if __name__ == '__main__':
    main()
