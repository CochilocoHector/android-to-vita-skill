# 02 · 图形与纹理

## 1. 马赛克的三种可能

按优先级排查：

1. **游戏选了错误的解码器**（全局 `device_type` 之类）
2. **vitaGL 的压缩纹理路径解错**
3. 数据本身/UV 问题

判别方法：同一份数据，**自己解码正常、交给 vitaGL 就花** → 第 2 种。

## 2. 案例：device_type 被重置

引擎按 `device_type` 分派：

```
0/2/4 → loadATCTexture
1/3   → loadPVRTexture
5     → loadDXTTexture
```

游戏初始化时把它改回 0，于是拿 DXT 数据走 ATC → 整屏黑。

修法：每帧把该全局写回正确值（本项目 `0x98000000+0x372208 = 5`）。

## 3. 案例：压缩纹理 CPU 解码

在 `glCompressedTexImage2D` 包装里拦截：

```c
if (fmt == 0x83f3 /*DXT5*/ || fmt == 0x83f2 || fmt == 0x83f0) {
    rgba = dxt_decode(data, w, h);
    glTexImage2D(target, level, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
    free(rgba);
    return;
}
```

PVRTC 同理，但可以直接复用游戏自带的解码器：

```
PVRTCDecompress(const void* src, int flag, int w, int h, unsigned char* out)
```

flag 由格式决定（4bpp→1，2bpp→0）。先用游戏自身调用点确认参数顺序。

## 4. 离线验证工具

`tools/btex_info.py` 解析容器头：

```bash
python3 tools/btex_info.py texture4.pvr
# BTEXpvr v4 1024x512 data@0x3C PVR! embedded
```

导出解码结果转 PNG 检查内容，**不要只靠肉眼进游戏判断**。

## 5. 性能与内存

- CPU 解码只在加载时发生，运行时无开销
- RGBA 占用量 = 宽×高×4：1024² = 4MB，2048² = 16MB
- 出现贴图变黑/丢失时，先查显存，再查解码

## 6. 日志节流

- 每帧统计：`draws / texC / genTex / glErr / lastTex`
- 调用栈轨迹表满后**必须停止记录**，否则日志爆炸会拖死游戏
