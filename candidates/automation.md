# 可自动化操作

> 原则：先用一次性命令解决问题，**确认需要重复**后再固化成脚本。

## 已有脚本（tools/）

| 脚本 | 用途 | 来源 | 状态 |
|---|---|---|---|
| `psp2dmp_parse.py` | 解析崩溃 dump：应用名、内存分区、寄存器候选 | 多次崩溃分析 | verified |
| `dex_class_methods.py` | 提取 dex 类方法表（名称/签名/static/native） | 音频 JNI 定位 | verified |
| `btex_info.py` | 解析 BTEX/PVR 头（版本/宽高/位深） | 纹理格式确认 | verified |

## 待固化（重复出现过 ≥2 次）

| 操作 | 现状 | 计划 |
|---|---|---|
| 解析 BTEX v4 宽高并交换字段 | 手工 python 片段 | 增加 `--swap-dims` 选项 |
| 导出 0.snd 单段为 WAV | 一次性脚本 | `sound_bank.py --id N --rate 22050` |
| 提取 smali 中指定方法 | `awk` + baksmali | `smali_method.py <file> <method>` |
| 统计日志中某类事件频次 | grep/sort | `log_stats.py --pattern AUDIO_EVENT` |
| so 符号地址 → 运行时地址 | 手工 | `so_symbols.py <so> <base>`（待做） |

## 不自动化

- 具体游戏的补丁（地址、全局、字符串）——属于项目知识库，不进通用脚本
- 一次性的逆向判断（例如"这个函数在做什么"）——写进案例文档即可
