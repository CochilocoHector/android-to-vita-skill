# 00b · ARM ELF 与反汇编

## 1. 先看 ELF

```bash
python3 tools/elf_info.py libGame.so
```

输出：

- `DT_NEEDED`（依赖库）
- 导出符号（`nm -D --defined-only`）
- 未定义导入（`nm -D -u`）
- 重定位数量与 PLT 映射（用于把 `bl 0xf3f68` 还原成 `strncmp`）

## 2. 反汇编

```bash
llvm-objdump -d libGame.so > dis.txt
# 或
arm-none-eabi-objdump -d libGame.so > dis.txt
```

- 文件很大时按符号切段，不要一次读全
- `-d` 不含数据段；查字符串/表用 `xxd` 或 `strings -t x`

## 3. 地址换算

| 用途 | 公式 |
|---|---|
| 运行时地址 | `0x80000000 + 偏移`（本类项目主库基址由加载器决定） |
| 文件偏移 → 虚拟地址 | 读程序头，找 `p_offset <= off < p_offset+p_filesz` 的段，`va = p_vaddr + (off - p_offset)` |
| 虚拟地址 → 文件偏移 | 反向 |

**陷阱**：`.so` 的 `e_phoff` 段表里可能有非标准段，别用固定偏移猜测。

## 4. Thumb / ARM 判断

- 符号地址最低位为 1 → Thumb
- `bl 0x146c5c` 跳转后目标按 Thumb 解释（Cortex-A9 常见）
- Hook 跳转必须保持状态位：`0x9814487d`（带 1）而不是 `0x9814487c`

## 5. 反汇编阅读顺序

1. 找函数边界：`push {..., lr}` 开头，`pop {..., pc}` 结尾
2. 看参数：`r0-r3`，第 5 个起在栈上
3. 看 early return：`cmp/beq` 到 `pop`
4. 看调用：`bl`/`blx`，间接调用看 vtable 或函数指针
5. 看全局：`ldr rX,[pc,#imm]` → 字面量地址 → GOT 槽 → 重定位 addend

## 6. PC 相对寻址陷阱（真实踩过）

Thumb 下 `ldr rX,[pc,#imm]`：

```
PC = (指令地址 + 4) 按 4 对齐
字面量地址 = PC + imm
```

`add rX, pc`：

```
PC = 指令地址 + 4（16 位指令 +4；32 位指令 +4）
```

算错会导致解析到相邻的 GOT 槽，读到错误全局变量（本项目曾把 `device_type` 读成别的变量）。

## 7. 找交叉引用

```bash
python3 tools/arm_xrefs.py libGame.so 0x13b9ac
```

同时输出：

- 最近符号 + 偏移（`0x13b9ac = CGUIManager::IsNeedToLoadTexture + 0x0`）
- 反汇编中 `bl 0x13b9ac` 的调用点
- 字面量中等于该地址的槽位（间接引用）

**判据**：直接 `bl` = 静态调用；经 GOT/vtable = 动态调用，需要看运行时值。

## 8. Hook 安全性检查

在函数入口写 8 字节跳转前，检查前 4 条指令：

| 情况 | 能否整段搬移 |
|---|---|
| `push` / `mov` / `add sp` | ✅ 安全 |
| `ldr rX,[pc,#imm]` | ❌ 字面量地址会变 |
| `bl` / 条件跳转 | ❌ 目标偏移会变 |

不安全时：手写桩，按绝对地址重建这几条指令，再跳到 `entry+8`。

## 9. 证据记录

```markdown
- 函数：CGUIManager::IsNeedToLoadTexture
- 来源：[ASM] libGame.so 0x13b9ac
- 证据：0x13b9de `blx 0xf45d4`（PLT → strstr）
- 状态：✅
```
