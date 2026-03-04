# ApiAotuTest — API 自动化测试框架使用教程

---

## 一、项目结构

```
ApiAotuTest/
├── Runner.py                    # 测试执行入口
├── pytest.ini                   # Pytest 配置
├── requirements.txt             # 依赖清单
├── .gitignore                   # Git 忽略规则
│
├── Config/                      # 配置层
│   ├── config.py                #   路径管理 + 环境切换
│   ├── Login.yaml               #   环境配置（URL / 账号 / 数据库）
│   └── Login.yaml.example       #   配置模板（不含敏感信息）
│
├── Common/                      # 公共层（框架核心）
│   ├── common_requests.py       #   HTTP 请求封装（Requests / AuthClient）
│   ├── assertions.py            #   链式断言工具
│   ├── login.py                 #   登录接口封装
│   ├── yaml_config.py           #   YAML 配置读取（单例）
│   ├── mysql_operate.py         #   MySQL 操作（连接池）
│   ├── deal_with_response.py    #   响应处理 → Allure 报告
│   ├── perf.py                  #   性能监控（自动统计接口耗时）
│   ├── logger.py                #   统一日志模块
│   ├── parse_excel.py           #   Excel 解析
│   └── tools.py                 #   通用工具函数
│
├── Test_Case/                   # 测试用例层
│   ├── conftest.py              #   Pytest 夹具（token / api / 性能追踪）
│   ├── test_login.py            #   登录测试示例
│   └── test_api_demo.py         #   数据驱动测试示例
│
├── Datas/                       # 测试数据层
│   ├── test_login.json          #   登录测试数据
│   └── test_api_data.yaml       #   数据驱动测试数据
│
├── Token_dir/                   # Token 缓存（自动生成）
├── Logs/                        # 日志（自动生成）
├── Test_Report/                 # 测试报告（自动生成）
│   ├── AllureResult/
│   ├── AllureReport/
│   └── screenshots/
└── Utils/                       # 工具脚本
```

---

## 二、环境搭建

### 2.1 安装依赖

```bash
cd ApiAotuTest
pip install -r requirements.txt
```

### 2.2 安装 Allure 命令行

```bash
# macOS
brew install allure

# 验证
allure --version
```

### 2.3 配置环境信息

复制模板文件并填入真实配置：

```bash
cp Config/Login.yaml.example Config/Login.yaml
```

编辑 `Config/Login.yaml`：

```yaml
# 接口基础地址（所有请求会自动拼接此前缀）
url: 'https://your-domain.com/api/'

# 账号配置（支持多用户）
user:
  yhb:
    username: admin01
    password: 123456
    code: 666666
  test_user:
    username: tester
    password: abcdef
    code: 666666

# 数据库配置（可选）
mysql:
  db: your_db
  host: 127.0.0.1
  password: '123456'
  port: 3306
  user: root
```

---

## 三、运行测试

### 3.1 基本运行

```bash
# 运行全部用例 + 自动生成 Allure 报告
python Runner.py

# 只运行某个文件
python Runner.py Test_Case/test_login.py

# 关键字过滤
python Runner.py -k test_login_success

# 按标记筛选
python Runner.py -m smoke
```

### 3.2 并行运行（加速）

```bash
# 自动检测 CPU 核数并行
python Runner.py --parallel

# 指定 4 个 worker
python Runner.py --parallel -n 4
```

### 3.3 切换环境

```bash
# 通过环境变量切换
API_ENV=prod python Runner.py
API_ENV=dev python Runner.py
```

### 3.4 直接用 pytest 运行（不生成报告）

```bash
pytest Test_Case/ -v -s
```

---

## 四、编写测试用例

### 4.1 最简用例

在 `Test_Case/` 目录下新建 `test_xxx.py`（文件名必须以 `test_` 开头）：

