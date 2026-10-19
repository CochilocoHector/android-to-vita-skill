# 案例：JNI 方法映射缺失（完全静音）

## 现象

游戏可玩，但完全没有声音；日志里 `resetSound` 高频刷屏、参数杂乱。

## 初始假设

- 游戏没有调用音频接口
- 音效数据路径不对

## 静态证据

- DEX 中 `GLMediaPlayer` 共 41 个方法，**全部 static**（[DEX]）
- 原生库通过 `GetStaticMethodID` + `CallStaticVoidMethod` 调用（[ASM] 索引 141）
- 兼容层只注册了 21 个方法，缺 22 个音频接口（[SRC] 对照）
- 兼容层方法 ID 从 0 开始，`resetSound` 恰好是 0（[SRC]）
- `GetNativeSoundRaw` 是 `bx lr` 空桩（[ASM]）

## 排除的错误假设

| 假设 | 排除依据 |
|---|---|
| 游戏不调用音频 | 补齐后立刻看到 `playSoundBig` 调用 |
| GetNativeSoundRaw 可取 PCM | 空桩，无法返回数据 |
| 只需要补方法就能发声 | v0.59 方法齐全仍静音（还需后端） |

## 根因

查找失败返回 NULL(0)，而 0 被分配给 `resetSound`，
所有缺失方法的调用都塌缩成 `resetSound(id=0)`。

## 最小修复

1. 方法 ID 从 1 开始，0 保留为非法
2. 分发处对 `id <= 0` 记 `INVALID` 并丢弃
3. 按 DEX 补齐全部方法（名称+签名）

## 实机验证

✅ v0.59 日志出现真实调用（`playSoundBig(287,50.0,1)`），无 INVALID。

## 可迁移的方法

1. 方法表必须来自 DEX，不能猜
2. 兼容层 ID 从 1 开始
3. 查找与调用分别记录，按签名解析参数
