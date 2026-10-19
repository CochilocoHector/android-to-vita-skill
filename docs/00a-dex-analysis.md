# 00a · APK / DEX 静态分析

## 1. APK 结构速览

```bash
python3 tools/apk_info.py game.apk
```

输出：dex 数量、每 ABI 的 .so、assets 大小、res/raw 资源、是否可能依赖 AAssetManager。

**判断**：

- 有 `lib/armeabi-v7a/lib*.so` 且很大 → 逻辑在 native
- `classes*.dex` 很大而 so 很小 → 逻辑在 Java（移植难度高）
- assets 里有大资源 → 需要重写资源层

## 2. 反编译 DEX

```bash
java -jar baksmali.jar d classes.dex -o out
# 结果: out/com/your/game/Class.smali
```

- `baksmali` 适合**看实现**（控制流、常量、方法调用）
- `jadx` 适合**快速浏览**（反编译成 Java，但可能失真）
- 两者冲突时以 smali 为准

## 3. 提取方法表

```bash
python3 tools/dex_class_methods.py classes.dex 'Lcom/your/game/MediaPlayer;'
```

输出 `static/native/public`、名称、JNI 签名。**签名必须从这里来，不能猜。**

## 4. JNI 签名速查

| 类型 | 签名 |
|---|---|
| void/boolean/byte/char/short/int/long/float/double | `V Z B C S I J F D` |
| 对象 | `Lcom/your/Class;` |
| 数组 | `[I`、`[B`、`[Ljava/lang/String;` |

例：`playSoundBig(int, float, int) -> void` = `(IFI)V`。

## 5. 判断 static 还是 virtual

- smali 方法头有 `static` → 游戏会走 `GetStaticMethodID` + `CallStatic*Method`
- 没有 `static` → `GetMethodID` + `Call*Method`

**陷阱**：只给 `GetMethodID` 埋点会完全看不到 static 方法的解析（本项目踩过）。

## 6. native 方法如何注册

两种：

1. **按名注册**：`.so` 导出 `Java_com_pkg_Class_method`
   ```bash
   nm -D --defined-only libGame.so | grep Java_
   ```
2. **RegisterNatives**：`.so` 里用字符串表 + 函数指针注册
   ```bash
   strings libGame.so | grep -E "^[a-zA-Z_]+$" | head
   ```
   DEX 里方法声明为 native，但 .so 没有对应 `Java_*` 导出 → 大概率是 RegisterNatives。

## 7. 兼容层差异检测

```bash
# 1) 导出 dex 方法清单
python3 tools/dex_class_methods.py classes.dex 'Lcom/x/Y;' > /tmp/dex.txt

# 2) 准备兼容层注册表（每行: name sig）
cat > /tmp/reg.txt <<'TXT'
playSound (IIF)V
playSoundBig (IFI)V
TXT

# 3) 差异
python3 tools/jni_diff.py /tmp/dex.txt /tmp/reg.txt
```

输出 `MISSING`（dex 有、兼容层没注册）与 `EXTRA`（注册了但 dex 没有）。

## 8. 看实现时的常见陷阱

| 陷阱 | 例子 | 处理 |
|---|---|---|
| 常量刻度藏在除法里 | `n = vol / 70.0f` | 搜 `div-float` 与 `sget ... q:F` |
| 数组按 id 索引 | `d[id]`、`a[id]` | 说明每 id 一个实例 |
| 字符串拼接生成文件名 | `"000"+id+".ogg"` | 还原所有分支（<10/<100/…） |
| 异常吞掉 | `try/catch Exception` | 失败时可能静默 |
| 日志开关 | `if (o) println` | 不能靠日志判断是否执行 |

## 9. 证据记录

```markdown
- 方法：playSoundBig(int id, float vol, int loop)
- 来源：[DEX] GLMediaPlayer.smali
- 证据：`n = p1 / q`，`q = 70.0f`（<clinit> 中 `const/high16 0x428c0000`）
- 状态：✅
```