```python
import allure
from Common.assertions import assert_response


@allure.epic("订单管理")
@allure.feature("订单查询")
class TestOrder:

    @allure.title("查询订单列表")
    def test_order_list(self, api):
        # api("yhb") 返回带 token 的客户端
        resp = api("yhb").get("order/list", params={"page": 1, "size": 10})

        assert_response(resp) \
            .status_ok() \
            .json_field_exists("data.list") \
            .json_list_not_empty("data.list") \
            .response_time_less_than(3000)
```

**重点说明：**
- `api` 是 conftest.py 提供的 fixture，传入用户名即可获得**自动携带 token** 的客户端
- 不需要手动管理 token，框架自动处理登录、缓存、过期刷新
- 每个请求自动记录到 Allure 报告（含耗时）

### 4.2 三个内置 Fixture

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `token` | session | `token("yhb")` → 返回 token 字符串，自动缓存 |
| `api` | session | `api("yhb")` → 返回 AuthClient 实例，自带 token |
| `http` | session | 返回裸 Requests 实例，不带 token |

```python
def test_example(self, token, api, http):
    # 方式1：手动拿 token
    t = token("yhb")

    # 方式2：直接用带认证的客户端（推荐）
    resp = api("yhb").get("some/path")

    # 方式3：不需要认证的接口
    resp = http.get("public/path")
```

### 4.3 请求方法

`api("yhb")` 和 `http` 都支持以下方法：

```python
client = api("yhb")

# GET
resp = client.get("path", params={"key": "value"})

# POST JSON
resp = client.post("path", json={"name": "test"})

# POST 表单
resp = client.post("path", data={"name": "test"})

# POST 文件
resp = client.post("path", files={"file": open("a.png", "rb")})

# PUT
resp = client.put("path", json={"id": 1, "name": "new"})

# DELETE
resp = client.delete("path", params={"id": 1})

# 自定义 headers（会和 token 合并，不会覆盖）
resp = client.get("path", headers={"X-Custom": "value"})

# 完整 URL（跳过 base_url 拼接）
resp = client.get("https://other-api.com/endpoint")
```

---

## 五、断言工具

`assert_response(resp)` 返回链式断言对象，可以一直 `.` 下去：

### 5.1 状态码断言

```python
from Common.assertions import assert_response

assert_response(resp).status_ok()           # 断言 200
assert_response(resp).status_is(201)        # 断言指定状态码
```

### 5.2 JSON 字段断言

支持用 `.` 分隔的嵌套路径，数组用数字索引：

```python
# 假设响应 JSON：
# {
#   "code": 0,
#   "data": {
#     "list": [{"id": 1, "name": "test"}],
#     "total": 100
#   }
# }

assert_response(resp) \
    .json_field_equals("code", 0) \                  # 字段等于
    .json_field_exists("data.list") \                # 字段存在
    .json_field_contains("data.list.0.name", "te") \ # 字段包含子串
    .json_list_not_empty("data.list") \              # 列表非空
    .json_field_type("data.total", int)              # 字段类型
```

### 5.3 性能断言

```python
assert_response(resp).response_time_less_than(3000)  # 响应时间 < 3秒
```

### 5.4 组合使用（推荐写法）

```python
assert_response(resp) \
    .status_ok() \
    .json_field_equals("code", 0) \
    .json_field_exists("data") \
    .response_time_less_than(5000) \
    .log_result("查询订单")    # 记录到日志 + Allure
```

---

## 六、数据驱动测试

### 6.1 JSON 数据驱动

**数据文件** `Datas/test_login.json`：

```json
{
  "test_login_success": {
    "desc": "正常登录",
    "user": "yhb",
    "expect_code": 200,
    "expect_field": "data.loginCode"
  }
}
```

**用例文件**：

```python
import json, os
from Config.config import Config

def load_test_data():
    path = os.path.join(Config.Datas_path, "test_login.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

TEST_DATA = load_test_data()

class TestLogin:
    def test_login_success(self, token):
        data = TEST_DATA["test_login_success"]
        # ... 使用 data 里的参数
```

