from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import shutil
import tempfile
import base64
import sys
from io import BytesIO
from video_utils import (
    get_video_info,
    extract_thumbnail,
    convert_video,
    format_duration,
    format_size
)

app = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 支持的所有视频格式
SUPPORTED_FORMATS = [
    "mp4", "avi", "mkv", "mov", "flv", "wmv", 
    "webm", "m4v", "mpg", "mpeg", "3gp", "3g2"
]

conversion_records = {}


def get_unique_filename(base_name, output_format):
    ext = output_format
    counter = 1
    while True:
        filename = f"{base_name}_converted_{counter}.{ext}"
        if filename in conversion_records:
            counter += 1
            continue
        return filename


def thumbnail_to_base64(thumbnail):
    if thumbnail is None:
        return None
    buffered = BytesIO()
    thumbnail.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/formats')
def get_formats():
    return jsonify(SUPPORTED_FORMATS)


@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"upload_{file.filename}")
    file.save(temp_path)
    
    info = get_video_info(temp_path)
    if "error" in info:
        return jsonify({'error': info['error']}), 400
    
    thumbnail = extract_thumbnail(temp_path, time_sec=1.0)
    thumb_base64 = thumbnail_to_base64(thumbnail)
    
    return jsonify({
        'filename': file.filename,
        'temp_path': temp_path,
        'info': info,
        'thumbnail': thumb_base64
    })


@app.route('/api/convert', methods=['POST'])
def convert():
    data = request.json
    temp_path = data.get('temp_path')
    output_format = data.get('output_format', 'mp4')
    base_name = data.get('base_name', 'video')
    
    if not temp_path or not os.path.exists(temp_path):
        return jsonify({'error': '源文件不存在'}), 400
    
    if output_format not in SUPPORTED_FORMATS:
        return jsonify({'error': f'不支持的格式: {output_format}'}), 400
    
    filename = get_unique_filename(base_name, output_format)
    
    temp_dir = tempfile.gettempdir()
    temp_output_path = os.path.join(temp_dir, f"converted_{filename}")
    
    success = convert_video(temp_path, temp_output_path)
    
    if success:
        info = get_video_info(temp_output_path)
        thumbnail = extract_thumbnail(temp_output_path, time_sec=1.0)
        thumb_base64 = thumbnail_to_base64(thumbnail)
        
        conversion_records[filename] = {
            'info': info,
            'temp_path': temp_output_path,
            'thumbnail': thumb_base64,
            'format': output_format
        }
        
        return jsonify({
            'success': True,
            'filename': filename,
            'info': info,
            'thumbnail': thumb_base64
        })
    else:
        return jsonify({'error': '转换失败'}), 500


@app.route('/api/list')
def list_videos():
    """返回原始数据（不格式化）"""
    records = []
    for filename, record in conversion_records.items():
        info = record.get('info', {})
        output_path = os.path.join(OUTPUT_DIR, filename)
        is_downloaded = os.path.exists(output_path)
        records.append({
            'filename': filename,
            'duration': info.get('duration', 0),
            'size': info.get('size', 0),
            'width': info.get('width', '?'),
            'height': info.get('height', '?'),
            'codec': info.get('codec', '未知'),
            'fps': info.get('fps', '未知'),
            'thumbnail': record.get('thumbnail'),
            'is_downloaded': is_downloaded,
            'format': record.get('format', '')
        })
    return jsonify(records)


@app.route('/api/video_info/<filename>')
def get_video_info_by_filename(filename):
    """获取转换记录中视频的详细信息 - 返回原始数据"""
    if filename not in conversion_records:
        return jsonify({'error': '视频不存在'}), 404
    
    record = conversion_records[filename]
    info = record.get('info', {})
    
    return jsonify({
        'filename': filename,
        'duration': info.get('duration', 0),
        'width': info.get('width', '?'),
        'height': info.get('height', '?'),
        'codec': info.get('codec', '未知'),
        'fps': info.get('fps', '未知'),
        'size': info.get('size', 0),
        'format': info.get('format', '未知'),
        'thumbnail': record.get('thumbnail'),
        'is_downloaded': os.path.exists(os.path.join(OUTPUT_DIR, filename))
    })


@app.route('/api/download/<filename>')
def download(filename):
    if filename not in conversion_records:
        return jsonify({'error': '文件不存在'}), 404
    
    record = conversion_records[filename]
    temp_path = record.get('temp_path')
    
    if not temp_path or not os.path.exists(temp_path):
        return jsonify({'error': '源文件不存在'}), 404
    
    output_path = os.path.join(OUTPUT_DIR, filename)
    counter = 1
    base_name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    while os.path.exists(output_path):
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}_{counter}{ext}")
        counter += 1
    
    shutil.copy2(temp_path, output_path)
    
    return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))


@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete(filename):
    if filename not in conversion_records:
        return jsonify({'error': '文件不存在'}), 404
    
    record = conversion_records[filename]
    temp_path = record.get('temp_path')
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
    
    del conversion_records[filename]
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)