import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QHeaderView, QMenu
)
from PySide6.QtCore import Qt
from waapi import WaapiClient, CannotConnectToWaapiException

class WwiseTableExplorer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wwise ShortID Explorer")
        self.resize(1000, 600)
        self.client = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 输入栏+按钮
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入 ShortID，用逗号分隔，回车执行查询")
        self.input_line.returnPressed.connect(self.query_shortids)

        self.query_btn = QPushButton("搜索")
        self.query_btn.clicked.connect(self.query_shortids)

        input_layout.addWidget(self.input_line, stretch=1)
        input_layout.addWidget(self.query_btn)
        main_layout.addLayout(input_layout)

        # 表格
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(4)
        self.info_table.setHorizontalHeaderLabels(["Name", "Type", "ShortID", "Path"])
        self.info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.info_table.setSelectionBehavior(QTableWidget.SelectItems)  # 可以选择单元格
        self.info_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.info_table.setAlternatingRowColors(True)

        header = self.info_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        total_width = self.width()
        header.resizeSection(0, int(total_width * 0.15))
        header.resizeSection(1, int(total_width * 0.10))
        header.resizeSection(2, int(total_width * 0.15))
        header.resizeSection(3, int(total_width * 0.35))

        # 支持右键复制
        self.info_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.info_table.customContextMenuRequested.connect(self.show_context_menu)

        # Ctrl+C 快捷复制选中的单元格
        self.info_table.addAction(self.create_copy_action())
        self.info_table.setFocus()

        main_layout.addWidget(self.info_table)

    def create_copy_action(self):
        action = self.info_table.addAction("Copy")
        action.setShortcut("Ctrl+C")
        action.triggered.connect(self.copy_selected_cells)
        return action

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = menu.addAction("复制选中单元格")
        copy_action.triggered.connect(self.copy_selected_cells)
        menu.exec(self.info_table.viewport().mapToGlobal(pos))

    def copy_selected_cells(self):
        selected_items = self.info_table.selectedItems()
        if not selected_items:
            return
        text = "\n".join([item.text() for item in selected_items])
        QApplication.clipboard().setText(text)

    def query_shortids(self):
        text = self.input_line.text()
        if not text.strip():
            return

        try:
            short_ids = [int(s.strip()) for s in text.split(",") if s.strip()]
        except ValueError:
            self.info_table.setRowCount(0)
            return

        self.info_table.setRowCount(0)

        try:
            if not self.client:
                self.client = WaapiClient()
        except CannotConnectToWaapiException:
            self.info_table.setRowCount(0)
            return

        for sid in short_ids:
            query = {
                "waql": f"$ where shortId = {sid}",
                "options": {
                    "return": ["id", "name", "type", "path", "shortId"]
                }
            }
            try:
                result = self.client.call("ak.wwise.core.object.get", query)
                objs = result.get("return", [])
                if not objs:
                    self.add_table_row([f"[ShortID={sid}] 未找到对象", "", str(sid), ""])
                    continue
                for obj in objs:
                    self.add_table_row([
                        obj.get("name", ""),
                        obj.get("type", ""),
                        str(obj.get("shortId", "")),
                        obj.get("path", "")
                    ])
            except Exception as e:
                self.add_table_row([f"[ShortID={sid}] 查询失败", "", str(sid), str(e)])

    def add_table_row(self, row_data):
        row = self.info_table.rowCount()
        self.info_table.insertRow(row)
        for col, value in enumerate(row_data):
            item = QTableWidgetItem(value)
            self.info_table.setItem(row, col, item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WwiseTableExplorer()
    window.show()
    sys.exit(app.exec())
