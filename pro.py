import sys
import sqlite3
# from datetime import datetime
# pylint: disable=no-name-in-module, import-error
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QDateEdit, QComboBox,
                             QDoubleSpinBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
                             QAbstractItemView, QGroupBox)

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont


class LedgerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.db_name = "my_ledger.db"
        self.init_db()
        self.init_ui()
        self.load_data()

    def init_db(self):
        """初始化数据库 (和之前逻辑一致)"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item TEXT,
                record_type TEXT,
                amount REAL
            )
        ''')
        self.conn.commit()

    def init_ui(self):
        """初始化 PyQt 界面"""
        self.setWindowTitle("Python 记账本 (PyQt6 版)")
        self.resize(700, 600)

        # 主布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # --- 1. 输入区域 ---
        input_group = QGroupBox("记一笔")
        form_layout = QFormLayout()

        # 日期控件 (自带日历弹窗)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")

        # 摘要输入
        self.item_edit = QLineEdit()
        self.item_edit.setPlaceholderText("例如：超市购物、工资...")

        # 金额输入 (只能输数字)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 10000000.00)
        self.amount_spin.setPrefix("¥ ")

        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["支出", "收入"])

        # 添加按钮
        self.add_btn = QPushButton("添加记录")
        self.add_btn.setStyleSheet("background-color: #0078d7; color: white; padding: 6px; font-weight: bold;")
        self.add_btn.clicked.connect(self.add_record)

        form_layout.addRow("日期:", self.date_edit)
        form_layout.addRow("摘要:", self.item_edit)
        form_layout.addRow("金额:", self.amount_spin)
        form_layout.addRow("类型:", self.type_combo)
        form_layout.addRow(self.add_btn)

        input_group.setLayout(form_layout)
        main_layout.addWidget(input_group)

        # --- 2. 表格区域 ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "日期", "摘要", "类型", "金额"])
        # 隐藏ID列
        self.table.hideColumn(0)
        # 表格自适应宽度
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 整行选中
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        # 禁止编辑
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        main_layout.addWidget(self.table)

        # --- 3. 底部统计与操作 ---
        bottom_layout = QHBoxLayout()

        self.balance_label = QLabel("当前余额: ¥ 0.00")
        self.balance_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        self.del_btn = QPushButton("删除选中行")
        self.del_btn.setStyleSheet("background-color: #d9534f; color: white; padding: 6px;")
        self.del_btn.clicked.connect(self.delete_record)

        bottom_layout.addWidget(self.balance_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.del_btn)

        main_layout.addLayout(bottom_layout)

    def add_record(self):
        """添加数据"""
        date = self.date_edit.date().toString("yyyy-MM-dd")
        item = self.item_edit.text().strip()
        r_type = self.type_combo.currentText()
        amount = self.amount_spin.value()

        if not item:
            QMessageBox.warning(self, "提示", "请输入摘要！")
            return

        self.cursor.execute("INSERT INTO records (date, item, record_type, amount) VALUES (?, ?, ?, ?)",
                            (date, item, r_type, amount))
        self.conn.commit()

        # 重置输入
        self.item_edit.clear()
        self.amount_spin.setValue(0.00)
        self.item_edit.setFocus()

        self.load_data()

    def load_data(self):
        """读取并显示数据"""
        self.table.setRowCount(0)  # 清空表格
        self.cursor.execute("SELECT * FROM records ORDER BY date DESC, id DESC")
        rows = self.cursor.fetchall()

        total = 0.0

        for row_idx, row_data in enumerate(rows):
            r_id, r_date, r_item, r_type, r_amount = row_data

            self.table.insertRow(row_idx)

            # 设置单元格内容
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(r_date))
            self.table.setItem(row_idx, 2, QTableWidgetItem(r_item))

            # 类型带颜色
            type_item = QTableWidgetItem(r_type)
            if r_type == "收入":
                type_item.setForeground(QColor("green"))
                total += r_amount
            else:
                type_item.setForeground(QColor("red"))
                total -= r_amount
            self.table.setItem(row_idx, 3, type_item)

            # 金额格式化
            amount_item = QTableWidgetItem(f"¥ {r_amount:.2f}")
            # 右对齐
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 4, amount_item)

        # 更新余额显示
        self.balance_label.setText(f"当前余额: ¥ {total:.2f}")
        if total < 0:
            self.balance_label.setStyleSheet("color: red;")
        else:
            self.balance_label.setStyleSheet("color: black;")

    def delete_record(self):
        """删除选中行"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return

        # 获取隐藏的第一列 ID
        record_id = self.table.item(current_row, 0).text()

        reply = QMessageBox.question(self, '确认', '确定要删除这条记录吗？',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM records WHERE id=?", (record_id,))
            self.conn.commit()
            self.load_data()

    def closeEvent(self, event):
        """关闭窗口时断开数据库连接"""
        self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置一个融合风格，让界面在不同系统上看起来都不错
    app.setStyle("Fusion")

    window = LedgerApp()
    window.show()
    sys.exit(app.exec())