# 07 · 案例：The Settlers HD（四条根因）

项目：<https://github.com/CochilocoHector/settlers-vita>
版本：v0.22 → v0.60（地形/精灵/GUI 完整，音频最小闭环）

## 根因 1：device_type 被重置 → 整屏黑

- 引擎按全局 `device_type` 选解码器（ATC/PVR/DXT）
- 游戏初始化把它改回 0 → DXT 数据走 ATC → 黑屏
- 修法：每帧写回 5（`0x98000000+0x372208`）

## 根因 2：压缩纹理路径 → 精灵马赛克

- 同一份 DXT5：自己解码正常，交给 vitaGL 就是马赛克
- 修法：拦截 `glCompressedTexImage2D`，CPU 解码成 RGBA 再上传
- 验证：地形用同样方式解码后完全正常

## 根因 3：GUI 图集名后缀 → 菜单空白

- 960 宽度查 `texture0_960.pvr`，数据包只有 `texture0.pvr`
- `strstr` 永不命中 → 所有图集被跳过
- 修法：比较时去掉 `_960/_854` 后缀（注册名与路径不动）
- 修复后菜单、HUD、暂停界面全部恢复

## 根因 4：JNI 方法缺失 → 音频"没有任何调用"

- 缺失方法返回 NULL methodID，被分发成 id 0（`resetSound`）
- 日志表现为 `resetSound` 高频刷屏、参数混乱
- 修法：ID 从 1 开始、0 视为非法；按 dex 补齐 43 个方法
- 补齐后一次运行看到真实调用：`playSoundBig(287, 50.0, 1)`

## 音频结论

- 所有播放走 `playSoundBig(IFI)V`（"Big" 命名误导）
- 音量刻度 `vol/70.0`（smali 确认）
- 声音 id → `Snd/0NNN.ogg`（`getSoundFileName` 确认）
- `0.snd/0.sil` 是原生 PCM 库，不参与播放链

## 时间线（经验值）

| 阶段 | 主要工作 |
|---|---|
| 可行性 + 骨架 | 1 天 |
| 黑屏（device_type） | 数天，靠每帧打印全局值定位 |
| 地形 DXT 自解码 | 1 天 |
| 精灵马赛克（CPU 解码） | 1 天 |
| GUI 空白（后缀匹配） | 2 天，靠门控顺序推断 |
| 音频调用链 | 1 天，靠 dex/smali 精确定义 |
