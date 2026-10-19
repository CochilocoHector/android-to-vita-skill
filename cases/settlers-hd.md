# 案例：The Settlers HD

- 项目仓库：<https://github.com/CochilocoHector/settlers-vita>
- 逆向知识库：<https://github.com/CochilocoHector/settlers-vita/tree/main/docs/kb>
- 状态：图形完整（地形/精灵/动画/菜单/HUD），音频最小闭环（v0.60）

## 这个案例贡献了哪些通用方法

| 通用方法 | 条目 |
|---|---|
| 依赖体检、候选基址、阶段日志 | G-01 / G-02 / G-03 |
| 压缩纹理 CPU 解码 | G-04 |
| JNI 方法 ID 从 1 开始 | G-05 / G-06 / G-07 |
| SWF 图集名后缀匹配 | G-08 |
| dump 对比判定确定性 | G-09 |
| 系统工具改内存事故 | G-10 |

## 游戏专属内容在哪里

函数地址、全局变量、资源命名、音量刻度等**不写在本仓库**，
统一放在项目的 `docs/kb/`：

- `addresses.md`：函数/全局地址
- `resources.md`：资源格式与命名
- `jni-audio.md`：JNI 方法表与音频语义
- `crash-and-memory.md`：崩溃与内存事实

本仓库只保留"可迁移到其他项目的做法"，避免把某个游戏的地址当成标准。
