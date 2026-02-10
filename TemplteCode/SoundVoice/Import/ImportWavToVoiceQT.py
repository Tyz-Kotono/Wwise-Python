#!/usr/bin/env python3
from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException
from pathlib import Path, PureWindowsPath

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QFileDialog, QLabel
)
from PySide6.QtCore import Qt

WAAPI_URL = "ws://127.0.0.1:8080/waapi"

# =========================
# 全局数据
# =========================
root_path = None
originals_path = None
json_path = None
voice_path = None

languages = []
languages_path = {}
VoiceSource_Paths = {}
wwiseoriginalsVoiceWav_paths = []

# =========================
# 工具函数
# =========================
def normalize_path(path_str: str) -> str:
    """统一路径为正斜杠格式"""
    if not path_str:
        return ""
    try:
        if "\\" in path_str or (len(path_str) > 1 and path_str[1] == ":"):
            return str(PureWindowsPath(path_str).as_posix())
        return path_str
    except Exception:
        return path_str.replace("\\", "/")


# =========================
# 初始化函数
# =========================
def IninData():
    """初始化 Wwise 工程路径与语言信息"""
    global root_path, originals_path, json_path, voice_path
    global languages, languages_path

    try:
        with WaapiClient(WAAPI_URL) as client:
            result = client.call("ak.wwise.core.getProjectInfo")

        root_str = normalize_path(result['directories']['root'])
        originals_str = normalize_path(result['directories']['originals'])
        
        root_path = Path(root_str)
        originals_path = Path(originals_str)
        json_path = root_path / 'Json' / 'imported_files.json'
        voice_path = originals_path / 'Voices'
        
        print(f"Root: {root_path}")
        print(f"Originals: {originals_path}")
        print(f"JSON path: {json_path}")
        print(f"Voice path: {voice_path}")
        
        # 收集语言
        languages = []
        for language in result['languages']:
            key = language['name']
            languages_path[key] = voice_path/key
            languages.append(key)
            print(f"{key} : {voice_path/key}")
        
        return True

    except CannotConnectToWaapiException:
        print("WAAPI 连接失败")
        return False


# =========================
# Voice Source 收集
# =========================
def CollectVoiceSourcePath(input_path: str):
    """
    在输入路径中查找语言目录并记录路径
    """
    global VoiceSource_Paths

    VoiceSource_Paths.clear()
    base_path = Path(normalize_path(input_path))

    if not base_path.exists():
        raise FileNotFoundError(f"路径不存在: {base_path}")

    for lang in languages:
        lang_dir = base_path / lang
        if lang_dir.exists() and lang_dir.is_dir():
            VoiceSource_Paths[lang] = lang_dir

    return VoiceSource_Paths

import shutil


def RemovePath(Ori: str, target: str) -> Path:
    a = Path(target).resolve()
    b = Path(Ori).resolve()

    return b.relative_to(a)

def CopyVoiceSourceToWwiseVoices():
    wwiseoriginalsVoiceWav_paths.clear()
    for lang, src_root in VoiceSource_Paths.items():
        if lang not in languages_path:
            continue

        dst_root = languages_path[lang]
        dst_root.mkdir(parents=True, exist_ok=True)

        print(f"\n[{lang}]")
        print(f"  Source: {src_root}")
        print(f"  Target: {dst_root}")

        for file in src_root.rglob("*"):
            if not file.is_file():
                continue

            relative_path = file.relative_to(src_root)
            target_file = dst_root / relative_path

            target_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(file, target_file)
            # print(f"Source: {file}")
            # print(f"Ori {target_file}")
            
            wwiseoriginalsVoiceWav_paths.append(target_file)
            # wavPath = RemovePath(target_file,voice_path)
            print(target_file)


import json

def WriteWavToJson(wav_paths, json_path: Path):
    """
    将 wav 路径列表写入 json 文件（覆盖）
    """
    json_path.parent.mkdir(parents=True, exist_ok=True)

    data = [str(p.as_posix()) for p in wav_paths]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"已写入 {len(data)} 条 wav 路径到 {json_path}")


#  UI

# =========================
# Log 重定向
# =========================
class LogRedirect:
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit

    def write(self, msg):
        if msg.strip():
            self.text_edit.append(msg.rstrip())

    def flush(self):
        pass


# =========================
# 主窗口
# =========================
class VoiceImportWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Wwise Voice Import Tool")
        self.resize(1200, 600)

        layout = QVBoxLayout(self)

        # ---- Path Selector ----
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择 Voice Source 根路径")
        browse_btn = QPushButton("Browse")

        browse_btn.clicked.connect(self.browse)

        path_layout.addWidget(QLabel("Source Path:"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)

        # ---- Import Button ----
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.run_import)

        # ---- Log Window ----
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        layout.addLayout(path_layout)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.log_view)

        # redirect print → log
        sys.stdout = LogRedirect(self.log_view)

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择 Voice Source 根路径")
        if path:
            self.path_edit.setText(path)

    def run_import(self):
        source_root = self.path_edit.text().strip()
        if not source_root:
            print("❌ 未选择路径")
            return

        print("========== 开始导入 ==========")

        if not IninData():
            return

        result = CollectVoiceSourcePath(source_root)

        print("\n收集到的 VoiceSource_Paths:")
        for lang, path in result.items():
            print(f"{lang} -> {path}")

        print("\n开始复制 Voice Source...")
        CopyVoiceSourceToWwiseVoices()

        print("\n写入 JSON...")
        WriteWavToJson(wwiseoriginalsVoiceWav_paths, json_path)

        print("========== 导入完成 ==========")

# =========================
# 示例用法
# =========================
if __name__ == "__main__":
    # if IninData():
    #     source_root = input("请输入 Voice Source 根路径: ").strip()
    #     result = CollectVoiceSourcePath(source_root)

    #     print("\n收集到的 VoiceSource_Paths:")
    #     for lang, path in result.items():
    #         print(f"{lang} -> {path}")

    #     print("\n开始复制 Voice Source...")
    #     CopyVoiceSourceToWwiseVoices()

    #     WriteWavToJson(wwiseoriginalsVoiceWav_paths, json_path)
    app = QApplication(sys.argv)
    win = VoiceImportWindow()
    win.show()
    sys.exit(app.exec())