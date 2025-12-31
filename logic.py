import sqlite3


class LedgerLogic:
    def __init__(self, db_name="my_ledger.db"):
        """初始化逻辑类，支持指定数据库名称（测试时可用 :memory:）"""
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """创建数据库表结构"""
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

    def add_record(self, date, item, r_type, amount):
        """
        添加数据逻辑
        返回: (bool, message)
        """
        item = item.strip()
        if not item:
            return False, "摘要不能为空"

        try:
            self.cursor.execute(
                "INSERT INTO records (date, item, record_type, amount) VALUES (?, ?, ?, ?)",
                (date, item, r_type, amount)
            )
            self.conn.commit()
            return True, "添加成功"
        except Exception as e:
            return False, str(e)

    def get_all_records(self):
        """获取所有记录，并按日期降序排列"""
        self.cursor.execute("SELECT * FROM records ORDER BY date DESC, id DESC")
        return self.cursor.fetchall()

    def calculate_balance(self):
        """计算当前总余额"""
        self.cursor.execute("SELECT record_type, amount FROM records")
        rows = self.cursor.fetchall()
        total = 0.0
        for r_type, amount in rows:
            if r_type == "收入":
                total += amount
            else:
                total -= amount
        return total

    def delete_record(self, record_id):
        """根据 ID 删除记录"""
        try:
            self.cursor.execute("DELETE FROM records WHERE id=?", (record_id,))
            self.conn.commit()
            return True, "删除成功"
        except Exception as e:
            return False, str(e)

    def close(self):
        """关闭连接"""
        self.conn.close()


# --- 简单的命令行使用示例 ---
if __name__ == "__main__":
    logic = LedgerLogic("my_ledger.db")

    # 示例添加
    success, msg = logic.add_record("2023-10-27", "买奶茶", "支出", 15.0)
    print(msg)

    # 示例查询
    print(f"当前余额: ¥ {logic.calculate_balance():.2f}")
    records = logic.get_all_records()
    for r in records:
        print(r)

    logic.close()