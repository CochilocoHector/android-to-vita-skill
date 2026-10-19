# android-to-vita-skill

把 Android 原生游戏移植到 PS Vita 的**方法论与工具集**，沉淀自
[The Settlers HD Vita 移植项目](https://github.com/CochilocoHector/settlers-vita)。

不是通用教程，而是一份"遇到问题怎么查"的实战手册：
每个阶段都给出**判据、日志、失败案例与修法**，全部来自真机验证。

## 内容

```
SKILL.md                     核心流程（先读这个）
CHECKLIST.md                 移植检查表
docs/
  00-static-reverse-engineering.md  静态逆向总流程（核心）
  00a-dex-analysis.md               APK/DEX 分析
  00b-arm-disassembly.md            ARM ELF 与反汇编
  00c-call-graph-and-dataflow.md    调用链与数据流
  00d-original-behavior-reconstruction.md 原版行为还原
  01-feasibility-and-loader.md      可行性体检 + so-loader 骨架
  02-graphics-and-textures.md    图形与纹理解码（含马赛克根因）
  03-jni-and-java.md             JNI 方法表、NULL methodID 陷阱
  04-gui-swf.md                  gameswf / SWF 界面与图集名匹配
  05-audio.md                    音频：Java 层、格式、最小输出闭环
  06-debugging.md                日志、psp2dmp、崩溃定位
  07-case-study-settlers.md      完整案例：四条根因的发现过程
templates/
  touch.cfg                  运行时配置模板
  build-vpk.yml              GitHub Actions 构建工作流
cases/                       真实案例（含验证状态）
tools/
  apk_info.py                APK 结构与架构概览
  dex_class_methods.py       从 dex 提取 Java 方法表
  jni_diff.py                dex 方法 vs 兼容层注册表差异
  elf_info.py                ELF 依赖/导入/导出/重定位
  arm_xrefs.py               地址符号化与交叉引用
  btex_info.py               解析 BTEX/PVR 纹理头
  psp2dmp_parse.py           解析 Vita 崩溃 dump
  log_stats.py               日志事件统计
```

## 怎么用

1. 新项目：从 `SKILL.md` 的"阶段 0"开始，产出可行性报告
2. 遇到黑屏/马赛克/空白/静音：直接查 SKILL.md 末尾的**根因速查表**
3. 拿到 dump 或 dex：用 `tools/` 里的脚本先出事实，再下结论

## 三条铁律

1. **证据分级**：静态确认 / 日志确认 / 推测 / 未确认，禁止混用
2. **先读日志再改代码**，日志里没有的现象不要断言原因
3. **一次只改一个变量**，版本号写进文件名，随时能回退

## 适用前提

- 游戏逻辑在 ARMv7 `lib*.so`，符号基本完整
- 资源明文（PVR/OGG/自定义容器），不依赖 AAssetManager
- 有 HENkaku/Ensō 环境与 kubridge、taiHEN、libshacccg

## 许可

文档与脚本 MIT。案例中的游戏代码/资源版权归原厂商，本仓库不包含任何游戏资源。
