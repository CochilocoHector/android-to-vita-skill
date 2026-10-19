# 通用方法候选

> 每条格式：**结论 / 判据 / 验证于 / 证据 / 状态**

---

## G-01 先看依赖再谈可行

**结论**：`DT_NEEDED` 只有 libc/libstdc++/libm/GLES/dl/log 时，native 移植通常可行。
**判据**：出现 libOpenSLES/libmedia → 音频在 Java；出现 libunity/libil2cpp → 另算。
**验证于**：Settlers HD、GTA SA 类项目
**状态**：verified

## G-02 基址必须候选化

**结论**：不要硬编码 so_file_load 的基址；用候选数组并对每个失败打印返回码。
**判据**：同一设备不同内存配置下，固定地址可能不可用或与其他分配冲突。
**验证于**：Settlers HD（Storm 库 5 个候选）
**状态**：verified

## G-03 每阶段一行 success 日志

**结论**：加载器每个阶段打一行 success，崩溃时按日志停点定位阶段。
**验证于**：Settlers HD（"停在 Storm JNI_OnLoad 之后"→ 定位到 gl_init）
**状态**：verified

## G-04 压缩纹理：先自解码验证，再怀疑 vitaGL

**结论**：同一份数据"自解码正常、交给 vitaGL 就花"时，在 glCompressedTexImage2D 拦截并 CPU 解码。
**判据**：地形/单一纹理自解码显示正常，而精灵/UI 花屏。
**验证于**：Settlers HD（DXT5 与 PVRTC 均采用）
**状态**：verified

## G-05 JNI 方法 ID 从 1 开始

**结论**：FalsoJNI 里 0 必须保留为非法；查找失败的 NULL 不能映射到真实方法。
**判据**：日志出现某方法高频刷屏且参数混乱 → 很可能所有缺失方法塌缩到 id 0。
**验证于**：Settlers HD（补齐 43 个方法后一次定位）
**状态**：verified

## G-06 方法表必须来自 dex

**结论**：方法名与签名从 dex/smali 提取，禁止凭字符串猜测。
**判据**：smali 能看到真实控制流（如音量 `/70.0`、文件名规则）。
**验证于**：Settlers HD（baksmali 反编译 getSoundFileName/playSoundBig）
**状态**：verified

## G-07 高频日志按 (id,参数) 去重

**结论**：每个探针独立限流 + 哈希去重，防止刷屏拖死游戏。
**验证于**：Settlers HD（resetSound 刷屏吃掉全部配额）
**状态**：verified

## G-08 SWF UI 的图集名可能带分辨率后缀

**结论**：游戏按宽度选图集名（如 `_960`），数据包可能只有无后缀版本；比较逻辑会导致全部跳过。
**判据**：UI 文字/矢量正常，位图与背景空白。
**验证于**：Settlers HD（strstr 后缀不匹配）
**状态**：verified（单一项目，但机制通用）

## G-09 dump 对比判定确定性

**结论**：两次崩溃寄存器完全一致 → 确定性路径，优先查逻辑而非内存压力。
**验证于**：Settlers HD（两次 dump 仅线程 id 不同）
**状态**：verified

## G-10 系统工具改内存后的故障先重启再重装

**结论**：应用文件哈希未变却无法启动时，考虑系统登记项被工具写坏。
**验证于**：Settlers HD（VitaToolbox 285MB 事故）
**状态**：probable（单一案例，可能是平台特性）

## G-11 音频采样率可能逐文件不同

**结论**：同一个目录下的音频文件可能混用采样率（如 22050/44100），必须按文件头解码并逐样本重采样。
**判据**：日志里同一接口加载的文件出现不同 `@rate`；统一重采样会变调或变速。
**验证于**：Settlers HD（12 条 22050、3 条 44100）
**状态**：verified
