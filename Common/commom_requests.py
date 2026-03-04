import urllib3
from urllib3.util.retry import Retry
from urllib.parse import urlencode
import time
import json
from Common.yaml_config import GetConfig
from Common.deal_with_response import deal_with_res

# 全局连接池管理
_global_pool_manager = None


def get_global_pool_manager():
    """获取全局连接池管理器，减少资源开销"""
    global _global_pool_manager
    if _global_pool_manager is None:
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        _global_pool_manager = urllib3.PoolManager(
            retries=retries,
            num_pools=50,  # 增加连接池数量
            maxsize=50,   # 最大连接数
            block=False   # 不阻塞等待连接
        )
    return _global_pool_manager


class Requests:
    def __init__(self, headers=None, timeout=None):
        # 使用全局连接池实例，提高连接复用率
        self.http = get_global_pool_manager()
        # 公共请求头设置，把对应的值设置好
        self.headers = headers
        self.timeout = timeout if timeout is not None else 30  # 默认30秒超时
        # 调用获取yaml里的url，把测试域名拿出来，下面做拼接接口用
        self.url = GetConfig().get_url()

    def get_request(self, path=None, params=None, headers=None):
        # 构建完整的URL
        full_url = self.url + path
        if params:
            full_url += '?' + urlencode(params)
        # 记录请求开始时间
        start_time = time.time()
        # 发送GET请求
        try:
            res = self.http.request('GET', full_url, headers=headers, timeout=self.timeout)
            # 记录请求结束时间
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            deal_with_res(params, res, full_url, 'GET', self.headers, response_time)
            return res
        except urllib3.exceptions.HTTPError as exc:
            raise Exception(f"GET 请求失败: {exc}")

    def post_request(self, path: str, data=None, json=None, dumps_json=None, body=None, files=None, headers=None, timeout=None):
        # 构建完整的URL
        full_url = self.url + path
        # 设置请求头
        request_headers = self.headers.copy() if self.headers else {}
        if headers:
            request_headers.update(headers)
        # 记录请求开始时间
        start_time = time.time()
        # 发送POST请求
        try:
            if data:
                res = self.http.request('POST', full_url, data=data, headers=request_headers, timeout=self.timeout)

            elif json:
                res = self.http.request('POST', full_url, json=json, headers=request_headers,timeout=self.timeout)

            elif dumps_json:
                res = self.http.request('POST', full_url, json=json.dumps(dumps_json), headers=request_headers,timeout=self.timeout)

            elif body:
                res = self.http.request('POST', full_url, body=body, headers=request_headers, timeout=self.timeout)

            elif files:
                res = self.http.request('POST', full_url, fields=files, headers=request_headers, timeout=self.timeout)

            else:
                res = self.http.request('POST', full_url, headers=request_headers, timeout=self.timeout)

            # 记录请求结束时间
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            deal_with_res(data or json, res, full_url, 'POST', request_headers, response_time)
            return res
        except urllib3.exceptions.HTTPError as exc:
            raise Exception(f"POST 请求失败: {exc}")

    def __del__(self):
        self.http.clear()
