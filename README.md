## 六、运行方式  (在终端运行)

### 6.1 安装依赖

pip install flask flask-cors opencv-python Pillow ffmpeg-python requests pywebview

或使用 requirements.txt：

pip install -r requirements.txt

如果提示是否安装虚拟环境, 点击是

激活虚拟环境：
Windows CMD：.venv\Scripts\activate   (或者在.venv\Scripts文件里找到activate.bat, 双击运行)

Windows PowerShell：.venv\Scripts\Activate.ps1

Mac/Linux：source .venv/bin/activate

激活后，终端前面会出现 (.venv) 字样, 然后继续安装依赖

### 6.2 确保 FFmpeg 已安装

ffmpeg -version   # (添加到环境变量时终端才可以查看)

如未安装，请从 https://www.gyan.dev/ffmpeg/builds/ 下载安装，在页面里找到 ffmpeg-release-full.7z，点击下载, 解压后添加你的路径 ...\bin 到环境变量或者把 bin 文件夹里的 ffmpeg.exe 和 ffprobe.exe 放在项目文件夹里。

### 6.3 启动应用

python app_webview.py
