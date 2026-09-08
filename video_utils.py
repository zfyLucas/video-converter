import subprocess
import json
import os
import cv2
from PIL import Image
import tempfile
import re
import sys


def get_ffmpeg_path():
    """获取 FFmpeg 可执行文件路径"""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    ffmpeg_path = os.path.join(base_dir, 'ffmpeg.exe')
    if os.path.exists(ffmpeg_path):
        return ffmpeg_path
    
    import shutil
    system_ffmpeg = shutil.which('ffmpeg')
    if system_ffmpeg:
        return system_ffmpeg
    
    return 'ffmpeg'


def get_ffprobe_path():
    """获取 FFprobe 可执行文件路径"""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    ffprobe_path = os.path.join(base_dir, 'ffprobe.exe')
    if os.path.exists(ffprobe_path):
        return ffprobe_path
    
    import shutil
    system_ffprobe = shutil.which('ffprobe')
    if system_ffprobe:
        return system_ffprobe
    
    return 'ffprobe'


def get_encoder(output_format):
    """
    根据输出格式返回对应的视频编码器和音频编码器
    """
    codec_map = {
        'mp4': ('libx264', 'aac'),
        'm4v': ('libx264', 'aac'),
        'mkv': ('libx264', 'aac'),
        'mov': ('libx264', 'aac'),
        '3gp': ('libx264', 'aac'),
        '3g2': ('libx264', 'aac'),
        'flv': ('libx264', 'aac'),
        'avi': ('mpeg4', 'mp3'),
        'webm': ('libvpx-vp9', 'libopus'),
        'wmv': ('wmv2', 'wmav2'),
        'mpg': ('mpeg2video', 'mp2'),
        'mpeg': ('mpeg2video', 'mp2'),
    }
    return codec_map.get(output_format, ('libx264', 'aac'))


def get_video_info(file_path):
    """
    使用 ffprobe 获取视频信息
    """
    if not os.path.exists(file_path):
        return {"error": "文件不存在"}
    
    ffprobe_path = get_ffprobe_path()
    
    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if not result.stdout:
            return {"error": "ffprobe 未返回数据，请检查 ffmpeg 是否安装"}
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"解析失败: {e}"}
    except FileNotFoundError:
        return {"error": "ffprobe 未找到，请安装 ffmpeg 并添加到环境变量"}
    
    info = {}
    
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")
            info["codec"] = stream.get("codec_name")
            fps_str = stream.get("r_frame_rate", "0/1")
            if "/" in fps_str:
                try:
                    info["fps"] = round(eval(fps_str), 2)
                except:
                    info["fps"] = fps_str
            else:
                info["fps"] = fps_str
            break
    
    format_info = data.get("format", {})
    info["duration"] = float(format_info.get("duration", 0))
    info["size"] = int(format_info.get("size", 0))
    info["format"] = format_info.get("format_name", "")
    
    return info


def extract_thumbnail(file_path, time_sec=1.0):
    """提取视频缩略图"""
    cap = cv2.VideoCapture(file_path)
    
    if not cap.isOpened():
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_index = int(fps * time_sec)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def convert_video(input_path, output_path, progress_callback=None):
    """
    使用 ffmpeg 转换视频 - 根据格式自动选择编码器
    """
    info = get_video_info(input_path)
    total_duration = info.get("duration", 0)
    
    if "error" in info:
        return False
    
    output_format = os.path.splitext(output_path)[1].lower().replace('.', '')
    video_codec, audio_codec = get_encoder(output_format)
    ffmpeg_path = get_ffmpeg_path()
    
    # 构建基础命令
    cmd = [
        ffmpeg_path,
        "-i", input_path,
        "-c:v", video_codec,
        "-c:a", audio_codec,
        "-y",
        output_path
    ]
    
    # 针对不同格式添加额外参数
    if output_format in ['mp4', 'mkv', 'mov', 'm4v', '3gp', '3g2', 'flv']:
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-c:v", video_codec,
            "-preset", "medium",
            "-crf", "23",
            "-c:a", audio_codec,
            "-b:a", "128k",
            "-y",
            output_path
        ]
    elif output_format in ['mpg', 'mpeg']:
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-c:v", video_codec,
            "-b:v", "2M",
            "-c:a", audio_codec,
            "-b:a", "192k",
            "-y",
            output_path
        ]
    elif output_format in ['webm', 'wmv', 'avi']:
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-c:v", video_codec,
            "-b:v", "2M",
            "-c:a", audio_codec,
            "-b:a", "128k",
            "-y",
            output_path
        ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1
    )
    
    time_pattern = re.compile(rb"time=(\d+):(\d+):(\d+)\.(\d+)")
    
    for line in iter(process.stderr.readline, b""):
        if not line:
            break
        match = time_pattern.search(line)
        if match and total_duration > 0:
            h = int(match.group(1))
            m = int(match.group(2))
            s = int(match.group(3))
            current_time = h * 3600 + m * 60 + s
            progress = min(int((current_time / total_duration) * 100), 99)
            if progress_callback:
                progress_callback(progress)
    
    process.wait()
    
    if process.returncode == 0 and progress_callback:
        progress_callback(100)
    
    return process.returncode == 0


def format_duration(seconds):
    """格式化时长显示"""
    if not seconds or seconds <= 0:
        return "0s"
    total_seconds = int(round(seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h}h{m:02d}m{s:02d}s"
    elif m > 0:
        return f"{m}m{s:02d}s"
    else:
        return f"{s}s"


def format_size(size_bytes):
    """格式化文件大小"""
    if not size_bytes or size_bytes <= 0:
        return "0B"
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"