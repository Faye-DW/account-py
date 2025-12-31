import pytest
from logic import LedgerLogic

@pytest.fixture
def logic():
    # 使用内存数据库初始化逻辑类
    l = LedgerLogic(":memory:")
    yield l
    l.close()

def test_add_record(logic):
    # 测试添加功能
    success, msg = logic.add_record("2023-10-27", "测试支出", "支出", 50.0)
    assert success is True
    assert logic.calculate_balance() == -50.0

def test_add_empty_item(logic):
    # 测试边界条件：摘要为空
    success, msg = logic.add_record("2023-10-27", "", "支出", 10.0)
    assert success is False
    assert msg == "摘要不能为空"

def test_delete_record(logic):
    # 测试删除功能
    logic.add_record("2023-10-27", "待删除", "收入", 100.0)
    records = logic.get_all_records()
    record_id = records[0][0] # 获取自动生成的 ID
    success, msg = logic.delete_record(record_id)
    assert success is True
    assert logic.calculate_balance() == 0.0