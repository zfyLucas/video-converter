## 六、运行方式

### 6.1 安装依赖

pip install flask flask-cors opencv-python Pillow ffmpeg-python requests pywebview

或使用 requirements.txt：

pip install -r requirements.txt

### 6.2 确保 FFmpeg 已安装

ffmpeg -version

如未安装，请从 https://ffmpeg.org/download.html 下载安装，然后添加你的路径 ...\bin 到环境变量或者把 bin 文件夹里的 ffmpeg.exe 和 ffprobe.exe 放在项目文件夹里。

### 6.3 启动应用

python app_webview.py
