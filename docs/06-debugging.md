# 06 · 调试与崩溃分析

## 1. 先看日志停在哪

日志最后一行 = 崩溃发生在**下一阶段**。
例：停在 "跳过 Storm JNI_OnLoad" → 下一步是 `gl_init()`。

## 2. psp2dmp 解析

```bash
python3 tools/psp2dmp_parse.py ux0:data/psp2core-*.psp2dmp
```

输出：

```
app: SETL00001  The Settlers HD v0.56
game partition: total 256.0 MB  used 240.7 MB  free 13.7 MB
thread regs (candidates in modules): ...
```

判读：

- **两次 dump 寄存器完全一致** → 确定性路径，先查逻辑
- 寄存器每次不同 → 随机（内存/时序）
- 分区 used 接近 total → 内存压力，但不等于根因

## 3. 案例：改系统设置后打不开

- 对比 `eboot.bin` 哈希、`param.sfo` 内容 → 与应用文件无关
- 工具把设置写进了系统登记项（`ur0` 的 app.db 类区域，USB 看不到）
- **重启后仍坏 → 重装应用即可恢复**（重新登记）

## 4. 日志治理

- 每个探针独立开关（配置项）
- 高频路径按 `(id,参数)` 去重
- 每个探针有上限，满了就停
- 每帧统计一行即可，不要每帧多行

## 5. 版本策略

- 文件名带版本号
- 每版只改一个变量
- 稳定版打 tag + Release，附 VPK 与说明
- 保留上一版 VPK，随时回退
