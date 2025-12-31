import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from unittest.mock import patch
from pro import LedgerApp
import os


@pytest.fixture
def integration_app(tmp_path):
    """
    集成测试环境：创建一个真实的临时数据库文件
    """
    app = QApplication.instance() or QApplication([])
    db_path = tmp_path / "integration_test.db"
    LedgerApp.db_name = str(db_path)

    window = LedgerApp()
    yield window
    window.conn.close()


### 组 1：自底向上集成 - 添加记录到显示
def test_integration_add_to_display(integration_app):
    # 1. 模拟用户在 UI 上的操作
    integration_app.item_edit.setText("集成测试项")
    integration_app.amount_spin.setValue(123.45)
    integration_app.type_combo.setCurrentText("收入")

    # 2. 触发点击事件
    integration_app.add_record()

    # 3. 验证数据库层 (底层)
    integration_app.cursor.execute("SELECT * FROM records WHERE item='集成测试项'")
    db_record = integration_app.cursor.fetchone()
    assert db_record is not None
    assert db_record[4] == 123.45  # amount 字段

    # 4. 验证 UI 显示层 (顶层)
    # 确认表格第一行是否显示了该数据
    assert integration_app.table.rowCount() == 1
    assert "123.45" in integration_app.table.item(0, 4).text()
    assert "当前余额: ¥ 123.45" in integration_app.balance_label.text()


### 组 2：交互逻辑集成 - 删除记录与状态同步
def test_integration_delete_and_status_sync(integration_app):
    # 1. 预置数据（模拟已有多条数据的情况）
    data = [
        ('2023-10-01', '项1', '收入', 200.0),
        ('2023-10-02', '项2', '支出', 50.0)
    ]
    integration_app.cursor.executemany(
        "INSERT INTO records (date, item, record_type, amount) VALUES (?,?,?,?)", data
    )
    integration_app.conn.commit()
    integration_app.load_data()

    # 2. 模拟选中“项2”并点击删除
    integration_app.table.selectRow(0)  # 假设排序后第一行是要删的

    # 模拟用户点击确认删除
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
        integration_app.delete_record()

    # 3. 验证一致性
    # 检查数据库：应剩 1 条
    integration_app.cursor.execute("SELECT count(*) FROM records")
    assert integration_app.cursor.fetchone()[0] == 1

    # 检查余额更新：200 - 0 = 200 (因为 50 的那笔被删了)
    assert "¥ 200.00" in integration_app.balance_label.text()