# 移植检查表

## 阶段 0：可行性
- [ ] `DT_NEEDED` 已列出，无音频/加密库异常
- [ ] 符号表完整（大量 C++ mangled 符号）
- [ ] Java 类与 native 方法数量已统计
- [ ] 资源抽样确认明文（PVR/OGG/JSON…）
- [ ] 无 AAssetManager 依赖（或已规划重写）

## 阶段 1：加载器
- [ ] 每个阶段（relocate/imports/patched/init）都有 success 日志
- [ ] 所有固定基址都有候选数组 + 错误码日志
- [ ] `_newlib_heap_size_user` 未贴着机器上限
- [ ] 次级库的 JNI_OnLoad 可跳过（配置项）
- [ ] 首次运行能打印游戏 cwd 与关键全局值

## 阶段 2-3：图形与纹理
- [ ] 每帧统计（draw/tex/glErr/lastTex）可开关
- [ ] 纹理格式用头部字节确认，不靠扩展名
- [ ] 已知全局（如 device_type）每帧钉住并记录
- [ ] 压缩纹理解码路径已确认（DXT/PVRTC/ATC）
- [ ] 自解码结果先离线转 PNG 验证，再进游戏

## 阶段 4：JNI
- [ ] 方法表来自 dex（名称+签名+static/native）
- [ ] 方法 ID 从 1 开始，0 为非法
- [ ] 查找失败有 MISS 日志，调用有 INVALID 日志
- [ ] 参数按签名解析（F→double）
- [ ] 高频方法按 (id,参数) 去重
- [ ] 所有已注册方法都有默认处理器，避免 not found 刷屏

## 阶段 5：GUI
- [ ] 确认 UI 是 SWF 渲染还是自绘
- [ ] SWF 位图是否只有占位头（无像素）
- [ ] 图集名比较逻辑已确认（是否带分辨率后缀）
- [ ] 两道门控按调用顺序推断，不额外调用

## 阶段 6：音频
- [ ] 确认音频在 native 还是 Java
- [ ] Java 方法签名来自 dex/smali
- [ ] 音量刻度来自反编译（如 /70.0）
- [ ] 音频格式离线试听确认（采样率/声道）
- [ ] 第一版只做一个音效闭环
- [ ] `audio=1` 开关默认关闭

## 阶段 7-8：发布
- [ ] 崩溃 dump 会用 `tools/psp2dmp_parse.py` 解析
- [ ] 稳定版有 tag + Release + VPK
- [ ] CHANGELOG 写明"改了什么/依据是什么"
- [ ] 正式版所有探针默认关闭
