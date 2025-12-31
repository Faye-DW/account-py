import pytest
import os
import sqlite3
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from unittest.mock import patch
from pro import LedgerApp


@pytest.fixture(scope="session")
def app():
    """提供 QApplication 实例"""
    return QApplication([])


@pytest.fixture
def ledger(app, tmp_path):
    """
    为每个测试用例创建一个独立的本地 .db 文件
    """
    # 在系统的临时目录下生成一个独立的数据库文件
    db_file = tmp_path / "test_ledger.db"

    # 修改类属性以确保每个实例连接自己的数据库
    # 注意：这里需要确保 LedgerApp 内部使用 self.db_name
    LedgerApp.db_name = str(db_file)

    window = LedgerApp()
    yield window
    # 清理：关闭连接并物理删除数据库文件（可选，tmp_path会自动清理）
    window.conn.close()


# --- 子功能 1: 添加与数据库持久化测试 ---

def test_add_record_success(ledger):
    """测试正常添加记录"""
    ledger.item_edit.setText("超市买菜")
    ledger.amount_spin.setValue(15.5)
    ledger.type_combo.setCurrentText("支出")

    ledger.add_record()

    # 验证数据库是否写入
    ledger.cursor.execute("SELECT item, amount FROM records WHERE item='超市买菜'")
    res = ledger.cursor.fetchone()
    assert res is not None
    assert res[1] == 15.5
    # 验证 UI 重置
    assert ledger.item_edit.text() == ""


def test_add_record_empty_warning(ledger):
    """测试摘要为空时的弹窗拦截 (边界覆盖)"""
    ledger.item_edit.setText("")  # 空摘要

    with patch.object(QMessageBox, 'warning') as mock_warn:
        ledger.add_record()
        # 验证弹窗被触发
        mock_warn.assert_called_once()

    # 验证数据库没有记录
    ledger.cursor.execute("SELECT count(*) FROM records")
    assert ledger.cursor.fetchone()[0] == 0


# --- 子功能 2: 账务逻辑与覆盖率提升 ---

def test_balance_calculation_logic(ledger):
    """测试收支计算与余额颜色切换 (判定覆盖)"""
    # 插入一笔收入
    ledger.cursor.execute(
        "INSERT INTO records (date, item, record_type, amount) VALUES ('2023-01-01', '发工资', '收入', 100.0)")
    # 插入一笔大额支出导致欠债
    ledger.cursor.execute(
        "INSERT INTO records (date, item, record_type, amount) VALUES ('2023-01-01', '买相机', '支出', 150.0)")
    ledger.conn.commit()

    ledger.load_data()

    # 余额应为 100 - 150 = -50
    assert "¥ -50.00" in ledger.balance_label.text()
    # 验证负数变红逻辑 (Missing 路径覆盖)
    assert "color: red;" in ledger.balance_label.styleSheet()


def test_delete_record_cancel(ledger):
    """测试删除时点击'取消' (路径覆盖)"""
    ledger.cursor.execute(
        "INSERT INTO records (date, item, record_type, amount) VALUES ('2023-01-01', '不删我', '支出', 10.0)")
    ledger.conn.commit()
    ledger.load_data()

    # 选中第一行
    ledger.table.selectRow(0)

    # 模拟用户点击 No
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
        ledger.delete_record()

    # 验证记录还在
    ledger.cursor.execute("SELECT count(*) FROM records WHERE item='不删我'")
    assert ledger.cursor.fetchone()[0] == 1


def test_delete_record_confirm(ledger):
    """测试删除确认逻辑 (判定覆盖)"""
    # 不指定 ID，解决 UNIQUE 冲突报错
    ledger.cursor.execute(
        "INSERT INTO records (date, item, record_type, amount) VALUES ('2023-01-01', '要删除', '支出', 10.0)")
    ledger.conn.commit()
    ledger.load_data()

    ledger.table.selectRow(0)

    # 模拟用户点击 Yes
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        ledger.delete_record()

    ledger.cursor.execute("SELECT count(*) FROM records WHERE item='要删除'")
    assert ledger.cursor.fetchone()[0] == 0


def test_delete_no_selection_warning(ledger):
    """测试未选中行直接点击删除 (判定覆盖)"""
    # 清空选中
    ledger.table.clearSelection()
    ledger.table.setCurrentCell(-1, -1)

    with patch.object(QMessageBox, 'warning') as mock_warn:
        ledger.delete_record()
        mock_warn.assert_called_with(ledger, "提示", "请先选择要删除的行")