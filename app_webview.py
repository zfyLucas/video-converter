import webview
import time
import sys
import os
import subprocess
import atexit

flask_process = None


def start_flask():
    global flask_process
    
    startupinfo = None
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    
    flask_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )
    time.sleep(2)


def cleanup():
    global flask_process
    if flask_process:
        try:
            flask_process.terminate()
            flask_process.wait(timeout=3)
        except:
            flask_process.kill()
        flask_process = None


atexit.register(cleanup)


if __name__ == '__main__':
    print("🚀 正在启动服务...")
    start_flask()
    print("✅ 服务已启动，打开窗口...")
    
    window = webview.create_window(
        title="AI 视频格式转换器",
        url="http://127.0.0.1:5000",
        width=1100,
        height=780,
        resizable=True,
        confirm_close=False
    )
    
    webview.start()
    
    cleanup()
    sys.exit(0)