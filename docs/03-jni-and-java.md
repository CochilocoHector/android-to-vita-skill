# 03 · JNI 与 Java 层

## 1. 为什么要精确的方法表

FalsoJNI 用"名称 → id"的表来解析 Java 方法。
如果游戏请求的方法不在表里，`GetStaticMethodID` 返回 NULL(0)，
而 0 若被分配给某个真实方法（例如 `resetSound`），
**所有缺失方法的调用都会塌缩成那个方法**，日志表现为高频、参数混乱的调用。

## 2. 铁律：id 从 1 开始

```c
{ 1, "init", METHOD_TYPE_VOID },
{ 2, "playSoundBig", METHOD_TYPE_VOID },
...
```

分发处：

```c
if (id <= 0) {
    l_info("AUDIO_INVALID %s methodID=%d (lookup 失败，已丢弃)", kind, id);
    return;
}
```

## 3. 从 dex 取方法表

```bash
python3 tools/dex_class_methods.py classes.dex 'Lcom/xxx/GLMediaPlayer;'
```

输出：`static/native`、名称、JNI 签名。**签名不能猜。**

也可以用 smali 看实现（关键逻辑必须看）：

```bash
java -jar baksmali.jar d classes.dex -o out
# out/com/.../GLMediaPlayer.smali
```

## 4. 参数解析（ARM AAPCS）

| 签名 | C 读取方式 |
|---|---|
| `I Z S B C` | `va_arg(args, int)` |
| `F` | `va_arg(args, double)` ← varargs 提升 |
| `J` | `va_arg(args, long long)` |
| `L...;` | `va_arg(args, void *)` |

## 5. 日志设计

```
AUDIO_LOOKUP class=... name="playSoundBig" sig="(IFI)V" result=FOUND
AUDIO_EVENT void playSoundBig(id=8) sig="(IFI)V" args=(287,50.000,1)
AUDIO_INVALID void methodID=0 (lookup 失败，已丢弃)
```

- 查找最多记 32 条 MISS + 80 条 FOUND
- 调用按 `(id + 参数哈希)` 去重，最多 96 条
- 每个已注册方法都要有默认处理器，避免 `method ID not found` 刷屏
