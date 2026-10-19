# Skill 候选资料

> 这里收集**通用移植方法**，来源是真实项目里被验证过的做法。
> 规则见 [SKILL.md](../SKILL.md) 的"通用方法与游戏专属的边界"。

## 状态标签

| 标签 | 含义 |
|---|---|
| `verified` | 在至少一个真实项目中解决过问题，有日志/数据证据 |
| `probable` | 逻辑成立但只在单一场景验证 |
| `idea` | 待验证的猜想，**不得写进正式 SKILL.md** |

## 收录规则

- 只写"方法"，不写某个游戏的地址、文件名、常量
- 每条必须带 `验证于` 与 `证据`
- 游戏专属内容放对应项目的知识库（如 settlers-vita 的 `docs/kb/`）

## 文件

- [general-methods.md](general-methods.md) — 已沉淀的通用方法
- [automation.md](automation.md) — 可自动化操作与脚本演进

## 晋升流程

```
idea → probable（一次验证）→ verified（跨场景/跨项目复现）
     → 写入 SKILL.md 对应阶段 → 标记来源案例
```