### 6.2 YAML 数据驱动 + parametrize

**数据文件** `Datas/test_api_data.yaml`：

```yaml
- case_name: "查询接口-正常请求"
  method: GET
  path: "sys/menu/nav"
  params: null
  expect_status: 200

- case_name: "查询接口-带分页"
  method: GET
  path: "sys/menu/nav"
  params:
    page: 1
  expect_status: 200
```

**用例文件**：

```python
import os, yaml, pytest, allure
from Common.assertions import assert_response
from Config.config import Config

def load_yaml_cases():
    path = os.path.join(Config.Datas_path, "test_api_data.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CASES = load_yaml_cases()

class TestApiDataDriven:

    @pytest.mark.parametrize("case", CASES, ids=[c["case_name"] for c in CASES])
    def test_api_with_data(self, api, case):
        allure.dynamic.title(case["case_name"])
        client = api("yhb")

        if case["method"] == "GET":
            resp = client.get(case["path"], params=case.get("params"))
        elif case["method"] == "POST":
            resp = client.post(case["path"], json=case.get("body"))

        assert_response(resp).status_is(case["expect_status"])
```

YAML 里加一条数据，就自动多一条用例，不用改代码。

---

## 七、Allure 报告标签

用装饰器给用例打标签，报告里按层级展示：

```python
import allure

@allure.epic("一级分类：业务线")       # 最大分类
@allure.feature("二级分类：模块")      # 功能模块
class TestXxx:

    @allure.story("三级分类：场景")    # 用户故事
    @allure.title("用例标题")          # 用例名称
    @allure.severity(allure.severity_level.BLOCKER)  # 严重级别
    def test_xxx(self):
        pass
```

**严重级别可选值：**
- `BLOCKER` — 阻塞
- `CRITICAL` — 严重
- `NORMAL` — 一般（默认）
- `MINOR` — 轻微
- `TRIVIAL` — 不重要

**Pytest 标记：**

```python
@pytest.mark.smoke       # 冒烟测试
@pytest.mark.regression  # 回归测试
def test_xxx(self):
    pass

# 运行冒烟用例
# python Runner.py -m smoke
```

---

## 八、Allure 报告里的性能数据

框架自动收集，**无需写任何额外代码**。

### 8.1 用例内 — 每个请求显示为 Step

打开某条用例的详情页，Test Body 区域会看到：

```
▸ [POST] sys/login                     ← allure step，自带耗时时间条
    附件: 耗时 | POST sys/login → "320ms (状态码: 200)"
    附件: 请求的URL / 入参报文 / 响应报文

▸ [GET] sys/menu/nav                   ← 第二个请求
    附件: 耗时 | GET sys/menu/nav → "150ms (状态码: 200)"
```

### 8.2 用例内 — 接口性能明细表

每条用例结束后，Tear Down 区域会自动附加「接口性能明细」附件：

```
用例总耗时: 485ms

序号   方法    接口URL                                      耗时
----------------------------------------------------------------
1     POST    https://xxx.com/api/sys/login                320ms
2     GET     https://xxx.com/api/sys/menu/nav             150ms
----------------------------------------------------------------
合计          共 2 个请求                                   470ms
```

### 8.3 全局 — 所有接口 P50/P90/P99 统计

全部用例跑完后，日志和 Allure 中输出全局汇总：

```
接口                                          次数    P50      P90      P99      Max
POST https://xxx.com/api/sys/login               5   320ms    450ms    480ms    512ms
GET  https://xxx.com/api/sys/menu/nav             8   120ms    180ms    190ms    195ms
```

超过 3 秒的接口会自动告警。阈值修改位置：`Common/perf.py` 中的 `SLOW_THRESHOLD_MS`。

---

## 九、数据库操作

