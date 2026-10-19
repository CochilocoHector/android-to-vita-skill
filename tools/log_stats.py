#!/usr/bin/env python3
"""日志事件统计：匹配次数、唯一行、重复最多的行。

用法:
  python3 log_stats.py log.txt --pattern AUDIO_EVENT
  python3 log_stats.py log.txt --pattern "playSoundBig" --top 20
"""
import sys, re, collections

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    path = sys.argv[1]
    pattern = None
    top = 10
    if '--pattern' in sys.argv:
        pattern = sys.argv[sys.argv.index('--pattern') + 1]
    if '--top' in sys.argv:
        top = int(sys.argv[sys.argv.index('--top') + 1])
    rx = re.compile(pattern) if pattern else None

    total = 0
    matched = 0
    uniq = collections.Counter()
    for line in open(path, 'r', encoding='utf-8', errors='replace'):
        total += 1
        s = re.sub(r'\x1b\[[0-9;]*m', '', line).rstrip('\n')
        if rx and not rx.search(s):
            continue
        matched += 1
        uniq[s.strip()] += 1

    print(f'文件: {path}')
    print(f'总行数: {total}')
    if rx:
        print(f'匹配 "{pattern}": {matched} 行, 唯一 {len(uniq)} 种')
    print(f'\n出现最多的 {top} 行:')
    for line, n in uniq.most_common(top):
        print(f'  {n:6d}  {line[:150]}')

if __name__ == '__main__':
    main()
