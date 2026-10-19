# 04 · GUI（gameswf / SWF）

## 1. 先判断 UI 是谁画的

找管理器入口，例如：

```asm
CGUIManager::draw():
  if (this+0x24 && this+0x28)
      RenderFX::Render();   // gameswf
```

如果 draw 只是转发到 RenderFX，那 UI 就是 SWF 渲染，
游戏自己的 2D 绘制只负责血条/数字等。

## 2. SWF 位图通常是占位

解析 `DefineBitsLossless2`（tag 36）：

```
payload 只有 7 字节 = characterId + 格式 + 宽高，没有像素
```

说明真实图集由游戏按名字从外部加载（`texture0.pvr` 之类），
SWF 只负责布局与矢量元素。

## 3. 高频根因：图集名不匹配

游戏在 960 宽度下查 `texture0_960.pvr`，而数据包只有 `texture0.pvr`；
比较用的是 `strstr`，后缀导致永不命中 → 所有图集被判定"不需要加载" → 菜单空白。

修法：**只在名字比较时去掉 `_960` / `_854` 后缀**，注册名与资源路径保持不变。

```c
strip_variant("texture0_960.pvr") -> "texture0.pvr"
strstr("./texture0.pvr", "texture0.pvr") -> 命中
```

不要复制纹理文件、不要改注册逻辑——先修比较，最小改动。

## 4. 观测两道门控

典型结构：

```asm
GATE1: GetBitmapInfoByTexId(id)      ; 找不到 bitmap_info 就跳过
GATE2: IsNeedToLoadTexture(arg,name) ; 名字不在当前页就跳过
       → getTexture(name)            ; 真正加载
```

观测方法：只在两个门控入口挂日志，靠**调用顺序**推断结果：

```
GATE1 → GATE2 → GETTEX   = 两道都通过
GATE1 → 下一个 GATE1     = 门控一失败（门控二没被调用）
GATE1 → GATE2 → 下一个 GATE1 = 门控二失败
```

**不要为了日志额外调用门控函数。**
