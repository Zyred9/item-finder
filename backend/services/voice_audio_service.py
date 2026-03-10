"""
语音文件预处理服务。
负责识别上传语音的真实格式，并在必要时转成标准 wav。
"""
from __future__ import annotations

import io
from pathlib import Path

from pydub import AudioSegment


def detect_voice_extension(filename: str | None, audio_data: bytes) -> str:
    ext = ".mp3"
    lower_name = (filename or "").lower()
    for item in (".silk", ".m4a", ".aac", ".wav", ".mp3", ".ogg", ".webm", ".opus"):
        if lower_name.endswith(item) or item in lower_name:
            ext = item
            break

    if len(audio_data) >= 12:
        head = audio_data[:12]
        if audio_data.startswith(b"\x02#!SILK_V3") or audio_data.startswith(b"#!SILK_V3"):
            return ".silk"
        if head[4:8] == b"ftyp":
            return ".m4a"
        if head[:2] in (b"\xff\xf1", b"\xff\xf9", b"\xff\xfa"):
            return ".aac"
        if head[:4] == b"OggS":
            return ".ogg"
        if head[:4] == b"\x1a\x45\xdf\xa3":
            return ".webm"
        if head[:4] == b"Opus" or (len(audio_data) >= 36 and audio_data[28:32] == b"Opus"):
            return ".opus"
        if head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xfa"):
            return ".mp3"

    return ext


def prepare_voice_file(
    audio_data: bytes,
    ext: str,
    voice_temp_dir: Path,
    file_id: str,
) -> tuple[Path, str, str]:
    """
    返回: (落盘文件路径, 最终文件名, 处理说明)
    """
    if ext == ".silk":
        return _decode_silk_to_wav(audio_data, voice_temp_dir, file_id)
    return _decode_common_audio_to_wav(audio_data, ext, voice_temp_dir, file_id)


def _decode_silk_to_wav(audio_data: bytes, voice_temp_dir: Path, file_id: str) -> tuple[Path, str, str]:
    import pysilk

    silk_path = voice_temp_dir / f"{file_id}.silk"
    pcm_path = voice_temp_dir / f"{file_id}.pcm"
    wav_path = voice_temp_dir / f"{file_id}.wav"

    silk_path.write_bytes(audio_data)
    with open(silk_path, "rb") as silk_file, open(pcm_path, "wb") as pcm_file:
        pysilk.decode(silk_file, pcm_file, 24000)

    pcm_data = pcm_path.read_bytes()
    # pilk.decode 默认输出 24000Hz、16bit、单声道 PCM
    audio = AudioSegment(
        data=pcm_data,
        sample_width=2,
        frame_rate=24000,
        channels=1,
    )
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(wav_path, format="wav")
    return wav_path, wav_path.name, "silk->wav"


def _decode_common_audio_to_wav(
    audio_data: bytes,
    ext: str,
    voice_temp_dir: Path,
    file_id: str,
) -> tuple[Path, str, str]:
    buf = io.BytesIO(audio_data)
    seg = None
    used_label = ""
    for fmt, label in [
        ("aac", "aac"),
        ("mp4", "m4a"),
        ("mp3", "mp3"),
        ("ogg", "ogg"),
        ("opus", "opus"),
        ("webm", "webm"),
        ("wav", "wav"),
    ]:
        try:
            buf.seek(0)
            seg = AudioSegment.from_file(buf, format=fmt)
            used_label = label
            break
        except Exception:
            continue

    if seg is None:
        path = voice_temp_dir / f"{file_id}{ext}"
        path.write_bytes(audio_data)
        return path, path.name, f"raw:{ext}"

    wav_path = voice_temp_dir / f"{file_id}.wav"
    seg.set_frame_rate(16000).set_channels(1).export(wav_path, format="wav")
    return wav_path, wav_path.name, f"{used_label}->wav"
