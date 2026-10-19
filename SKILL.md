---
name: android-to-vita
description: 把 Android 原生游戏移植到 PS Vita（so-loader / vitaGL / FalsoJNI）的完整方法论。适用于"加载 Android ARMv7 .so 并在 Vita 上原生运行"类项目：可行性体检、加载器骨架、图形与纹理、JNI/Java 层、GUI(SWF)、音频、崩溃分析、CI 与版本管理。
---

# Android → PS Vita 移植 Skill

> 这不是"通用移植教程"，而是从《The Settlers HD》真实移植中沉淀的可复用流程。
> 核心原则：**先建立执行链，再验证假设；每条结论必须能指到具体地址、日志行或数据字节。**

## 何时使用

- 手上有一个 Android 游戏 APK，游戏逻辑在 `lib*.so`（ARMv7）
- 目标是在 HENkaku/Ensō 的 PS Vita 上原生运行，而不是模拟
- 资源是明文（`.pvr` / `.ogg` / `.bar` 等），不依赖 AAssetManager 或加密包

不适用：Unity/UE 大型引擎（IL2CPP 除外）、依赖 Google Play 服务、资源加密。


## 通用方法与游戏专属的边界

本 Skill 只收录**可迁移到其他项目**的做法。写作时严格区分：

| 类型 | 例子 | 归属 |
|---|---|---|
| 通用方法 | "压缩纹理先自解码验证，再怀疑 vitaGL" | 本 Skill |
| 游戏专属补丁 | `device_type` 在 `0x98372208`，要写回 5 | 项目知识库 `docs/kb/` |
| 资源命名规则 | `texture0_960.pvr` / `0NNN.ogg` | 项目知识库 |
| 一次性实验 | 某个全局值试出来的结果 | 项目知识库 + 案例文档 |

**禁止**把某个游戏的函数地址、资源命名、常量刻度写成"标准做法"。
案例可以引用具体数字，但必须标注"这是某游戏的取值，不是通用规则"。

候选资料先放 `candidates/`，跨场景验证后才晋升到本文档。

## 核心工作流程

```
① 收集事实（现象、日志、dump、资源头）
        ↓
② 静态分析还原原版行为（DEX / ARM / 调用链 / 数据流）
        ↓
③ 写成"兼容层规格"（函数、参数、状态、生命周期）
        ↓
④ 最小兼容实现
        ↓
⑤ 运行日志 + 实机测试验证
```

**静态分析与运行验证互补，不能互相替代**：

- 静态分析告诉你"原版应该怎样"，不能证明"实机就是这样运行的"
- 运行日志告诉你"这次实机发生了什么"，不能证明"原版设计如此"
- 只有两者一致时，结论才能标为"已确认"

参见 [docs/00-static-reverse-engineering.md](docs/00-static-reverse-engineering.md)。

## 总原则

1. **先收集事实，再还原行为**：拿到现象先查 DEX/ELF/资源，不急着改代码。
2. **证据分级**：每条结论标注【静态确认】【日志确认】【推测】【未确认】，禁止把推测写成结论。
3. **一次只改一个变量**：每版只解决一个问题，版本号写进文件名。
4. **静态推断 ≠ 运行事实**：反编译得到的行为要用日志/实机验证后才算闭环。
5. **保持稳定基线**：新实验失败时能立刻退回上一个可用版本。
6. **固定地址是隐患**：任何硬编码的映射基址都要有候选探测与错误码日志。
7. **通用与专属分离**：函数地址、结构体偏移、资源 ID 属于具体游戏；分析方法和判据才属于本 Skill。

## 文档与工具索引

| 类型 | 文件 | 用途 |
|---|---|---|
| 总流程 | [docs/00-static-reverse-engineering.md](docs/00-static-reverse-engineering.md) | 事实收集 → 静态还原 → 兼容规格 → 最小实现 → 验证 |
| DEX | [docs/00a-dex-analysis.md](docs/00a-dex-analysis.md) | APK 解包、baksmali、方法表、JNI 签名 |
| ARM | [docs/00b-arm-disassembly.md](docs/00b-arm-disassembly.md) | ELF 符号、反汇编、xref、Thumb/字面量陷阱 |
| 调用链 | [docs/00c-call-graph-and-dataflow.md](docs/00c-call-graph-and-dataflow.md) | 调用关系、结构体字段、门控与状态机 |
| 行为还原 | [docs/00d-original-behavior-reconstruction.md](docs/00d-original-behavior-reconstruction.md) | 把反编译结果写成兼容层规格 |
| 案例 | [cases/](cases/) | 真实问题的完整记录（含验证状态） |
| 工具 | [tools/](tools/) | APK/DEX/ELF/纹理/dump/日志 脚本 |

