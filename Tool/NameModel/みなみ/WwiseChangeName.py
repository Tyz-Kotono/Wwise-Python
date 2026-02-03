# PySide6-based Wwise Rename Tool
# UI style aligned to Wwise dark editor aesthetics, with hierarchy tree, indexed preview, and apply button

import sys
import re
from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QFrame, QPushButton, QSplitter, QGridLayout
)
from PySide6.QtCore import Qt, QTimer

Sound_TYPE = "Sound"
Event_TYPE = "Event"


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
# Wwise Helpers
# =============================

def get_object(client, object_id):
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "options": {"return": ["id", "name", "type", "children"]}
    })
    arr = result.get("return", [])
    return arr[0] if arr else None


def get_changeName(client, object_id, new_name):
    try:
        client.call("ak.wwise.core.object.setName", {
            "object": object_id,
            "value": new_name
        })
        return True
    except Exception as e:
        print(f"重命名对象时出错: {e}")
        return False


# =============================
# Main UI
# =============================

class RenameToolUI(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.engine = RenameEngine()
        self.objects = []
        self.all_objects = []  # 存储所有搜集到的对象
        self.setWindowTitle("Wwise Rename Tool")
        self.resize(1200, 700)
        self.build_ui()
        self.apply_style()
        self.poll_selection()

    def build_ui(self):
        root = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # Left: Hierarchy Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["对象", "类型"])

        width = self.tree.width()
        self.tree.header().setStretchLastSection(False)  # 禁止最后一列拉伸
        self.tree.setColumnWidth(0, int(width * 0.5))  # 对象列宽度350像素
        self.tree.setColumnWidth(1, int(width * 0.5))  # 类型列宽度150像素
        splitter.addWidget(self.tree)

        # Right Panel
        right = QFrame()
        right_layout = QVBoxLayout(right)
        splitter.addWidget(right)
        splitter.setSizes([400, 600])

        # Inputs
        form = QHBoxLayout()
        self.prefix = QLineEdit()
        self.prefix.setPlaceholderText("请输入前缀，例如：SFX_")
        self.suffix = QLineEdit()
        self.suffix.setPlaceholderText("请输入后缀，例如：_Loop")
        self.re_a = QLineEdit()
        self.re_a.setPlaceholderText("正则规则 A（匹配）")
        self.re_a_r = QLineEdit()
        self.re_a_r.setPlaceholderText("正则 A 替换为")
        self.re_b = QLineEdit()
        self.re_b.setPlaceholderText("正则规则 B（匹配）")
        self.re_b_r = QLineEdit()
        self.re_b_r.setPlaceholderText("正则 B 替换为")

        for w in [self.prefix, self.suffix, self.re_a, self.re_a_r, self.re_b, self.re_b_r]:
            w.textChanged.connect(self.refresh_preview)

        form.addWidget(self.prefix)
        form.addWidget(self.suffix)
        form.addWidget(self.re_a)
        form.addWidget(self.re_a_r)
        form.addWidget(self.re_b)
        form.addWidget(self.re_b_r)
        right_layout.addLayout(form)

        # Apply Button
        self.apply_btn = QPushButton("生成改名结果（打印 OldName / NewName / ID）")
        self.apply_btn.clicked.connect(self.execute_rename)
        right_layout.addWidget(self.apply_btn)

        # 预览区域 - 分成两列
        preview_frame = QFrame()
        preview_layout = QHBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # Old 列
        old_frame = QFrame()
        old_layout = QVBoxLayout(old_frame)
        old_layout.setContentsMargins(0, 0, 0, 0)
        old_label = QLabel("Old Name")
        old_label.setAlignment(Qt.AlignCenter)
        old_label.setStyleSheet("font-weight: bold; border-bottom: 1px solid #444; padding: 5px;")
        self.old_log = QTextEdit()
        self.old_log.setReadOnly(True)
        self.old_log.setLineWrapMode(QTextEdit.NoWrap)
        old_layout.addWidget(old_label)
        old_layout.addWidget(self.old_log)

        # New 列
        new_frame = QFrame()
        new_layout = QVBoxLayout(new_frame)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_label = QLabel("New Name")
        new_label.setAlignment(Qt.AlignCenter)
        new_label.setStyleSheet("font-weight: bold; border-bottom: 1px solid #444; padding: 5px;")
        self.new_log = QTextEdit()
        self.new_log.setReadOnly(True)
        self.new_log.setLineWrapMode(QTextEdit.NoWrap)
        new_layout.addWidget(new_label)
        new_layout.addWidget(self.new_log)

        # 设置两列等宽
        preview_layout.addWidget(old_frame, 1)  # 权重为1
        preview_layout.addWidget(new_frame, 1)  # 权重为1

        right_layout.addWidget(preview_frame)

    def apply_style(self):
        self.setStyleSheet("""
        QWidget { background:#1f1f1f; color:#d0d0d0; }
        QLineEdit { background:#2b2b2b; border:1px solid #3a3a3a; padding:4px; }
        QTextEdit { background:#151515; border:1px solid #333; }
        QTreeWidget { background:#181818; border:1px solid #333; }
        QLabel { font-size:11px; }
        QPushButton { background:#2d2d2d; border:1px solid #444; padding:6px; }
        QPushButton:hover { background:#3a3a3a; }
        """)

    # =============================
    # Core Refresh Logic
    # =============================

    def poll_selection(self):
        self.refresh_objects()
        QTimer.singleShot(800, self.poll_selection)

    def refresh_objects(self):
        sel = self.client.call("ak.wwise.ui.getSelectedObjects", {})
        self.objects = [get_object(self.client, o["id"]) for o in sel.get("objects", []) if
                        get_object(self.client, o["id"])]

        # BFS 收集所有对象（包括子节点）
        self.all_objects.clear()
        queue = list(self.objects)
        while queue:
            current = queue.pop(0)
            self.all_objects.append(current)
            if current["type"] != Sound_TYPE and current["type"] != Event_TYPE:
                for child_id in current.get("children", []):
                    child_obj = get_object(self.client, child_id["id"])
                    if child_obj:
                        queue.append(child_obj)

        self.refresh_tree()
        self.refresh_preview()

    def build_tree_item(self, obj):
        item = QTreeWidgetItem([obj["name"], obj["type"]])
        if obj["type"] != Sound_TYPE and obj["type"] != Event_TYPE:
            for child_id in obj.get("children", []):
                child_obj = get_object(self.client, child_id["id"])
                if child_obj:
                    item.addChild(self.build_tree_item(child_obj))
        return item

    def refresh_tree(self):
        self.tree.clear()
        for obj in self.objects:
            self.tree.addTopLevelItem(self.build_tree_item(obj))
        self.tree.expandAll()

    def refresh_preview(self):
        self.engine.prefix = self.prefix.text()
        self.engine.suffix = self.suffix.text()
        self.engine.regex_a = (self.re_a.text(), self.re_a_r.text())
        self.engine.regex_b = (self.re_b.text(), self.re_b_r.text())

        # 保存两个文本框的滚动位置
        old_scroll_pos = self.old_log.verticalScrollBar().value()
        new_scroll_pos = self.new_log.verticalScrollBar().value()

        # 清空两个文本框
        self.old_log.clear()
        self.new_log.clear()

        # 分别填充Old和New列
        for index, obj in enumerate(self.all_objects):
            old = obj["name"]
            new = self.engine.rename(old)

            # Old列 - 带索引号
            old_line = f"[{index}] {old}"
            self.old_log.append(old_line)

            # New列 - 如果名字有变化，显示为绿色，否则保持原色
            if old != new:
                self.new_log.append(f'<font color="green">{new}</font>')
            else:
                self.new_log.append(new)

        # 恢复滚动位置
        self.old_log.verticalScrollBar().setValue(old_scroll_pos)
        self.new_log.verticalScrollBar().setValue(new_scroll_pos)

    def execute_rename(self):
        results = []
        for obj in self.all_objects:
            old = obj["name"]
            new = self.engine.rename(old)
            if old != new:
                results.append({"id": obj["id"], "old_name": old, "new_name": new})
            get_changeName(self.client, obj["id"], new)
        print("Rename Payload:")
        for r in results:
            pprint(r)


# =============================
# Entry
# =============================

if __name__ == '__main__':
    try:
        with WaapiClient() as client:
            app = QApplication(sys.argv)
            ui = RenameToolUI(client)
            ui.show()
            sys.exit(app.exec())
    except CannotConnectToWaapiException:
        print("WAAPI not connected")