"""
MySQL 操作封装
- 连接池：lock 只保护池本身，ping / connect 在 lock 外执行
- 支持 context manager（自动归还连接）
- 支持参数化查询（防 SQL 注入）
- 支持批量插入
"""
import pymysql
import threading
from queue import Queue, Empty
from contextlib import contextmanager
from Common.yaml_config import GetConfig

_pool = None
_pool_lock = threading.Lock()


class ConnectionPool:
    def __init__(self, config, max_size=10):
        self._config = config
        self._max_size = max_size
        self._pool = Queue(maxsize=max_size)
        self._size = 0
        self._lock = threading.Lock()

    def _create_conn(self):
        return pymysql.connect(
            host=self._config["host"],
            user=self._config["user"],
            password=self._config["password"],
            db=self._config["db"],
            port=self._config["port"],
            charset=self._config.get("charset", "utf8mb4"),
            autocommit=True,
            connect_timeout=5,
            read_timeout=30,
        )

    def acquire(self):
        # 1. 优先从空闲池取
        try:
            conn = self._pool.get_nowait()
        except Empty:
            conn = None

        # 2. 验证连接（在锁外做网络 IO）
        if conn is not None:
            try:
                conn.ping(reconnect=False)
                return conn
            except Exception:
                with self._lock:
                    self._size -= 1

        # 3. 创建新连接
        with self._lock:
            if self._size < self._max_size:
                self._size += 1
                need_create = True
            else:
                need_create = False

        if need_create:
            try:
                return self._create_conn()
            except Exception:
                with self._lock:
                    self._size -= 1
                raise

        # 4. 池满，阻塞等待（最多 10 秒）
        try:
            conn = self._pool.get(timeout=10)
            conn.ping(reconnect=True)
            return conn
        except Empty:
            raise TimeoutError("获取数据库连接超时（池已满）")

    def release(self, conn):
        try:
            self._pool.put_nowait(conn)
        except Exception:
            with self._lock:
                self._size -= 1
            try:
                conn.close()
            except Exception:
                pass

    def close_all(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass
        with self._lock:
            self._size = 0


def _get_pool():
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is None:
            cfg = GetConfig().get_mysql_config()
            _pool = ConnectionPool(cfg, max_size=10)
    return _pool


class MysqlOperate:
    def __init__(self):
        self.pool = _get_pool()

    @contextmanager
    def _connection(self):
        conn = self.pool.acquire()
        try:
            yield conn
        finally:
            self.pool.release(conn)

    def query(self, sql, params=None):
        """
        参数化查询
        :param sql: SQL 语句，占位符用 %s
        :param params: 参数元组或列表
        """
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def query_one(self, sql, params=None):
        with self._connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()

    def execute(self, sql, params=None):
        """执行 INSERT / UPDATE / DELETE"""
        with self._connection() as conn:
            with conn.cursor() as cur:
                affected = cur.execute(sql, params)
                conn.commit()
                return affected

    def execute_many(self, sql, data_list):
        """批量执行（比循环 execute 快数十倍）"""
        with self._connection() as conn:
            with conn.cursor() as cur:
                affected = cur.executemany(sql, data_list)
                conn.commit()
                return affected

    # 向后兼容
    def insert_update_table(self, sql, params=None):
        return self.execute(sql, params) > 0


if __name__ == "__main__":
    db = MysqlOperate()
    print(db.query("SHOW TABLES"))