## 阶段 0：可行性体检（不改代码）

目标：判断值不值得做，以及工作量级别。

- `readelf -d` / 解析 `DT_NEEDED`：是否只有 `libc/libstdc++/libm/libGLESv2/libdl/liblog`？
  出现 `libOpenSLES`、`libmedia`、`libcrypto`、`libunity` 要单独评估。
- 符号表是否完整（`nm -D` 有大量 C++ mangled 符号 = 好事）
- Java 类数量与 native 方法数量（`classes.dex`）
- 资源是否明文：随机抽几个文件看头部（PVR/DXT/OGG/JSON）
- 是否有 `AAssetManager`（有则要重写资源层）
- 入口：`JNI_OnLoad`、`Java_*_nativeInit`、`nativeRender` 等

产出：`docs/findings-<game>.md`，含"能做/难度/主要风险"。

## 阶段 1：加载器骨架

```
so_util_init → so_file_load(base) → so_relocate → resolve_imports
→ so_flush_caches → so_initialize → 调用 JNI_OnLoad / nativeInit
```

要点：

- 主库基址**不要硬编码**：准备候选数组（如 `0x98000000/0x90000000/0x88000000`），
  每个失败都打印 `so_file_load` 返回码。
- 次级库（如 `libStormGLOFT.so`）单独加载，必要时跳过它的 `JNI_OnLoad`（配置项）。
- `_newlib_heap_size_user` 不要贴着机器上限；256MB 已是擦边值，128MB 更稳。
- 每个阶段打一行 success 日志，崩溃时能定位到阶段。

## 阶段 2：图形（GLES → vitaGL）

- 用 vitaGL 提供 GLES1/2 符号；`gl_init()` 放在游戏 nativeInit 之前。
- 记录每帧统计：`draws / tex / glErr / lastTex`，异常时一眼看出是"没画"还是"画错"。
- 常见坑：
  - 分辨率/视口与游戏假设不一致 → 黑边或错位
  - 游戏自己重置显卡相关全局（见案例 `device_type`）
  - 压缩纹理路径不可靠（见阶段 3）

## 阶段 3：纹理（最容易出"马赛克"）

判断顺序：

1. **先确认文件格式**：解析容器头（BTEX v0/v4、PVR、ASTC），不要靠扩展名。
2. **再确认游戏选了哪条解码路径**：很多引擎按 `device_type` 分派
   （DXT / PVRTC / ATC / ETC）。全局变量被游戏初始化重置是常见根因。
3. **最后才怀疑 vitaGL**：如果同一份数据"自解码正常、交给 vitaGL 就花"，
   就在 `glCompressedTexImage2D` 拦截，CPU 解码成 RGBA 再 `glTexImage2D`。
   PVRTC 可复用游戏自带的 `PVRTCDecompress`（导出符号，查调用点确认参数）。

操作要点：

- Hook `glCompressedTexImage2D` 时**只记录前 N 次**，否则日志爆炸。
- 自写解码器要先离线验证：导出单张 PNG 看内容，再进游戏。
- 尺寸字段可能被读反（v4 容器）；"上传尺寸"和"文件头尺寸"不一致时优先怀疑这里。

## 阶段 4：JNI / Java 层

- 用 FalsoJNI 提供 `JNIEnv`；**方法 ID 必须从 1 开始**，0 保留为非法。
  否则查找失败返回的 NULL 会被分发成 id 0 的方法，产生"莫名其妙的高频调用"。
- 从 dex 精确提取方法表（见 `tools/dex_class_methods.py`）：
  名称、签名、是否 static/native，一个都不能猜。
- 查找日志与调用日志分开：
  - `AUDIO_LOOKUP class=... name="..." sig="..." result=FOUND/MISS`
  - `AUDIO_EVENT kind name(id=..) sig="..." args=(按 ABI 解析)`
