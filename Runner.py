"""
测试执行入口
用法:
    python Runner.py                          # 运行全部用例
    python Runner.py -m smoke                 # 只运行冒烟用例
    python Runner.py -k test_login            # 关键字过滤
    python Runner.py --parallel               # 并行执行（自动检测 CPU 核数）
    python Runner.py --parallel -n 4          # 指定 4 个 worker
    API_ENV=prod python Runner.py             # 切换环境
"""
import os
import sys
import glob
import multiprocessing
import pytest
from Config.config import Config


def clean_screenshots():
    for f in glob.glob(os.path.join(Config.screenshots_path, "*.png")):
        os.remove(f)


def main():
    Config.ensure_dirs()
    clean_screenshots()

    allure_result = Config.AllureResult_path
    allure_report = Config.AllureReport_path

    args = sys.argv[1:]

    # --parallel 快捷开关：自动加 -n auto
    if "--parallel" in args:
        args.remove("--parallel")
        if "-n" not in args:
            cpu = multiprocessing.cpu_count()
            workers = max(2, cpu - 1)
            args.extend(["-n", str(workers)])
            print(f"[Runner] 并行模式: {workers} workers (CPU: {cpu})")

    base_args = [
        "-v", "-s",
        f"--alluredir={allure_result}",
        "--clean-alluredir",
    ]

    exit_code = pytest.main(base_args + args)

    os.system(f"allure generate {allure_result} -o {allure_report} --clean")
    os.system(f"allure open {allure_report} &")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
