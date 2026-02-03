import sys
import shutil
from pathlib import Path
from collections import deque
import json

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QTabWidget
)
from PySide6.QtGui import QFont, QColor, QPalette

# =========================
# 文件操作函数
# =========================
SUPPORTED_LANGS = ['en_US', 'ja_JP', 'ko_KR', 'zh_CN']
JsonPath = "Json/imported_files.json"


def bfs_find_language_dirs(base_path: Path) -> dict[str, Path]:
    found = {}
    queue = deque([base_path])
    while queue:
        current = queue.popleft()
        for child in current.iterdir():
            if child.is_dir():
                if child.name in SUPPORTED_LANGS:
                    found[child.name] = child
                else:
                    queue.append(child)
    return found


def build_target_path(source_path: Path, target_lang_root: Path, language: str) -> Path:
    source_parts = list(source_path.parts)
    try:
        lang_index = source_parts.index(language)
        relative_parts = source_parts[lang_index + 1:]
    except ValueError:
        relative_parts = [source_path.name]

    target_path = target_lang_root
    for part in relative_parts:
        target_path /= part
    return target_path


def import_path(source_path: Path, target_path: Path) -> bool:
    try:
        if source_path.is_file():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
        else:
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)
        return True
    except Exception as e:
        print(f"导入失败: {e}")
        return False


def collect_imported_files_to_json(base_target: Path):
    all_entries = []
    folder_dict = {}
    index_counter = 0

    for lang_folder in base_target.iterdir():
        if not lang_folder.is_dir():
            continue
        language = lang_folder.name
        for file_path in lang_folder.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                rel_path = file_path.relative_to(base_target / language)
                ParentName = rel_path.parent.name
                folder_path = rel_path.parent.parent.as_posix()
                full_path_str = (base_target / language / rel_path).as_posix()
                if folder_path not in folder_dict:
                    entry = {
                        "index": index_counter,
                        'ParentName': ParentName,
                        "path": folder_path,
                        "dictionary": {language: full_path_str}
                    }
                    all_entries.append(entry)
                    folder_dict[folder_path] = index_counter
                    index_counter += 1
                else:
                    idx = folder_dict[folder_path]
                    all_entries[idx]["dictionary"][language] = full_path_str
            except Exception as e:
                print(f"跳过文件 {file_path}: {e}")
    return all_entries


def load_imported_files_from_json(JsonPath):
    json_path = Path.cwd().parent.parent / JsonPath
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except:
        return None


def save_imported_files_to_json(self,data):
    try:
        output_path = Path.cwd().parent.parent / JsonPath
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 清空文件内容
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("")

        # 写入新数据
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log(f"✅ Json路径 {output_path}")
        print(f"JSON 文件已保存: {output_path}")
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        return False


# =========================
# PySide6 界面
# =========================
class AudioImportUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音频文件导入工具")
        self.resize(800, 500)
        self.setup_ui()
        self.apply_dark_style()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 路径选择器
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择源路径...")
        browse_btn = QPushButton("选择路径")
        browse_btn.clicked.connect(self.select_path)
        path_layout.addWidget(QLabel("源路径:"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        main_layout.addLayout(path_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.load_json_btn = QPushButton("打开 JSON 文件")
        self.load_json_btn.clicked.connect(self.open_json)
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(self.start_import)
        btn_layout.addWidget(self.load_json_btn)
        btn_layout.addWidget(self.import_btn)
        main_layout.addLayout(btn_layout)

        # Tab 页面：日志 / JSON
        self.tab_widget = QTabWidget()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.json_output = QTextEdit()
        self.json_output.setReadOnly(True)

        self.tab_widget.addTab(self.log_output, "日志")
        self.tab_widget.addTab(self.json_output, "JSON")
        main_layout.addWidget(self.tab_widget)

    def apply_dark_style(self):
        # 设置窗口背景色
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.Base, QColor(60, 60, 60))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.Button, QColor(0, 0, 0))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setFont(QFont("Segoe UI", 10))

        # 应用黑底白字样式到所有控件
        self.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #222;
            }
            QLineEdit {
                background-color: black;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
            QTextEdit {
                background-color: black;
                color: white;
                border: 1px solid #555;
            }
            QTabWidget::pane {
                background-color: black;
                border: 1px solid #555;
            }
            QTabBar::tab {
                background-color: black;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background-color: #222;
            }
            QLabel {
                color: white;
            }
        """)

    def log(self, msg: str):
        self.log_output.append(msg)
        print(msg)

    def select_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择源路径")
        if folder:
            self.path_edit.setText(folder)

    def open_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 JSON 文件", str(Path.cwd().parent.parent / JsonPath), "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.json_output.setPlainText(content)
                self.tab_widget.setCurrentWidget(self.json_output)
                self.log(f"✅ 成功读取 JSON: {file_path}")
            except Exception as e:
                self.log(f"❌ 读取失败: {e}")

    def start_import(self):
        source_path_text = self.path_edit.text().strip()
        if not source_path_text:
            self.log("❌ 未选择源路径")
            return
        source_path = Path(source_path_text)
        if not source_path.exists():
            self.log(f"❌ 源路径不存在: {source_path}")
            return

        # 使用默认语言
        wwise_languages = SUPPORTED_LANGS
        self.log(f"✅ Wwise 语言: {wwise_languages}")

        # 本地语言文件夹
        base_local_path = Path.cwd().parent.parent.parent / "Originals" / "Voices"
        base_local_path.mkdir(parents=True, exist_ok=True)
        local_folders = {f.name: f for f in base_local_path.iterdir() if f.is_dir()}
        self.log(f"✅ 本地已有语言文件夹: {list(local_folders.keys())}")

        # 创建缺失语言文件夹
        for lang in wwise_languages:
            if lang not in local_folders:
                folder_path = base_local_path / lang
                folder_path.mkdir(exist_ok=True)
                local_folders[lang] = folder_path
                self.log(f"🟢 创建缺失本地语言文件夹: {folder_path}")

        # 搜索源路径下语言文件夹
        found_dirs = bfs_find_language_dirs(source_path)
        if not found_dirs:
            self.log("❌ 源路径下未找到任何语言文件夹")
            return
        self.log(f"✅ 发现源语言文件夹: {list(found_dirs.keys())}")

        # 遍历导入
        for lang, lang_source_path in found_dirs.items():
            if lang not in local_folders:
                target_lang_root = base_local_path / lang
                target_lang_root.mkdir(exist_ok=True)
                local_folders[lang] = target_lang_root
            target_path = build_target_path(lang_source_path, local_folders[lang], lang)
            self.log(f"导入: {lang_source_path} → {target_path}")
            success = import_path(lang_source_path, target_path)
            if success:
                self.log(f"✅ 导入完成: {target_path}")
            else:
                self.log(f"❌ 导入失败: {target_path}")

        # 写入 JSON（先清空原有内容）
        self.log("🔄 正在清空并写入 JSON...")
        datas = collect_imported_files_to_json(base_local_path)
        if save_imported_files_to_json(self,datas):
            self.log("✅ 导入信息已写入 JSON，可以切换到 JSON 页查看")
            # 清空 JSON 显示区域并显示新内容
            self.json_output.clear()
            self.json_output.setPlainText(json.dumps(datas, ensure_ascii=False, indent=2))
        else:
            self.log("❌ 保存 JSON 失败")

        self.log("🔄 信息如下：")
        self.log("ParentName：为Sound Voice")
        self.log("path：为Actor Mixer")
        self.log("dictionary：为Voice")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioImportUI()
    window.show()
    sys.exit(app.exec())