
from waapi import WaapiClient
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QVBoxLayout, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from my_external_module import process_single_id, channel_C_LFE
import json
import os

JSON_PATH = "SelectedWwiseObject.json"
TYPE_PRIORITY = {"State": 1, "Switch": 2, "Event": 3, "Sound": 4, "Other": 100}


class WwiseSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wwise 选择管理")
        self.resize(700, 380)

        # -------------------------------
        # 左侧按钮区（中文）
        # -------------------------------
        self.write_btn = QPushButton("写入选中对象")
        self.delete_btn = QPushButton("删除选中行")
        self.clear_btn = QPushButton("清空选择的所有物体")
        self.call_func_btn = QPushButton("搜集所有的GUID")
        self.channelCLFE = QPushButton("修改通道为  1.1")  # ✅ 新按钮
        self.channelC = QPushButton("修改通道为  1.0")  # ✅ 新按钮

        self.write_btn.clicked.connect(self.write_selection)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.clear_btn.clicked.connect(self.clear_json)
        self.call_func_btn.clicked.connect(self.call_external_function)
        self.channelCLFE.clicked.connect(self.setChannelTo_C_LFE)
        self.channelC.clicked.connect(self.setChannelTo_C_LFE)


        button_layout = QVBoxLayout()
        for btn in [self.write_btn, self.delete_btn, self.clear_btn, self.call_func_btn, self.channelCLFE, self.channelC]:
            button_layout.addWidget(btn)
        button_layout.addStretch()

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Type"])
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table_widget)
        self.setLayout(main_layout)

        self.refresh_table()

    # -----------------------------------------------------
    # 写入当前选中的对象
    # -----------------------------------------------------
    def write_selection(self):
        try:
            with WaapiClient() as client:
                selected = client.call(
                    "ak.wwise.ui.getSelectedObjects",
                    {},
                    options={"return": ["id", "type", "name"]}
                )
        except Exception as e:
            QMessageBox.critical(self, "WAAPI 错误", f"无法连接WAAPI：{e}")
            return

        if not selected.get("objects"):
            QMessageBox.warning(self, "无选中对象", "请在Wwise中选中一个对象。")
            return

        data = self.load_json()

        for obj in selected.get("objects"):
            obj_id = obj["id"]
            obj_name = obj["name"]
            obj_type = obj["type"]

            # 检查是否重复
            if not any(item["id"] == obj_id for item in data["history"]):
                data["history"].append({
                    "id": obj_id,
                    "name": obj_name,
                    "type": obj_type
                })

        # 保存并刷新
        self.save_json(data)
        self.refresh_table()

    # -----------------------------------------------------
    # 删除选中行（多选）
    # -----------------------------------------------------
    def delete_selected(self):
        selected_rows = sorted(
            {item.row() for item in self.table_widget.selectedItems()}, reverse=True
        )

        if not selected_rows:
            QMessageBox.warning(self, "未选中", "请先选择要删除的记录。")
            return

        data = self.load_json()
        for row in selected_rows:
            if row < len(data["history"]):
                del data["history"][row]

        self.save_json(data)
        self.refresh_table()

    # -----------------------------------------------------
    # 清空所有记录
    # -----------------------------------------------------
    def clear_json(self):
        if os.path.exists(JSON_PATH):
            os.remove(JSON_PATH)
        self.refresh_table()

    # -----------------------------------------------------
    # 刷新表格（按类型优先级排序）
    # -----------------------------------------------------
    def refresh_table(self):
        self.table_widget.setRowCount(0)
        data = self.load_json()
        new_history = []

        # 自动修复旧格式
        for item in data["history"]:
            if isinstance(item, str):
                new_history.append({
                    "id": item,
                    "name": "Unknown",
                    "type": "Unknown"
                })
            else:
                new_history.append(item)

        # 按 TYPE 优先级排序
        new_history.sort(key=lambda x: TYPE_PRIORITY.get(x["type"], 100))

        # 保存修复和排序后的数据
        data["history"] = new_history
        self.save_json(data)

        # 填充表格
        self.table_widget.setRowCount(len(new_history))
        for row, item in enumerate(new_history):
            name_item = QTableWidgetItem(item["name"])
            type_item = QTableWidgetItem(item["type"])
            # 隐藏ID
            name_item.setData(Qt.UserRole, item["id"])

            self.table_widget.setItem(row, 0, name_item)
            self.table_widget.setItem(row, 1, type_item)

    # -----------------------------------------------------
    # JSON IO
    # -----------------------------------------------------
    def load_json(self):
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return {"history": []}
        return {"history": []}

    def save_json(self, data):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def call_external_function(self):
        data = self.load_json()
        id_list = [item["id"] if isinstance(item, dict) else item for item in data["history"]]

        if not id_list:
            QMessageBox.warning(self, "无数据", "当前 JSON 没有任何 ID。")
            return

        try:
            result = process_single_id(id_list)
            QMessageBox.information(self, "完成", f"外部函数执行完成，返回值: {result}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"调用外部函数失败: {e}")

    # ---------- 新按钮函数 ----------
    def setChannelTo_C_LFE(self):
        try:
            channel_C_LFE()
            QMessageBox.information(self, "完成", "已在控制台打印所有收集的 Sound ID")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打印 ID 失败: {e}")
        # ---------- 新按钮函数 ----------

  


# 运行
if __name__ == "__main__":
    app = QApplication([])
    win = WwiseSelectionWindow()
    win.show()
    app.exec()
