# mysql_operate.py 数据库操作使用教程

> 基于 `Common/mysql_operate.py` 的 MySQL 增删改查、复杂查询及跨文件调用说明。

---

## 一、前置配置

在 `Config/Login.yaml` 中配置 MySQL 连接信息：

```yaml
mysql:
  db: user_databases      # 数据库名
  host: 69.5.12.246
  port: 3306
  user: www
  password: 'your_password'
  charset: utf8mb4        # 可选，默认 utf8mb4
```

---

## 二、其他文件中的调用方式

```python
from Common.mysql_operate import MysqlOperate

db = MysqlOperate()
# 之后所有操作都用 db 调用
```

---

## 三、API 一览

| 方法 | 用途 | 返回值 |
|------|------|--------|
| `query(sql, params=None)` | 查询多条 | `list[tuple]` |
| `query_one(sql, params=None)` | 查询一条 | `tuple` 或 `None` |
| `execute(sql, params=None)` | 执行 INSERT/UPDATE/DELETE | 受影响行数 `int` |
| `execute_many(sql, data_list)` | 批量执行 | 受影响行数 `int` |

---

## 四、增（INSERT）

### 单条插入

```python
from Common.mysql_operate import MysqlOperate

db = MysqlOperate()

# 参数化：占位符用 %s，防止 SQL 注入
sql = "INSERT INTO user (name, age, email) VALUES (%s, %s, %s)"
params = ("张三", 25, "zhangsan@qq.com")

rows = db.execute(sql, params)
print(f"插入成功，影响 {rows} 行")
```

### 批量插入

```python
sql = "INSERT INTO user (name, age, email) VALUES (%s, %s, %s)"
data_list = [
    ("李四", 28, "lisi@qq.com"),
    ("王五", 30, "wangwu@qq.com"),
    ("赵六", 22, "zhaoliu@qq.com"),
]

rows = db.execute_many(sql, data_list)
print(f"批量插入成功，影响 {rows} 行")
```

---

## 五、删（DELETE）

```python
# 按条件删除
sql = "DELETE FROM user WHERE id = %s"
rows = db.execute(sql, (1001,))

# 批量删除
sql = "DELETE FROM user WHERE id IN (%s, %s, %s)"
rows = db.execute(sql, (1001, 1002, 1003))

# 注意：IN 子句数量不固定时，用字符串拼接
ids = [1001, 1002, 1003]
placeholders = ",".join(["%s"] * len(ids))
sql = f"DELETE FROM user WHERE id IN ({placeholders})"
rows = db.execute(sql, tuple(ids))
```

---

## 六、改（UPDATE）

```python
sql = "UPDATE user SET name = %s, age = %s WHERE id = %s"
params = ("张三丰", 26, 1001)

rows = db.execute(sql, params)
print(f"更新 {rows} 行")
```

---

## 七、查（SELECT）

### 查询多条

```python
# 无参数
sql = "SELECT id, name, age FROM user"
rows = db.query(sql)
# 返回: [(1, '张三', 25), (2, '李四', 28), ...]

# 带参数
sql = "SELECT id, name, age FROM user WHERE age > %s"
rows = db.query(sql, (20,))

# 多条件
sql = "SELECT * FROM user WHERE name = %s AND status = %s"
rows = db.query(sql, ("张三", 1))
```

### 查询一条

```python
sql = "SELECT id, name, age FROM user WHERE id = %s"
row = db.query_one(sql, (1001,))
# 返回: (1001, '张三', 25) 或 None

if row:
    user_id, name, age = row
    print(f"用户: {name}, 年龄: {age}")
```

---

## 八、复杂查询

### 1. 分页

```python
sql = "SELECT id, name, age FROM user ORDER BY id LIMIT %s OFFSET %s"
page, size = 1, 10
offset = (page - 1) * size
rows = db.query(sql, (size, offset))
```

### 2. 模糊查询

```python
sql = "SELECT id, name FROM user WHERE name LIKE %s"
rows = db.query(sql, ("%张%",))
```

### 3. IN 子句（数量不固定）

```python
ids = [1, 2, 3, 5]
placeholders = ",".join(["%s"] * len(ids))
sql = f"SELECT * FROM user WHERE id IN ({placeholders})"
rows = db.query(sql, tuple(ids))
```

### 4. 多表 JOIN

```python
sql = """
    SELECT u.id, u.name, o.order_no, o.amount
    FROM user u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.status = %s
"""
rows = db.query(sql, (1,))
```

### 5. 聚合查询

```python
sql = "SELECT COUNT(*) FROM user WHERE status = %s"
row = db.query_one(sql, (1,))
total = row[0] if row else 0

# 分组统计
sql = "SELECT status, COUNT(*) as cnt FROM user GROUP BY status"
rows = db.query(sql)
```

### 6. 子查询

```python
sql = """
    SELECT * FROM user
    WHERE id IN (SELECT user_id FROM orders WHERE amount > %s)
"""
rows = db.query(sql, (100,))
```

---

## 九、在测试用例中的用法

```python
# Test_Case/test_xxx.py
import pytest
from Common.mysql_operate import MysqlOperate


def test_user_exists(db):
    """校验数据库里是否存在对应用户"""
    sql = "SELECT id FROM user WHERE email = %s"
    row = db.query_one(sql, ("test@qq.com",))
    assert row is not None, "用户不存在"


@pytest.fixture
def db():
    return MysqlOperate()
```

---

## 十、注意事项

1. **占位符**：统一用 `%s`，不要用字符串拼接，防止 SQL 注入。
2. **参数类型**：`params` 必须是 `tuple` 或 `list`，不能是 `dict`。
3. **批量执行**：`execute_many` 比循环 `execute` 快很多，大批量插入时优先使用。
4. **返回值**：`query` 返回 `list[tuple]`，`query_one` 返回 `tuple` 或 `None`，按索引取列：`row[0]`、`row[1]`。

---

## 十一、快速参考

```python
from Common.mysql_operate import MysqlOperate

db = MysqlOperate()

# 查
db.query("SELECT * FROM t WHERE id = %s", (1,))
db.query_one("SELECT * FROM t WHERE id = %s", (1,))

# 增
db.execute("INSERT INTO t (a,b) VALUES (%s,%s)", ("a", "b"))

# 改
db.execute("UPDATE t SET a=%s WHERE id=%s", ("a", 1))

# 删
db.execute("DELETE FROM t WHERE id=%s", (1,))

# 批量增
db.execute_many("INSERT INTO t (a,b) VALUES (%s,%s)", [("a", "b"), ("c", "d")])
```
