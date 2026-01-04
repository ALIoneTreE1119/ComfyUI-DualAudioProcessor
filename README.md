# ComfyUI-DualAudioProcessor

给 InfiniteTalk 多人数字人场景用的音频处理节点。

## 干嘛用的

做多人数字人视频的时候，需要让每个人轮流说话。这个节点把多段音频处理成等长的版本，每段音频在自己说话的时间有声音，其他时间是静音。

比如 A 说 3 秒，B 说 2 秒：
- A 的输出：3秒有声 + 2秒静音
- B 的输出：3秒静音 + 2秒有声  
- 合并输出：A说完B接着说，共5秒

## 效果展示

https://github.com/user-attachments/assets/示例视频.mp4

## 节点

### DualAudioProcessor
两个人对话用的。

![DualAudioProcessor](示例图1.png)

输入：
- `audio_left` - 先说话的人
- `audio_right` - 后说话的人

输出：
- `left_padded` - 左边音频（有声+静音）
- `right_padded` - 右边音频（静音+有声）
- `merged` - 拼接后的完整音频

### MultiAudioProcessor
2-4个人用的，按顺序说话。

![MultiAudioProcessor](示例图2.png)

输入：
- `audio_1`, `audio_2` - 必填
- `audio_3`, `audio_4` - 可选

输出：
- `padded_1` ~ `padded_4` - 每个人的填充音频
- `merged` - 拼接后的完整音频

## 工作流

`workflow/` 文件夹里有现成的工作流可以直接用：
- `InfiniteTalk双人数字人对口型.json` - 双人对话的完整工作流

## 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/你的用户名/ComfyUI-DualAudioProcessor.git
```

重启 ComfyUI 就行。

## 依赖

ComfyUI 自带的 torch 和 torchaudio，不用额外装。
