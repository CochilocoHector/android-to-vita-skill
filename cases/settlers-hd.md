# 项目总览：The Settlers HD

- 移植仓库：<https://github.com/CochilocoHector/settlers-vita>
- 逆向知识库：<https://github.com/CochilocoHector/settlers-vita/tree/main/docs/reverse-engineering>
- 状态：图形完整（地形/精灵/动画/菜单/HUD），音频最小闭环（v0.61 待实机验证）

## 案例索引

| 案例 | 领域 | 状态 |
|---|---|---|
| [device_type 被重置](settlers-device-type.md) | 黑屏 | ✅ |
| [压缩纹理解码](settlers-compressed-textures.md) | 马赛克 | ✅ |
| [GUI 图集名匹配](settlers-gui-atlas-names.md) | 菜单空白 | ✅ |
| [JNI 方法映射缺失](settlers-jni-null-methodid.md) | 静音 | ✅ |
| [音频 voice 生命周期](settlers-audio-voice-lifecycle.md) | 音调异常 | ◐ 待验证 |

## 这个项目贡献了哪些通用方法

| 通用方法 | 条目 |
|---|---|
| 依赖体检、候选基址、阶段日志 | G-01 / G-02 / G-03 |
| 压缩纹理 CPU 解码 | G-04 |
| JNI 方法 ID 从 1 开始 | G-05 / G-06 / G-07 |
| SWF 图集名后缀匹配 | G-08 |
| dump 对比判定确定性 | G-09 |
| 系统工具改内存事故 | G-10 |
| 采样率可能逐文件不同 | G-11 |
| 播放器实例生命周期语义 | G-12 |

## 游戏专属内容

函数地址、全局变量、资源命名、音量刻度等**不写在本仓库**，
见项目的 `docs/reverse-engineering/` 各文件。

本仓库只保留"可迁移到其他项目的做法"。