- 参数必须按签名解析：`I`→int、`F`→**double**（varargs 提升）、`J`→long long、`L..;`→指针。
- 高频方法按 `(id+参数)` 哈希去重，避免刷爆日志配额。

## 阶段 5：GUI（gameswf / SWF）

1. 先确认 UI 是 **SWF 渲染**还是自绘 2D：找 `CGUIManager::draw` 这类入口，
   看它是不是只调 `RenderFX::Render()`。
2. SWF 里的位图常常是**占位**（只有头没有像素），真实图集由游戏按名字加载。
3. 纹理名比较失败是高频根因：
   - 游戏在 960 宽度下查 `texture0_960.pvr`，而数据包只有 `texture0.pvr`
   - 比较用 `strstr` 时后缀永远匹配不上 → 全部跳过 → 菜单空白
   - 修法：只在比较时去掉 `_960`/`_854` 后缀，不动注册名与资源路径
4. 验证方式：hook 两道门控（查找/判断），按调用顺序推断分支，不要额外调用它们。

## 阶段 6：音频

先判断音频在哪里：

- `DT_NEEDED` 没有 `libOpenSLES`/`libmedia` → 音频几乎一定在 **Java 层**（MediaPlayer/SoundPool）
- 反编译 dex 拿到 Java 方法的真实签名（smali 最可靠）
- 播放接口通常只有一个（本项目是 `playSoundBig(IFI)V`，"Big" 命名有误导）
- 音量常有隐含刻度（本项目 `gain = vol / 70.0`），必须从 smali 里读出来
- 数据格式先离线验证：导出 WAV 试听，**用耳朵确认采样率/声道**
- Vita 侧：stb_vorbis 解码 → 重采样到 48k → 软件混音 → `sceAudioOut`
- 第一版只做一个闭环（一个音效），不要一上来做多路混音与音乐流

## 阶段 7：崩溃与 dump 分析

- 日志停在某一行 = 崩溃发生在下一阶段，先看阶段顺序。
- `psp2dmp` 是 gzip 压缩的 ELF core，含 `THREAD_REG_INFO`、`MODULE_INFO`、`BUDGET_INFO`。
- 看三件事：崩溃 PC 落在哪个模块、各线程寄存器是否**每次相同**（确定性 vs 随机）、
  内存分区 used/free。
- 若两次 dump 寄存器完全一致 → 确定性路径，优先查逻辑而非"内存不足"。
- 用户在系统工具里改过内存/插件后出问题：先重启，再重装应用（系统登记项可能被写坏）。

## 阶段 8：CI 与版本

- 编译放 GitHub Actions（VitaSDK-softfp），产物 VPK artifact + Release。
- 文件名带版本号；每个版本写 CHANGELOG（改了什么、依据是什么）。
- 稳定版本打 tag + Release，附 VPK 与说明。
- 探针全部做成配置开关，正式版默认关闭。

## 根因速查表（来自真实案例）

| 现象 | 常见根因 | 验证方式 |
|---|---|---|
| 整屏黑 | 全局 `device_type` 被重置，选错解码器 | 每帧打印该全局值 |
| 精灵/UI 马赛克 | 压缩纹理由 vitaGL 解码出错 | 拦截压缩上传改 CPU 解码 |
| 菜单空白但文字正常 | SWF 位图靠外部图集，名字不匹配 | 记录查找/比较两道门控 |
| 音频全静音 | Java 方法未注册，调用塌缩到 id 0 | 在 JNI 分发处按 id 打印 |
| 改设置后游戏打不开 | 系统登记项被工具写坏 | 重装应用；对比 eboot 哈希 |
| 某版本突然卡住 | 日志刷屏阻塞 | 统计每帧日志行数 |

## 检查表

- [ ] 可行性报告已写，依赖与资源格式已确认
- [ ] 加载器每个阶段都有 success 日志
- [ ] 所有固定基址都有候选与错误码
- [ ] 每帧统计（draw/tex/glErr）可开关
- [ ] 纹理格式用头部字节确认，不靠扩展名
- [ ] JNI 方法表来自 dex，ID 从 1 开始
- [ ] 高频日志有去重与上限
- [ ] 稳定版本有 tag + Release + VPK