```python
from Common.mysql_operate import MysqlOperate

db = MysqlOperate()

# 查询（参数化，防 SQL 注入）
result = db.query("SELECT * FROM user WHERE id = %s", (1,))
row = db.query_one("SELECT name FROM user WHERE id = %s", (1,))

# 插入 / 更新 / 删除
db.execute("INSERT INTO user (name, age) VALUES (%s, %s)", ("test", 20))
db.execute("UPDATE user SET age = %s WHERE id = %s", (25, 1))
db.execute("DELETE FROM user WHERE id = %s", (1,))

# 批量插入（性能远优于循环 execute）
data = [("user1", 20), ("user2", 25), ("user3", 30)]
db.execute_many("INSERT INTO user (name, age) VALUES (%s, %s)", data)
```

---

## 十、日志系统

```python
from Common.logger import log

log.info("普通信息")
log.debug("调试信息（只写文件，不输出控制台）")
log.warning("警告")
log.error("错误")
```

- 控制台：INFO 及以上
- 文件：DEBUG 及以上，按天轮转，保留 30 天
- 日志路径：`Logs/api_test.log`

---

## 十一、完整用例编写示例

以「用户管理」模块为例，完整演示一个增删改查的测试文件：

```python
"""Test_Case/test_user.py"""
import pytest
import allure
from Common.assertions import assert_response


@allure.epic("用户管理")
@allure.feature("用户 CRUD")
class TestUser:

    @allure.title("创建用户")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_create_user(self, api):
        resp = api("yhb").post("user/create", json={
            "name": "自动化测试用户",
            "phone": "13800138000",
        })
        assert_response(resp) \
            .status_ok() \
            .json_field_equals("code", 0) \
            .json_field_exists("data.id") \
            .log_result("创建用户")

    @allure.title("查询用户列表")
    def test_user_list(self, api):
        resp = api("yhb").get("user/list", params={"page": 1, "size": 10})
        assert_response(resp) \
            .status_ok() \
            .json_list_not_empty("data.list") \
            .response_time_less_than(2000) \
            .log_result("用户列表")

    @allure.title("修改用户信息")
    def test_update_user(self, api):
        resp = api("yhb").put("user/update", json={
            "id": 1,
            "name": "修改后的名称",
        })
        assert_response(resp) \
            .status_ok() \
            .json_field_equals("code", 0) \
            .log_result("修改用户")

    @allure.title("删除用户")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_user(self, api):
        resp = api("yhb").delete("user/delete", params={"id": 1})
        assert_response(resp) \
            .status_ok() \
            .json_field_equals("code", 0) \
            .log_result("删除用户")

    @allure.title("无权限访问")
    def test_no_permission(self, http):
        resp = http.get("user/list")
        assert_response(resp).status_is(401)
```

---

## 十二、速查表

| 需求 | 命令 / 代码 |
|------|------------|
| 运行全部用例 | `python Runner.py` |
| 运行单个文件 | `python Runner.py Test_Case/test_user.py` |
| 关键字过滤 | `python Runner.py -k "create or delete"` |
| 标记过滤 | `python Runner.py -m smoke` |
| 并行执行 | `python Runner.py --parallel` |
| 失败即停 | `python Runner.py -x` |
| 切换环境 | `API_ENV=prod python Runner.py` |
| 获取带认证客户端 | `client = api("yhb")` |
| 获取裸客户端 | `client = http` |
| 断言状态码 200 | `.status_ok()` |
| 断言 JSON 字段 | `.json_field_equals("data.code", 0)` |
| 断言字段存在 | `.json_field_exists("data.token")` |
| 断言列表非空 | `.json_list_not_empty("data.list")` |
| 断言响应时间 | `.response_time_less_than(3000)` |
| 记录到日志和报告 | `.log_result("用例名")` |
| 数据库查询 | `MysqlOperate().query("SELECT ...", (param,))` |
| 批量插入 | `MysqlOperate().execute_many(sql, data_list)` |
| 打日志 | `from Common.logger import log; log.info("xxx")` |
