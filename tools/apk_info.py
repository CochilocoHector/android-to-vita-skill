#!/usr/bin/env python3
"""APK 结构速览：dex、ABI、SO、assets、res/raw 资源。

用法: python3 apk_info.py game.apk
"""
import sys, zipfile, collections, os

def main(path):
    z = zipfile.ZipFile(path)
    infos = z.infolist()
    print(f'== {os.path.basename(path)}  ({os.path.getsize(path)/1048576:.1f} MB, {len(infos)} entries)')

    dex = [i for i in infos if i.filename.endswith('.dex')]
    if dex:
        print('DEX:')
        for i in sorted(dex, key=lambda x: x.filename):
            print(f'  {i.filename:24s} {i.file_size/1048576:6.2f} MB')

    libs = collections.defaultdict(list)
    for i in infos:
        if i.filename.startswith('lib/') and i.filename.endswith('.so'):
            abi = i.filename.split('/')[1]
            libs[abi].append((i.filename.split('/')[-1], i.file_size))
    if libs:
        print('Native libs:')
        for abi in sorted(libs):
            total = sum(s for _, s in libs[abi]) / 1048576
            print(f'  [{abi}] {len(libs[abi])} 个, {total:.1f} MB')
            for n, s in sorted(libs[abi], key=lambda x: -x[1])[:6]:
                print(f'      {n:34s} {s/1048576:6.2f} MB')

    assets = [i for i in infos if i.filename.startswith('assets/')]
    if assets:
        total = sum(i.file_size for i in assets) / 1048576
        print(f'assets/: {len(assets)} 个, {total:.1f} MB')
        for i in sorted(assets, key=lambda x: -x.file_size)[:5]:
            print(f'    {i.filename[:56]:56s} {i.file_size/1048576:6.2f} MB')
        print('  提示: assets 大 → 可能需要重写 AAssetManager 资源层')

    raw = [i for i in infos if i.filename.startswith('res/raw/')]
    if raw:
        print(f'res/raw/: {len(raw)} 个')
        for i in sorted(raw, key=lambda x: -x.file_size)[:5]:
            print(f'    {i.filename[:56]:56s} {i.file_size:8d} B')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
