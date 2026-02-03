import sys
import os
import re
from pprint import pprint

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QPushButton, QSplitter, QFileDialog, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


# =============================
# Rename Core
# =============================
class RenameEngine:
    def __init__(self):
        self.prefix = ""
        self.suffix = ""
        self.regex_a = ("", "")
        self.regex_b = ("", "")

    def rename(self, name: str) -> str:
        new = name
        if self.regex_a[0]:
            new = re.sub(self.regex_a[0], self.regex_a[1], new)
        if self.regex_b[0]:
            new = re.sub(self.regex_b[0], self.regex_b[1], new)
        if self.prefix and not new.startswith(self.prefix):
            new = self.prefix + new
        if self.suffix and not new.endswith(self.suffix):
            new = new + self.suffix
        return new


# =============================
# File System Helpers
# =============================
def build_file_tree(path):
    name = os.path.basename(path)
    if os.path.isfile(path):
        return {"name": name, "path": path, "children": []}
    else:
        children = [build_file_tree(os.path.join(path, c)) for c in os.listdir(path)]
        return {"name": name, "path": path, "children": children}


def collect_all_nodes(obj):
    all_nodes = []
    queue = [obj]
    while queue:
        current = queue.pop(0)
        all_nodes.append(current)
        queue.extend(current.get("children", []))
    return all_nodes


def change_name(obj, new_name):
    dir_path = os.path.dirname(obj["path"])
    new_path = os.path.join(dir_path, new_name)
    try:
        os.rename(obj["path"], new_path)
        obj["name"] = new_name
        obj["path"] = new_path
        return True
    except Exception as e:
        print(f"重命名失败: {obj['path']} -> {new_path}, {e}")
        return False


