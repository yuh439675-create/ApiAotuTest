"""
测试执行入口
用法:
    python Runner.py                          # 运行全部用例 + 自动打开报告
    python Runner.py --no-open                # 只生成报告，不打开（适合服务器/CI）
    python Runner.py -m smoke                 # 只运行冒烟用例
    python Runner.py -k test_login            # 关键字过滤
    python Runner.py --parallel               # 并行执行（自动检测 CPU 核数）
    python Runner.py --parallel -n 4          # 指定 4 个 worker
    API_ENV=prod python Runner.py             # 切换环境
"""
import os
import sys
import glob
import signal
import subprocess
import importlib
import multiprocessing
import pytest
from Config.config import Config


def _check_plugin(module_name, pip_name):
    """检查插件是否已安装。用 find_spec 避免 import，防止 pytest 报 PytestAssertRewriteWarning。"""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        pass
    print(f"\n[错误] 缺少依赖: {pip_name}")
    print(f"  请执行: pip install {pip_name}\n")
    return False


def clean_screenshots():
    for f in glob.glob(os.path.join(Config.screenshots_path, "*.png")):
        os.remove(f)


def _allure_available():
    """检查 allure 命令行是否已安装"""
    try:
        subprocess.run(["allure", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _install_allure():
    """未安装时自动安装 Allure CLI（macOS 用 brew，否则用 npm）"""
    print("\n[Runner] 未检测到 Allure CLI，正在尝试自动安装...")
    if sys.platform == "darwin":
        # macOS: 优先 brew
        try:
            if subprocess.run(["which", "brew"], capture_output=True).returncode == 0:
                print("[Runner] 使用 Homebrew 安装 allure...")
                ret = subprocess.run(["brew", "install", "allure"], capture_output=False)
                if ret.returncode == 0:
                    return True
        except FileNotFoundError:
            pass
    # 通用: npm 安装（需已安装 Node.js）
    try:
        if subprocess.run(["which", "npm"], capture_output=True).returncode == 0:
            print("[Runner] 使用 npm 安装 allure-commandline...")
            ret = subprocess.run(
                ["npm", "install", "-g", "allure-commandline"],
                capture_output=False,
            )
            if ret.returncode == 0:
                return True
    except FileNotFoundError:
        pass
    return False


def _kill_allure_serve():
    """关闭之前残留的 allure open / serve 进程，防止内存泄漏"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "allure.*open|allure.*serve"],
            capture_output=True, text=True,
        )
        pids = result.stdout.strip().split("\n")
        for pid in pids:
            if pid.strip():
                try:
                    os.kill(int(pid.strip()), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass
        if any(p.strip() for p in pids):
            print(f"[Runner] 已关闭 {len([p for p in pids if p.strip()])} 个残留 Allure 进程")
    except FileNotFoundError:
        pass


def main():
    Config.ensure_dirs()
    clean_screenshots()

    if not _check_plugin("allure_pytest", "allure-pytest"):
        sys.exit(1)

    allure_result = Config.AllureResult_path
    allure_report = Config.AllureReport_path

    args = sys.argv[1:]

    no_open = "--no-open" in args
    if no_open:
        args.remove("--no-open")

    use_parallel = "--parallel" in args
    if use_parallel:
        args.remove("--parallel")
        if not _check_plugin("xdist", "pytest-xdist"):
            sys.exit(1)
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

    # 生成报告（未安装则自动安装 Allure CLI）
    if not _allure_available():
        _install_allure()
    if _allure_available():
        os.system(f"allure generate {allure_result} -o {allure_report} --clean --lang zh")
        if no_open:
            print(f"\n[报告已生成] {allure_report}")
            print(f"  查看报告: allure open {allure_report}\n")
        else:
            _kill_allure_serve()
            subprocess.Popen(
                ["allure", "open", allure_report],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    else:
        print(f"\n[提示] Allure CLI 安装失败，跳过报告生成。")
        print(f"  报告数据已保存: {allure_result}")
        print(f"  请手动安装: macOS 执行 brew install allure，或访问 https://github.com/allure-framework/allure2/releases\n")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
