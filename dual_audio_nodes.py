import torch
import torchaudio


def _unify_audio(wf_a, sr_a, wf_b, sr_b):
    """统一两个音频的采样率和声道"""
    # 采样率对齐
    if sr_a != sr_b:
        if sr_a > sr_b:
            wf_b = torchaudio.functional.resample(wf_b, sr_b, sr_a)
            sr = sr_a
        else:
            wf_a = torchaudio.functional.resample(wf_a, sr_a, sr_b)
            sr = sr_b
    else:
        sr = sr_a
    
    # 声道对齐 (mono -> stereo)
    if wf_a.shape[1] == 1 and wf_b.shape[1] == 2:
        wf_a = wf_a.repeat(1, 2, 1)
    elif wf_b.shape[1] == 1 and wf_a.shape[1] == 2:
        wf_b = wf_b.repeat(1, 2, 1)
    elif wf_a.shape[1] == 1 and wf_b.shape[1] == 1:
        pass  # 都是mono就保持
    
    return wf_a, wf_b, sr


class DualAudioProcessor:
    """给 InfiniteTalk 多人对话用的，把两段音频处理成带静音填充的版本"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_left": ("AUDIO",),
                "audio_right": ("AUDIO",),
            },
        }
    
    RETURN_TYPES = ("AUDIO", "AUDIO", "AUDIO")
    RETURN_NAMES = ("left_padded", "right_padded", "merged")
    FUNCTION = "process"
    CATEGORY = "audio"

    def process(self, audio_left, audio_right):
        wf_a, wf_b, sr = _unify_audio(
            audio_left["waveform"], audio_left["sample_rate"],
            audio_right["waveform"], audio_right["sample_rate"]
        )
        
        ch = wf_a.shape[1]
        len_a, len_b = wf_a.shape[-1], wf_b.shape[-1]
        
        # 静音填充
        sil_a = torch.zeros((1, ch, len_a), dtype=wf_a.dtype, device=wf_a.device)
        sil_b = torch.zeros((1, ch, len_b), dtype=wf_b.dtype, device=wf_b.device)
        
        left_out = torch.cat([wf_a, sil_b], dim=-1)   # A说话 + 静音
        right_out = torch.cat([sil_a, wf_b], dim=-1)  # 静音 + B说话
        merged_out = torch.cat([wf_a, wf_b], dim=-1)  # A + B 拼接
        
        return (
            {"waveform": left_out, "sample_rate": sr},
            {"waveform": right_out, "sample_rate": sr},
            {"waveform": merged_out, "sample_rate": sr},
        )


class MultiAudioProcessor:
    """支持2-4人的版本，按顺序说话"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_1": ("AUDIO",),
                "audio_2": ("AUDIO",),
            },
            "optional": {
                "audio_3": ("AUDIO",),
                "audio_4": ("AUDIO",),
            },
        }
    
    RETURN_TYPES = ("AUDIO", "AUDIO", "AUDIO", "AUDIO", "AUDIO")
    RETURN_NAMES = ("padded_1", "padded_2", "padded_3", "padded_4", "merged")
    FUNCTION = "process"
    CATEGORY = "audio"

    def process(self, audio_1, audio_2, audio_3=None, audio_4=None):
        audios = [audio_1, audio_2]
        if audio_3 is not None:
            audios.append(audio_3)
        if audio_4 is not None:
            audios.append(audio_4)
        
        # 统一采样率
        sr = max(a["sample_rate"] for a in audios)
        wfs = []
        for a in audios:
            wf = a["waveform"]
            if a["sample_rate"] != sr:
                wf = torchaudio.functional.resample(wf, a["sample_rate"], sr)
            if wf.shape[1] == 1:
                wf = wf.repeat(1, 2, 1)
            wfs.append(wf)
        
        ch = wfs[0].shape[1]
        lens = [w.shape[-1] for w in wfs]
        total = sum(lens)
        
        # 每段音频前后补静音
        results = []
        offset = 0
        for i, wf in enumerate(wfs):
            before = torch.zeros((1, ch, offset), dtype=wf.dtype, device=wf.device)
            after = torch.zeros((1, ch, total - offset - lens[i]), dtype=wf.dtype, device=wf.device)
            results.append({"waveform": torch.cat([before, wf, after], dim=-1), "sample_rate": sr})
            offset += lens[i]
        
        merged = {"waveform": torch.cat(wfs, dim=-1), "sample_rate": sr}
        
        # 不够4个就补空音频
        while len(results) < 4:
            empty = torch.zeros((1, ch, total), dtype=wfs[0].dtype, device=wfs[0].device)
            results.append({"waveform": empty, "sample_rate": sr})
        
        return (*results, merged)


NODE_CLASS_MAPPINGS = {
    "DualAudioProcessor": DualAudioProcessor,
    "MultiAudioProcessor": MultiAudioProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DualAudioProcessor": "Dual Audio Processor (双人音频处理)",
    "MultiAudioProcessor": "Multi Audio Processor (多人音频处理)",
}
