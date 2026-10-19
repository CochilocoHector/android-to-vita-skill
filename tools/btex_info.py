#!/usr/bin/env python3
"""解析 BTEX / PVR 纹理容器头。

用法: python3 btex_info.py textureN.pvr [...]
"""
import struct, sys


def info(path):
    d = open(path, 'rb').read()
    n = len(d)
    print('==', path.split('/')[-1], f'({n} bytes)')
    w = h = 0
    if d[:4] == b'PVR!':
        off = 0
    elif d[:4] == b'BTEX':
        tag = d[4:8].decode('latin1', 'replace')
        if d[8:16] == b'BTEXdxtr':
            w, h = struct.unpack_from('<HH', d, 0x10)
            size = struct.unpack_from('<I', d, 0x14)[0]
            print(f'  v0 container tag={tag} {w}x{h} dataSize={size} data@0x18')
            print(f'  位深: {size * 8 / (w * h):.2f} bpp')
            return
        off = struct.unpack_from('<I', d, 8)[0]
        w = struct.unpack_from('<I', d, 0x0C)[0]
        h = struct.unpack_from('<I', d, 0x10)[0]
        print(f'  v4 container tag={tag} {w}x{h} pvr@{off:#x}')
    else:
        print('  未知格式:', d[:8])
        return

    if d[off:off + 4] != b'PVR!':
        print('  未找到 PVR! 头')
        return
    data = n - (off + 8)
    print(f'  内嵌 PVR! @0x{off:x}，数据起点 0x{off+8:x}，长度 {data}')
    if w and h:
        bpp = data * 8 / (w * h)
        print(f'  位深: {bpp:.2f} bpp')
        if abs(bpp - 4) < 0.01:
            print('  可能格式: PVRTC 4bpp')
        elif abs(bpp - 2) < 0.01:
            print('  可能格式: PVRTC 2bpp')
        elif abs(bpp - 8) < 0.01:
            print('  可能格式: 8bpp（非标准 PVRTC，需进一步确认）')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        info(p)
