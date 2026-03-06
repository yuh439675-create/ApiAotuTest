"""
动态登录参数字段 — 登录前按需获取 captcha、uuid 等会变化的字段

用法：在本文件实现 get_dynamic_login_fields(user)，返回要合并到登录请求体的 dict。
Login.yaml 中对应字段可省略或写占位，实际值由本函数提供。
"""
import glob
import os
import time

import requests

from BasePage.Base import BasePage
from Common.common_requests import Requests
from Common.yaml_config import GetConfig
from Config.config import Config


class DynamicLoginFields(BasePage):
    """动态获取登录所需字段（captcha、uuid 等）"""

    def __init__(self):
        super().__init__()
        self._cfg = GetConfig()
        self.login_url = "https://admin.testshort.top/login"
        self.api_login_url = "https://admin.testshort.top/sqx_fast/sys/login"
        self.captcha_service_url = "https://upload.chaojiying.net/Upload/Processing.php"
        self.PAGE_TIMEOUT = 5000
        self.click_code = 'xpath=/html/body/div/div/div/div/form/div[3]/div/div/div[2]/img'

    def fetch(self, user: str) -> dict:
        """
        登录前动态获取会变化的字段（如 captcha、uuid），合并到请求体。
        :param user: 用户标识，如 "admin"
        :return: 要合并的字段 dict，如 {"captcha": "xxx", "uuid": "yyy"}
        """
        if user == "admin":
            """
                    综合UI与接口操作，完成从页面加载到登录的所有流程。
                    返回动态字段(uuid和captcha)。

                    :param user_type: 用户类型, 默认为 "admin"
                    :return: 包含 uuid 和 captcha 的字典
                    """
            try:
                # 1️⃣ 访问登录页面
                print("🌐 访问并加载登录页面...")
                self._goto_url(self.login_url)
                self.page.wait_for_load_state("networkidle")

                # 2️⃣ 截图验证码并保存
                print("📸 正在截图验证码...")
                self.locator_screenshot(locator=self.click_code, save_dir=Config.code_image_path)

                # 验证验证码图片是否加载
                captcha_img = self.page.locator(self.click_code)
                captcha_img.wait_for(state="visible", timeout=self.PAGE_TIMEOUT)
                src_value = captcha_img.get_attribute("src")
                if not src_value:
                    raise Exception("无法获取验证码图片的 src 属性")

                # 提取 uuid
                uuid = src_value.split('=')[-1] if '=' in src_value else src_value

                # 3️⃣ 获取最新截图路径
                image_files = glob.glob(os.path.join(Config.code_image_path, "*.png"))
                if not image_files:
                    raise FileNotFoundError(f"目录 {Config.code_image_path} 下无图片文件")
                latest_image_path = max(image_files, key=os.path.getctime)
                print(f"🖼️ 使用图片: {latest_image_path}")

                # 4️⃣ 调用验证码识别服务
                print("🔐 调用验证码识别服务...")
                with open(latest_image_path, "rb") as f:
                    user_file = f.read()

                data = {
                    "user": "verygood521888",
                    "pass": "yhb282426",
                    "softid": "9514d72e7c143002dfeb6839a6bf85ca",
                    "codetype": "1005",
                    "str_debug": ""
                }
                files = {"userfile": ("captcha.png", user_file)}

                response = requests.post(self.captcha_service_url, data=data, files=files, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result['err_no'] == 0:
                        captcha = result['pic_str']
                        print(f"✅ 验证码识别结果: {captcha}")
                    else:
                        raise Exception(f"验证码识别失败: {result['err_str']}")
                else:
                    raise Exception(f"验证码服务HTTP错误: {response.status_code}")

                # 删除图片
                os.remove(latest_image_path)
                print("🗑️ 截图已删除")

                # 5️⃣ 返回动态字段结果
                return {
                    "uuid": uuid,
                    "captcha": captcha
                }

            except Exception as e:
                print(f"❌ 动态登录字段获取失败: {str(e)}")
                try:
                    error_screenshot = os.path.join(Config.code_image_path, f"error_{int(time.time())}.png")
                    self.page.screenshot(path=error_screenshot)
                    print(f"📷 错误截图已保存: {error_screenshot}")
                except Exception:
                    pass
                raise
        else:
            return {}




def get_dynamic_login_fields(user: str) -> dict:
    """
    对外入口，保持与 login.py 兼容。
    :param user: 用户标识
    :return: 要合并的字段 dict
    """
    return DynamicLoginFields().fetch(user)




