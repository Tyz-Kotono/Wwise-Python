import os
import subprocess
import sys


def open_current_folder():
    # 获取当前 Python 文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 根据操作系统打开文件夹
    if sys.platform == "win32":
        # Windows
        os.startfile(current_dir)
    elif sys.platform == "darwin":
        # macOS
        subprocess.run(["open", current_dir])
    else:
        # Linux
        subprocess.run(["xdg-open", current_dir])

    print(f"已打开文件夹: {current_dir}")


if __name__ == "__main__":
    open_current_folder()