import os


class Config:
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 环境切换: dev / test / prod，可通过环境变量 API_ENV 指定
    ENV = os.getenv("API_ENV", "test")

    # 各目录路径

    Config_path = os.path.join(BASE_DIR, "Config")
    Datas_path = os.path.join(BASE_DIR, "Datas")
    Logs_path = os.path.join(BASE_DIR, "Logs")
    Xlsx_Words = os.path.join(BASE_DIR, "Xlsx-Word")
    util_path = os.path.join(BASE_DIR, "Utils")
    Token_dir = os.path.join(BASE_DIR, "Token_dir")

    # 测试报告相关
    AllureReport_path = os.path.join(BASE_DIR, "Test_Report", "AllureReport")
    AllureResult_path = os.path.join(BASE_DIR, "Test_Report", "AllureResult")
    screenshots_path = os.path.join(BASE_DIR, "Test_Report", "screenshots")

    # UI 自动化（BasePage）相关
    auth_dir = os.path.join(BASE_DIR, "Token_dir")  # 认证文件目录
    test_screenshot_dir = screenshots_path  # 截图目录

    # 配置文件路径
    Login_yaml_path = os.path.join(Config_path, "Login.yaml")
    code_image_path = os.path.join(BASE_DIR, "Config",'验证码动态图')

    # 数据文件路径
    data_yaml_path = os.path.join(BASE_DIR, "data_yaml_001.yaml")
    data_json_path = os.path.join(Datas_path, "data_json.json")

    @classmethod
    def ensure_dirs(cls):
        """确保所有必要的目录都存在"""
        dirs = [
            cls.Datas_path, cls.Logs_path, cls.Token_dir,
            cls.AllureReport_path, cls.AllureResult_path,
            cls.screenshots_path, cls.Xlsx_Words,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)


if __name__ == "__main__":
    Config.ensure_dirs()
    print(f"项目根目录: {Config.BASE_DIR}")
    print(f"当前环境: {Config.ENV}")
    print(f"数据目录: {Config.Datas_path}")
    print(f"日志目录: {Config.Logs_path}")
    print(f"报告目录: {Config.AllureReport_path}")
    print(f"报告: {Config.code_image_path}")
