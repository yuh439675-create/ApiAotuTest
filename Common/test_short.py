import requests


class ShortDrama(Base):

    def __init__(self, page=None, headless=True):
        super().__init__(page=page, headless=headless)
        self.login_url = "https://o3khjyqv.reelchain.art/login"
        self.api_login_url = "https://o3khjyqv.reelchain.art/sqx_fast/sys/login"
        self.captcha_service_url = "https://upload.chaojiying.net/Upload/Processing.php"

    def login_with_captcha(self):
        """
        执行从 UI 自动化到接口的完整登录流程
        """
        try:
            print("🌐 访问并加载登录页面...")
            self.go_login_page()

            print("📸 获取验证码并处理...")
            latest_image_path, uuid = self.capture_and_save_captcha()

            print("🔍 调用验证码识别...")
            captcha_result = self._recognize_captcha(latest_image_path)

            print("✨ 开始提交登录...")
            token = self._perform_login(uuid=uuid, captcha_text=captcha_result)

            print(f"🎉 登录成功，返回Token: {token[:20]}")
            return token
        except Exception as e:
            print(f"❌ 登录失败: {str(e)}")
            raise

    def go_login_page(self):
        """
        访问登录页面并等待页面稳定
        """
        self._goto_url(self.login_url)
        self.page.wait_for_load_state("networkidle")

    def capture_and_save_captcha(self):
        """
        截图验证码并返回图片路径和uuid
        """
        try:
            # 截图并保存验证码
            print("📸 正在截图验证码...")
            self.locator_screenshot(locator=self.click_code, save_dir=Config.test_screenshot_dir)

            # 验证验证码图片
            captcha_img = self.page.locator(self.click_code)
            src_value = captcha_img.get_attribute("src")
            if not src_value:
                raise Exception("未能获取验证码图片的 src 属性")

            uuid = src_value.split('=')[-1] if '=' in src_value else src_value

            # 获取最新的图片
            image_files = glob.glob(os.path.join(Config.test_screenshot_dir, "*.png"))
            if not image_files:
                raise FileNotFoundError(f"目录 {Config.test_screenshot_dir} 下无图片文件")
            latest_image_path = max(image_files, key=os.path.getctime)

            return latest_image_path, uuid
        except Exception as e:
            raise Exception(f"验证码截图过程出错: {str(e)}")

    def _recognize_captcha(self, image_path):
        """
        调用验证码识别服务，返回识别的验证码
        """
        try:
            with open(image_path, "rb") as f:
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
                    return result['pic_str']
                else:
                    raise Exception(f"验证码识别失败: {result['err_str']}")
            else:
                raise Exception(f"验证码服务HTTP错误: {response.status_code}")
        except Exception as e:
            raise Exception(f"验证码识别过程出现异常: {str(e)}")

    def _perform_login(self, uuid, captcha_text):
        """
        提交登录请求并返回 token
        """
        try:
            data = {
                "username": "admin777",
                "password": "123456",
                "uuid": uuid,
                "captcha": captcha_text,
                "adminType": 1
            }

            response = requests.post(self.api_login_url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'token' in result:
                    return result['token']
                else:
                    raise Exception(f"登录响应中未找到token: {result}")
            else:
                raise Exception(f"登录HTTP请求错误: {response.status_code}")
        except Exception as e:
            raise Exception(f"登录过程错误: {str(e)}")