# =============================
# Main UI
# =============================
class RenameToolUI(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = RenameEngine()
        self.root_obj = None
        self.selected_nodes = []
        self.setWindowTitle("文件重命名工具")
        self.resize(1200, 700)
        self.build_ui()
        self.apply_style()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # 主分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        root.addWidget(splitter, 1)

        # 左侧树
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)

        tree_label = QLabel("文件夹结构")
        left_layout.addWidget(tree_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称"])
        self.tree.itemSelectionChanged.connect(self.on_tree_selection)
        left_layout.addWidget(self.tree)

        splitter.addWidget(left_frame)

        # 右侧
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # 文件夹选择部分
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)

        self.folder_btn = QPushButton("选择文件夹")
        self.folder_btn.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.folder_btn)
        folder_layout.addStretch()

        right_layout.addLayout(folder_layout)

        # 改名参数部分
        # 前缀和后缀
        prefix_suffix_layout = QHBoxLayout()
        prefix_suffix_layout.setSpacing(8)

        self.prefix = QLineEdit()
        self.prefix.setPlaceholderText("前缀")

        self.suffix = QLineEdit()
        self.suffix.setPlaceholderText("后缀")

        prefix_suffix_layout.addWidget(self.prefix, 1)
        prefix_suffix_layout.addWidget(self.suffix, 1)
        right_layout.addLayout(prefix_suffix_layout)

        # 正则A
        re_a_layout = QHBoxLayout()
        re_a_layout.setSpacing(8)

        self.re_a = QLineEdit()
        self.re_a.setPlaceholderText("正则A")

        self.re_a_r = QLineEdit()
        self.re_a_r.setPlaceholderText("替换A")

        re_a_layout.addWidget(self.re_a, 1)
        re_a_layout.addWidget(self.re_a_r, 1)
        right_layout.addLayout(re_a_layout)

        # 正则B
        re_b_layout = QHBoxLayout()
        re_b_layout.setSpacing(8)

        self.re_b = QLineEdit()
        self.re_b.setPlaceholderText("正则B")

        self.re_b_r = QLineEdit()
        self.re_b_r.setPlaceholderText("替换B")

        re_b_layout.addWidget(self.re_b, 1)
        re_b_layout.addWidget(self.re_b_r, 1)
        right_layout.addLayout(re_b_layout)

        # 连接信号
        for w in [self.prefix, self.suffix, self.re_a, self.re_a_r, self.re_b, self.re_b_r]:
            w.textChanged.connect(self.refresh_preview)

        # 执行按钮
        self.apply_btn = QPushButton("执行重命名")
        self.apply_btn.clicked.connect(self.execute_rename)
        right_layout.addWidget(self.apply_btn)

        # 预览部分 - 分成两列
        preview_header = QHBoxLayout()

        old_header = QLabel("原名称")
        new_header = QLabel("新名称")

        preview_header.addWidget(old_header, 1)
        preview_header.addWidget(new_header, 1)

        right_layout.addLayout(preview_header)

        # 使用两个文本框分别显示旧名和新名
        preview_splitter = QSplitter(Qt.Horizontal)
        preview_splitter.setHandleWidth(2)

        # 左侧显示旧名称
        self.old_log = QTextEdit()
        self.old_log.setReadOnly(True)
        self.old_log.setLineWrapMode(QTextEdit.NoWrap)

        # 右侧显示新名称
        self.new_log = QTextEdit()
        self.new_log.setReadOnly(True)
        self.new_log.setLineWrapMode(QTextEdit.NoWrap)

        preview_splitter.addWidget(self.old_log)
        preview_splitter.addWidget(self.new_log)

        right_layout.addWidget(preview_splitter, 1)

        splitter.addWidget(right_frame)
        splitter.setSizes([350, 650])

    def apply_style(self):
        # 简约风格样式
        self.setStyleSheet("""
        QWidget {
            background: #ffffff;
            color: #000000;
            font-family: "Microsoft YaHei", sans-serif;
            font-size: 12px;
        }

        QLabel {
            color: #333333;
            font-size: 12px;
        }

        QLineEdit {
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px 8px;
            font-size: 12px;
            min-height: 24px;
        }

        QLineEdit:focus {
            border: 1px solid #0078d4;
        }

        QPushButton {
            background: #f5f5f5;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 6px 12px;
            font-size: 12px;
            min-height: 28px;
        }

        QPushButton:hover {
            background: #e8e8e8;
        }

        QPushButton:pressed {
            background: #d9d9d9;
        }

        QTreeWidget {
            border: 1px solid #cccccc;
            border-radius: 3px;
            font-size: 12px;
        }

        QTreeWidget::item {
            padding: 4px;
        }

        QTreeWidget::item:selected {
            background: #e6f3ff;
            color: #000000;
        }

        QTreeWidget::item:hover {
            background: #f0f0f0;
        }

        QHeaderView::section {
            background: #f5f5f5;
            border: none;
            border-bottom: 1px solid #cccccc;
            padding: 6px;
        }

        QTextEdit {
            border: 1px solid #cccccc;
            border-radius: 3px;
            font-family: "Consolas", monospace;
            font-size: 11px;
            padding: 4px;
        }

        QSplitter::handle {
            background: #e0e0e0;
            width: 2px;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 10px;
        }

        QScrollBar::handle:vertical {
            background: #c0c0c0;
            border-radius: 5px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #a0a0a0;
        }
        """)

    # =============================
    # Folder & Tree
    # =============================
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.root_obj = build_file_tree(folder)
            self.refresh_tree()
            self.refresh_preview()

    def build_tree_item(self, obj):
        item = QTreeWidgetItem([obj["name"]])
        for child in obj.get("children", []):
            item.addChild(self.build_tree_item(child))
        return item

    def refresh_tree(self):
        self.tree.clear()
        if self.root_obj:
            self.tree.addTopLevelItem(self.build_tree_item(self.root_obj))
            self.tree.collapseAll()

    def on_tree_selection(self):
        items = self.tree.selectedItems()
        self.selected_nodes = []

        def map_item_to_obj(item, obj):
            if item.isSelected():
                self.selected_nodes.append(obj)
            for child_item, child_obj in zip([item.child(i) for i in range(item.childCount())],
                                             obj.get("children", [])):
                map_item_to_obj(child_item, child_obj)

        if self.root_obj:
            map_item_to_obj(self.tree.topLevelItem(0), self.root_obj)
        self.refresh_preview()

    # =============================
    # Preview & Rename
    # =============================
    def refresh_preview(self):
        self.engine.prefix = self.prefix.text()
        self.engine.suffix = self.suffix.text()
        self.engine.regex_a = (self.re_a.text(), self.re_a_r.text())
        self.engine.regex_b = (self.re_b.text(), self.re_b_r.text())

        old_scroll_pos = self.old_log.verticalScrollBar().value()
        new_scroll_pos = self.new_log.verticalScrollBar().value()

        self.old_log.clear()
        self.new_log.clear()

        targets = []
        for node in self.selected_nodes:
            targets.extend(collect_all_nodes(node))

        if not targets:
            return

        for index, obj in enumerate(targets):
            old = obj["name"]
            new = self.engine.rename(old)
            self.old_log.append(old)
            self.new_log.append(new)

        # 保持两个文本框的滚动位置同步
        self.old_log.verticalScrollBar().setValue(old_scroll_pos)
        self.new_log.verticalScrollBar().setValue(old_scroll_pos)  # 使用相同的滚动位置

    def execute_rename(self):
        if not self.selected_nodes:
            return

        targets = []
        for node in self.selected_nodes:
            targets.extend(collect_all_nodes(node))

        results = []
        success_count = 0

        # 执行重命名
        for obj in targets:
            old = obj["name"]
            new = self.engine.rename(old)
            if old != new:
                if change_name(obj, new):
                    results.append({"old": old, "new": new, "path": obj["path"]})
                    success_count += 1

        # 显示结果
        self.old_log.clear()
        self.new_log.clear()

        if success_count > 0:
            for r in results:
                self.old_log.append(r['old'])
                self.new_log.append(r['new'])

            # 添加统计信息
            self.old_log.append("")  # 空行
            self.old_log.append("总计:")
            self.new_log.append("")  # 空行
            self.new_log.append(f"{success_count} 个文件已重命名")
        else:
            self.old_log.append("没有需要重命名的文件")
            self.new_log.append("")

        # 更新树显示
        self.refresh_tree()


# =============================
# Entry
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = RenameToolUI()
    ui.show()
    sys.exit(app.exec())