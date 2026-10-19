# 05 · 音频

## 1. 先确定音频在哪一层

- `DT_NEEDED` 没有 `libOpenSLES` / `libmedia` → **音频在 Java**（MediaPlayer / SoundPool）
- dex 里出现 `Landroid/media/MediaPlayer;` / `SoundPool;` 可确认
- 原生库里的 `native*` 函数往往是 **Java → native 的数据回调**，不是播放接口

## 2. 从 smali 读真实语义（必须）

```bash
java -jar baksmali.jar d classes.dex -o out
```

本案关键方法：

```
getSoundFileName(id)：
  id<10 → "000"+id+".ogg"；id<100 → "00"+id；id<283 → "0"+id
  283..291 → m_lose / m_*_fight / m_*_settle / m_title_settlers / m_win
  其它 → ""

playSoundBig(id, vol, loop)：
  n = vol / 70.0f        ← 音量刻度隐藏在这里
  setVolume(n,n); setLooping(loop==1); start()

loadSoundBig(id)：
  MediaPlayer.create(Uri.fromFile("/sdcard/.../Snd/" + getSoundFileName(id)))
```

**结论**：声音 id 直接对应 `Snd/0NNN.ogg`，不需要研究自定义 PCM 库。

## 3. 数据格式先离线确认

```bash
python3 tools/btex_info.py   # 不适用
# 用 ogg 头解析：mono 22050（音效）/ stereo 44100（音乐）
```

导出单段 WAV 试听："22050 听起来自然，是个鸟叫"——这一步不能省。

## 4. 最小输出闭环（Vita）

```
playSoundBig(id, vol, loop)
  → Snd/0NNN.ogg
  → stb_vorbis 解码（单声道化）
  → gain = clamp(vol/70, 0..1)
  → 线性重采样 22050→48000
  → 软件混音（8 路 voice）
  → sceAudioOut（48k 立体声，512 帧/次，独立线程）
```

要点：

- `sceAudioOutOpenPort(SCE_AUDIO_OUT_PORT_TYPE_MAIN, 512, 48000, STEREO)`
- 音频线程独立，混音时加锁，短临界区
- 解码缓存要设上限（条数 + 总字节 + 单条上限），音乐先跳过
- `audio=1` 开关默认关闭

## 5. 常见坑

| 现象 | 原因 |
|---|---|
| 完全静音 | JNI 方法未注册，调用塌缩到 id 0 |
| 有调用无声音 | 音量刻度理解错（如忘了 /70） |
| 声音变调 | 采样率用错（22050 当 44100） |
| 卡顿/爆音 | 解码在主线程，或缓冲过小 |
