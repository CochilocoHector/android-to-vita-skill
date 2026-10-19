# 01 · 可行性体检与加载器骨架

## 1. 先看依赖

```bash
readelf -d lib/armeabi/libGame.so | grep NEEDED
```

- 只有 `libc libstdc++ libm libGLESv1_CM libGLESv2 libdl liblog` → 很干净
- 出现 `libOpenSLES` / `libmedia` → 音频可能在 native（否则在 Java）
- 出现 `libcrypto` / `libssl` → 需要移植或桩掉网络/加密
- 出现 `libunity` / `libil2cpp` → 工作量完全不同，先评估

## 2. 符号表

```bash
nm -D --defined-only lib/armeabi/libGame.so | wc -l
nm -D --defined-only lib/armeabi/libGame.so | grep -c " _ZN"
```

C++ mangled 符号多 = 逻辑在 native，可移植性好。
只有 `JNI_OnLoad` 和少量入口 = 逻辑在 Java，基本不可行。

## 3. Java 侧

`classes.dex` 里类数量、`native` 方法数量、JNI 入口名：

```bash
python3 tools/dex_class_methods.py classes.dex 'Lcom/your/game/Main;'
```

## 4. 资源

随机抽文件看头部：

- `BTEXdxtr` / `BTEXpvr` / `PVR!` → 纹理容器
- `OggS` → Vorbis
- `RIFF` → WAV
- `PK` / 加密头 → 麻烦

## 5. 加载器骨架

```c
so_util_init();
int r = so_file_load(&mod, path, BASE_CANDIDATES[0]);
so_relocate(&mod);
resolve_imports(&mod);
so_flush_caches(&mod);
so_initialize(&mod);
```

### 基址选择

**不要硬编码单一地址。** 用候选数组，每个失败打印返回码：

```c
static const uintptr_t candidates[] = { 0x98000000, 0x90000000, 0x88000000 };
for (...) {
    int res = so_file_load(&mod, path, candidates[i]);
    if (res < 0) { l_warn("load at 0x%08x failed: 0x%08x", candidates[i], res); continue; }
    ...
}
```

### 堆大小

```c
int _newlib_heap_size_user = 128 * 1024 * 1024;  // 256MB 已在 256MB 分区上擦边
```

### 日志节点

每个阶段一行 success，崩溃时能立刻定位：

```
Settings loaded / SO relocated / SO imports resolved / SO patched
SO caches flushed / SO initialized / OpenGL preloaded / FalsoJNI initialized
```

## 6. 常见失败

| 现象 | 原因 | 处理 |
|---|---|---|
| `so_file_load` 返回 0x80024804 | 地址不可用/被占用 | 换候选地址 |
| 加载成功但立刻崩 | 需要另一个库先初始化 | 调整加载顺序 |
| 初始化后黑屏 | GL 上下文未建立 | `gl_init()` 提前 |
