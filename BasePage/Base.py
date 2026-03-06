# -*- coding:utf-8 -*-
import logging
import os
import platform
import time
from datetime import datetime
from typing import Optional, Union

import pyautogui
import pytesseract
from PIL import Image, ImageEnhance
from playwright.sync_api import expect, Page, sync_playwright, Locator

from Config.config import Config
from library.build import BuildInLibrary


class BasePage:
    # 默认按钮文本列表（可以在调用时通过 action_texts 参数覆盖）
    DEFAULT_ACTION_TEXTS = ("Confirm cancellation", "确认注销", "注销用户", "确认", "确定")
    def __init__(self, page: Page = None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = page
        self._is_self_managed = False

        # 设置服务器环境
        # 🎯 Xvfb (X Virtual Framebuffer)
        os.environ['DISPLAY'] = ':99'

        if self.page is None:
            self._launch_browser()
            self._is_self_managed = True

    def _launch_browser(self):
        """启动浏览器 - 服务器优化版本"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,  # 服务器环境强制无头模式
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--headless=new'
                ]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
                           "Safari/537.36"
            )
            self.page = self.context.new_page()

            # 设置超时时间
            self.page.set_default_timeout(60000)
            self.page.set_default_navigation_timeout(90000)

        except Exception as e:
            raise Exception(f"启动浏览器失败: {e}")

    def _goto_url(self, url, timeout=90000, wait_until="load"):
        """
        导航到指定URL
        :param url: 目标URL
        :param timeout: 超时时间（毫秒），默认90000ms（90秒）
        :param wait_until: 等待条件，可选值: "load", "domcontentloaded", "networkidle", "commit"
        """
        try:
            self.page.goto(url, timeout=timeout, wait_until=wait_until)
        except Exception as e:
            print(f"导航到 {url} 失败: {e}")
            raise

    def _normalize_locator(self, locator):
        """将可能的 XPath 选择器转换为 Playwright 可识别格式"""
        if not isinstance(locator, str):
            return locator
        stripped = locator.lstrip()
        if stripped.startswith("xpath="):
            return locator
        if stripped.startswith(("/", "./", "../", "(")):
            return f"xpath={locator}"
        return locator

    def _locator(self, locator, frame_locator=None):
        """
        获取页面元素的定位器
        :param locator: 元素定位表达式（如 "text=登录"、".btn" 等）
        :param frame_locator: 可选，iframe 的定位表达式（如需在 iframe 内定位元素）
        :return: Playwright 的 Locator 对象，可用于后续操作（点击、输入等）
        """
        try:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
            if frame_locator is not None:
                # 如果指定了 iframe，先定位 iframe 再定位元素
                return self.page.frame_locator(normalized_frame).locator(normalized_locator)
            else:
                # 直接在当前页面定位元素
                return self.page.locator(normalized_locator)
        except Exception as e:
            print(f"定位元素失败：{e}")
            # 可根据需要抛出异常，让测试用例捕获
            # raise Exception(f"定位元素失败：{e}") from e

    def _click(self, locator, frame_locator=None):

        try:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
            if frame_locator is not None:
                self.page.frame_locator(normalized_frame).locator(normalized_locator).click()
            else:
                self.page.click(normalized_locator)
        except Exception as e:
            print(e)

    def get_all_timestamps(self, father_locator, child_locator):
        """提取页面中所有交易记录的时间戳
        Returns:
            包含所有时间字符串的列表，格式如["2025-08-07 02:08:12", ...]
        """
        try:
            # 定位包含所有交易记录的父容器
            normalized_father = self._normalize_locator(father_locator)
            normalized_child = self._normalize_locator(child_locator)
            parent_container = self.page.locator(normalized_father)

            # 等待父容器加载完成
            self.page.wait_for_timeout(1000)

            # 在父容器内定位所有时间元素
            time_elements = parent_container.locator(normalized_child).all()
            # 提取并清洗时间文本
            timestamps = [
                elem.text_content().strip()
                for elem in time_elements
                if elem.text_content()  # 过滤空文本
            ]

            return timestamps

        except Exception as e:
            print(f"提取时间戳时发生错误: {str(e)}")

    def _hover(self, locator, frame_locator=None):

        try:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
            if frame_locator is not None:
                self.page.frame_locator(normalized_frame).locator(normalized_locator).hover()
            else:
                self.page.hover(normalized_locator)
        except Exception as e:
            print(e)

    def _fill(self, locator, value, frame_locator=None):

        value = BuildInLibrary().repalce_parameter(value)
        try:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
            if frame_locator is not None:
                self.page.frame_locator(selector=normalized_frame).locator(selector_or_locator=normalized_locator).fill(
                    value
                )
            else:
                self.page.fill(selector=normalized_locator, value=value)
        except Exception as e:
            print(e)

    def _type(self, locator, value, frame_locator=None):

        value = BuildInLibrary().repalce_parameter(value)
        try:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
            if frame_locator is not None:
                self.page.frame_locator(selector=normalized_frame).locator(
                    selector_or_locator=normalized_locator
                ).type(text=value, delay=100)
            else:
                self.page.type(selector=normalized_locator, text=value, delay=100)
        except Exception as e:
            print(e)

    def _file(self, locator, files, frame_locator=None):

        try:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
            if frame_locator is not None:
                self.page.frame_locator(normalized_frame).locator(normalized_locator).set_input_files(files=files)
            else:
                self.page.locator(normalized_locator).set_input_files(files=files)
        except Exception as e:
            print(e)

    def _ele_to_be_visible(self, locator):

        normalized_locator = self._normalize_locator(locator)
        return expect(self.page.locator(normalized_locator)).to_be_visible()

    def _ele_to_be_visible_force(self, locator, frame_locator=None, timout: int = 5):

        ele = None
        normalized_locator = self._normalize_locator(locator)
        normalized_frame = self._normalize_locator(frame_locator) if frame_locator is not None else None
        if frame_locator is not None:
            ele = self.page.frame_locator(normalized_frame).locator(normalized_locator)
        else:
            ele = self.page.locator(normalized_locator)
        for t in range(0, timout):
            self.page.wait_for_timeout(500)
            if ele.is_visible():
                break
        else:
            raise Exception("元素未找到!")

    def _ele_is_checked(self, selector):

        normalized_selector = self._normalize_locator(selector)
        return self.page.is_checked(normalized_selector)

    def _browser_operation(self, reload=False, forward=False, back=False):

        if reload:
            self.page.reload()
        if back:
            self.page.go_back()
        if forward:
            self.page.go_forward()

    # 截图方法
    def screenshot(self, path, full_page=True, locator=None):

        if locator is not None:
            normalized_locator = self._normalize_locator(locator)
            self.page.locator(normalized_locator).screenshot(path=path)
            return path
        self.page.screenshot(path=path, full_page=full_page)
        return path

    def _del_auth(self):
        # 使用 os.path.join 拼接路径，适配不同操作系统（Windows/Linux/mac）
        auth_path = os.path.join(Config.auth_dir, "auth.json")
        try:
            # 检查文件是否存在并删除
            if os.path.exists(auth_path):
                os.remove(auth_path)
                # 可选：添加日志，便于调试
                # print(f"已删除认证文件: {auth_path}")
        except OSError as e:
            # 捕获删除时可能出现的异常（如文件被占用、权限不足等）
            print(f"删除认证文件失败: {e}")
            # 若需要中断程序，可改为 raise；否则记录异常后继续执行
            # raise

    def get_text_all(self, locator):
        # 1. 定位所有行容器（.cell 对应每一行）
        rows = self.page.locator('.cell').all()
        # 2. 遍历每行，提取时间文本
        all_times = []
        for row in rows:
            # 在当前行中，定位第一个 .time 元素（且不含 span 子元素，确保是时间而非状态）
            normalized_locator = self._normalize_locator(locator)
            time_element = row.locator(normalized_locator).first
            # 提取文本并添加到列表
            time_text = time_element.text_content().strip()
            all_times.append(time_text)
        return all_times

    # 获取指定元素定位的值
    def get_text(self, locator, frame_locator=None):
        """获取元素的文本内容"""
        if frame_locator is not None:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator)
            return self.page.frame_locator(normalized_frame).locator(normalized_locator).text_content()
        normalized_locator = self._normalize_locator(locator)
        return self.page.locator(normalized_locator).text_content()

    # 获取某标签 如class标签 的值
    def get_attribute(self, locator, attribute_name, frame_locator=None):
        """获取元素的属性值"""
        if frame_locator is not None:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator)
            return self.page.frame_locator(normalized_frame).locator(normalized_locator).get_attribute(attribute_name)
        normalized_locator = self._normalize_locator(locator)
        return self.page.locator(normalized_locator).get_attribute(attribute_name)

    # 获取输入框的值
    def get_value(self, locator, frame_locator=None):
        """获取输入框的值"""
        if frame_locator is not None:
            normalized_locator = self._normalize_locator(locator)
            normalized_frame = self._normalize_locator(frame_locator)
            return self.page.frame_locator(normalized_frame).locator(normalized_locator).input_value()
        normalized_locator = self._normalize_locator(locator)
        return self.page.locator(normalized_locator).input_value()

    def locate_by_text(
            self,
            text: str,
            selector: str = None,
            exact: bool = False,
            case_sensitive: bool = True,
            xpath: bool = False,
            timeout: int = 30000,
            click: bool = False,
            input_text: Optional[str] = None,
            wait_for_selector: Optional[str] = None,
            wait_for_timeout: int = 5000,
    ) -> Locator:
        """
        使用Playwright通过文本内容定位元素并执行操作

        Args:
            text: 要匹配的文本内容
            selector: 可选，CSS选择器，用于缩小查找范围
            exact: 是否精确匹配（默认模糊匹配）
            case_sensitive: 是否区分大小写（默认区分）
            xpath: 是否使用XPath语法（默认False）
            timeout: 等待元素出现的超时时间（毫秒）
            click: 是否点击找到的元素（默认False）
            input_text: 是否向找到的元素输入文本（默认None）
            wait_for_selector: 操作后等待的选择器（默认None）
            wait_for_timeout: 等待选择器的超时时间（毫秒）

        Returns:
            定位到的元素Locator对象

        Example:
            # 精确匹配并点击
            helper.locate_by_text("Fate  武尊白色剑", exact=True, click=True)

            # 模糊匹配并输入文本
            helper.locate_by_text("用户名", input_text="testuser")

            # 点击后等待页面加载
            helper.locate_by_text("登录", click=True, wait_for_selector=".dashboard")
        """
        if xpath:
            # XPath定位
            if exact:
                xpath_expr = f"//*[normalize-space(text())='{text}']"
            else:
                xpath_expr = f"//*[contains(normalize-space(text()), '{text}')]"

            if selector:
                xpath_expr = selector + xpath_expr

            locator = self.page.locator(xpath_expr)

        else:
            # CSS选择器定位
            if exact:
                text_selector = f"text='{text}'"
            else:
                text_selector = f"text={text}"

            if selector:
                # 在指定选择器内查找文本
                locator = self.page.locator(selector).locator(text_selector)
            else:
                locator = self.page.locator(text_selector)

        # 处理大小写不敏感的情况
        if not case_sensitive and not xpath:
            # 使用正则表达式实现不区分大小写匹配（更符合类型约定）
            import re
            pattern = re.compile(re.escape(text), re.IGNORECASE)
            locator = locator.filter(has_text=pattern)

        # 等待元素出现
        locator.wait_for(timeout=timeout)

        # 执行操作
        if click:
            locator.click()

        if input_text is not None:
            locator.fill(input_text)

        # 等待操作后的状态
        if wait_for_selector:
            self.page.wait_for_selector(wait_for_selector, timeout=wait_for_timeout)

        return locator

    # 简化版方法：直接点击文本
    def click_by_text(
            self,
            text: str,
            selector: str = None,
            exact: bool = False,
            case_sensitive: bool = True,
            xpath: bool = False,
            timeout: int = 30000,
            wait_for_selector: Optional[str] = None,
    ) -> None:
        """定位并点击包含指定文本的元素"""
        self.locate_by_text(
            text=text,
            selector=selector,
            exact=exact,
            case_sensitive=case_sensitive,
            xpath=xpath,
            timeout=timeout,
            click=True,
            wait_for_selector=wait_for_selector,
        )

    # 简化版方法：直接输入文本
    def input_by_text(
            self,
            label_text: str,
            input_text: str,
            selector: str = None,
            exact: bool = False,
            case_sensitive: bool = True,
            xpath: bool = False,
            timeout: int = 30000,
            wait_for_selector: Optional[str] = None,
    ) -> None:
        """定位包含指定标签文本的元素并输入内容"""
        self.locate_by_text(
            text=label_text,
            selector=selector,
            exact=exact,
            case_sensitive=case_sensitive,
            xpath=xpath,
            timeout=timeout,
            input_text=input_text,
            wait_for_selector=wait_for_selector,
        )

    # 增强图像识别
    def preprocess_image(self, image_path):
        """图像预处理增强OCR识别率"""
        img = Image.open(image_path)
        # 提高对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        # 转换为灰度
        img = img.convert('L')
        # 二值化
        img = img.point(lambda x: 0 if x < 128 else 255, '1')
        return img

    # 通过图像定位
    def fill_by_text(self, text_to_find: str, text_to_input: str, delay: int = 100, max_attempts: int = 3) -> bool:
        pyautogui.size()
        """
        改进版的文本查找和填充函数
        """
        clean_text = text_to_find.strip()
        screenshot_dir = Config.test_screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)

        for attempt in range(max_attempts):
            try:
                # 1. 截屏
                screenshot_path = os.path.join(screenshot_dir, f'attempt_{attempt}.png')
                # if platform.system() == 'Darwin':
                #     ImageGrab.grab().save(screenshot_path)
                # elif platform.system() == 'Windows':
                #     pyautogui.screenshot(screenshot_path)

                # 2. 图像预处理
                processed_img = self.preprocess_image(screenshot_path)

                # 3. OCR识别
                ocr_data = pytesseract.image_to_data(
                    processed_img,
                    lang='chi_tra+eng',  # 尝试组合语言
                    output_type='dict'
                )

                # 4. 查找文本
                for i, text in enumerate(ocr_data['text']):
                    if clean_text in text.strip():  # 使用包含关系而非精确匹配
                        x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                        y = ocr_data['top'][i] + ocr_data['height'][i] // 2

                        # 调试：显示找到的位置
                        print(f"找到文本 '{text.strip()}' 在位置 ({x}, {y})")

                        # 5. 点击并输入
                        pyautogui.click(100, 250)
                        time.sleep(1)

                        pyautogui.write(text_to_input, interval=delay / 1000)
                        print(f'看看这个值是啥：{text_to_input}')
                        return True

                print(f"尝试 {attempt + 1} 未找到文本，OCR结果: {ocr_data['text']}")
                time.sleep(2)

            except Exception as e:
                logging.error(f"尝试 {attempt + 1} 出错: {str(e)}")
                time.sleep(2)

        logging.error(f"多次尝试后仍未找到文本: {clean_text}")
        return False

    # 页面后退
    def go_back(self):
        """浏览器原生后退（返回上一个历史记录页面）"""
        try:
            self.page.go_back()
            print("已执行后退操作")
        except Exception as e:
            print(f"后退失败：{e}")

    # 页面前进
    def go_forward(self):
        """浏览器原生后退（返回上一个历史记录页面）"""
        try:
            self.page.go_forward()
            print("已执行后退操作")
        except Exception as e:
            print(f"后退失败：{e}")

    def get_element_xpath_by_text(self,
                                  text: str,
                                  tag: str = "*",
                                  is_span: bool = False,
                                  exact_match: bool = True
                                  ) -> str:
        """根据文本值生成XPath（独立工具函数，不含self）"""
        escaped_text = text.replace('"', '\\"')  # 这里的text是传入的字符串，而非类实例
        if is_span:
            if exact_match:
                return f'//{tag}[.//span/text()="{escaped_text}"]'
            else:
                return f'//{tag}[.//span[contains(text(), "{escaped_text}")]]'
        else:
            if exact_match:
                return f'//{tag}[text()="{escaped_text}" or .//*[text()="{escaped_text}"]]'
            else:
                return f'//{tag}[contains(text(), "{escaped_text}") or .//*[contains(text(), "{escaped_text}")]]'

    def locator_screenshot(self,
                           locator: Union[str, Locator],
                           save_dir: str = "screenshots",  # 截图保存目录
                           file_name: str = None,  # 自定义文件名（None则自动生成）
                           timeout: float = 5000
                           ) -> Optional[dict]:
        """
        截取指定元素的区域截图（优化版：简洁时间戳命名）

        Args:
            locator: 元素定位器（XPath 字符串 或 CSS 字符串 或 已定位的 Locator 对象）
            save_dir: 截图保存目录（默认：screenshots）
            file_name: 自定义文件名（如 "captcha.png"，None则自动生成）
            timeout: 元素定位超时时间（毫秒）

        Returns:
            元素边界框信息字典（x, y, width, height, save_path），失败返回 None

        Raises:
            TimeoutError: 元素定位超时
            ValueError: 元素无法获取边界框
            OSError: 目录创建失败
        """
        # 生成基础时间戳（格式：20251128011546）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)

        try:
            # 处理定位器类型
            if isinstance(locator, str):
                normalized_locator = self._normalize_locator(locator)
                element = self.page.locator(normalized_locator)
            elif isinstance(locator, Locator):
                element = locator
            else:
                raise TypeError("locator 必须是字符串（XPath/CSS）或 Locator 对象")

            # 等待元素可见并获取边界框
            element.wait_for(state="visible", timeout=timeout)
            bounding_box = element.bounding_box()

            if not bounding_box:
                raise ValueError("无法获取元素边界框，元素可能不可见或已销毁")

            # 处理文件名：成功场景（success_20251128011546.png）
            if not file_name:
                file_name = f"success_{timestamp}.png"

            save_path = os.path.join(save_dir, file_name)

            # 截取元素区域截图
            self.page.screenshot(
                path=save_path,
                clip={
                    "x": bounding_box["x"],
                    "y": bounding_box["y"],
                    "width": bounding_box["width"],
                    "height": bounding_box["height"]
                },
                omit_background=False
            )

            print(f"✅ 元素截图成功保存至: {save_path}")
            return {
                **bounding_box,
                "save_path": save_path,
                "status": "success"
            }

        except Exception as e:
            # 处理文件名：失败场景（error_20251128011546.png）
            if not file_name:
                file_name = f"error_{timestamp}.png"

            error_save_path = os.path.join(save_dir, file_name)

            # 失败时截取全屏作为错误证据
            self.page.screenshot(path=error_save_path, full_page=True)

            print(f"❌ 截图失败：{str(e)}，错误截图已保存至: {error_save_path}")

            # 根据异常类型抛出对应错误
            if isinstance(e, TimeoutError):
                raise TimeoutError(f"元素定位超时（{timeout}ms），定位器：{locator}")
            elif isinstance(e, ValueError):
                raise ValueError(f"{e}")
            elif isinstance(e, TypeError):
                raise TypeError(f"{e}")
            else:
                raise Exception(f"截图失败：{str(e)}")

    def _find_row_by_email(self, email: str, timeout: int = 30000):
        """
        根据邮箱查找对应的表格行
        :param email: 邮箱地址
        :param timeout: 超时时间（毫秒）
        :return: 找到的行定位器
        """
        email_locator = self.page.locator(f"text={email}")
        row_candidates = [
            self.page.locator("tr", has=email_locator),
            self.page.locator("[role='row']", has=email_locator),
            self.page.locator(".el-table__row", has_text=email),
        ]

        for candidate in row_candidates:
            try:
                candidate.first.wait_for(state="visible", timeout=timeout)
                return candidate.first
            except Exception:
                continue

        raise Exception(f"未找到邮箱 {email} 对应的行")

    # 点击某个元素值同一行内容的方法
    def click_row_locator(
            self,
            email: str,
            action_texts=None,
            timeout: int = 30000
    ):

        """
        │  ┌──────┬──────────────────────┬──────────────────────┐   │
        │  │ ID   │ Email                │ Action               │   │
        │  ├──────┼──────────────────────┼──────────────────────┤   │
        │  │ 10325│ test_100@gmail.com   │ Confirm cancellation │   │ ← 目标行
        │  │ 10324│ 未绑定                │ Confirm cancellation │   │
        │  │ 10323│ 未绑定                │ 确认注销              │   │
        │  └──────┴──────────────────────┴──────────────────────┘
        点击指定邮箱对应行的确认注销按钮
        :param email: 邮箱地址
        :param action_texts: 按钮文本，支持多种格式：
                           - 逗号分隔的字符串（推荐）："注销用户,Confirm cancellation"
                           - 列表：["Confirm cancellation", "确认注销"]
                           - 元组：("注销用户", "确认")
                           - 单个字符串："确认注销"
                           - None：使用类默认值 DEFAULT_ACTION_TEXTS
        :param timeout: 超时时间（毫秒）
        """
        print(f"\n{'=' * 60}")
        print(f"开始查找邮箱 {email} 对应的行...")
        print(f"{'=' * 60}")

        # 步骤1：找到包含邮箱的行
        try:
            row = self._find_row_by_email(email, timeout=timeout)
            print(f"✅ 成功找到包含邮箱 {email} 的行")
        except Exception as e:
            print(f"❌ 查找行失败: {e}")
            raise

        # 滚动到可见位置
        row.scroll_into_view_if_needed()
        time.sleep(0.5)  # 等待滚动完成

        # 步骤2：处理 action_texts 参数
        if action_texts is None:
            action_texts = self.DEFAULT_ACTION_TEXTS
        elif isinstance(action_texts, str):
            if ',' in action_texts:
                action_texts = tuple(text.strip() for text in action_texts.split(',') if text.strip())
            else:
                action_texts = (action_texts,)
        elif isinstance(action_texts, list):
            action_texts = tuple(action_texts)
        elif not isinstance(action_texts, tuple):
            action_texts = (str(action_texts),)

        print(f"📋 尝试的按钮文本：{action_texts}")

        # 步骤3：打印当前行的所有文本（调试用）
        try:
            row_text = row.text_content()
            print(f"📄 找到的行内容（前300字符）：\n{row_text[:300]}")
            print(f"📏 行内容总长度：{len(row_text)} 字符")
        except Exception as e:
            print(f"⚠️ 无法获取行文本内容: {e}")

        # 步骤4：尝试查找行内的所有可点击元素（调试用）
        try:
            print(f"\n🔍 分析行内的所有可点击元素...")
            buttons = row.locator("button, a, [role='button'], .btn, [onclick]").all()
            print(f"   找到 {len(buttons)} 个可点击元素")
            for i, btn in enumerate(buttons[:5], 1):  # 只显示前5个
                try:
                    btn_text = btn.text_content().strip()
                    btn_tag = btn.evaluate("el => el.tagName")
                    print(f"   [{i}] {btn_tag}: '{btn_text}'")
                except:
                    print(f"   [{i}] 无法获取元素信息")
        except Exception as e:
            print(f"⚠️ 分析可点击元素失败: {e}")

        # 步骤5：尝试按文本查找按钮
        print(f"\n🎯 开始尝试点击按钮...")
        for idx, text in enumerate(action_texts, 1):
            print(f"\n   尝试 [{idx}/{len(action_texts)}]: '{text}'")

            # 尝试多种定位方式
            action_candidates = [
                ("文本模糊匹配", row.locator(f"text={text}").first),
                ("文本精确匹配", row.locator(f"text='{text}'").first),
                ("button元素+文本", row.locator("button").filter(has_text=text).first),
                ("a元素+文本", row.locator("a").filter(has_text=text).first),
                ("role=button+文本", row.locator("[role='button']").filter(has_text=text).first),
                ("包含文本的元素", row.locator(f":has-text('{text}')").first),
            ]

            for strategy_name, action in action_candidates:
                try:
                    # 检查元素是否存在
                    count = action.count()
                    if count == 0:
                        continue

                    print(f"      ✓ {strategy_name}: 找到 {count} 个元素")

                    # 等待元素可见（增加等待时间）
                    action.wait_for(state="visible", timeout=5000)

                    # 滚动到元素位置
                    action.scroll_into_view_if_needed()
                    time.sleep(0.5)  # 增加等待时间

                    # 检查元素是否可点击
                    is_visible = action.is_visible()
                    print(f"      ✓ 元素可见: {is_visible}")

                    # 尝试多种点击方式
                    # 方式1：普通点击
                    try:
                        print(f"      尝试 普通点击...")
                        action.click(timeout=5000)
                        print(f"      ✅ 成功点击！使用策略: {strategy_name}, 方法: 普通点击")
                        print(f"\n{'=' * 60}")
                        print(f"✅ 成功点击 {email} 行的 '{text}' 按钮")
                        print(f"{'=' * 60}\n")
                        return
                    except Exception as e:
                        print(f"      ✗ 普通点击 失败: {str(e)[:80]}")

                    # 方式2：强制点击
                    try:
                        print(f"      尝试 强制点击...")
                        action.click(force=True, timeout=5000)
                        print(f"      ✅ 成功点击！使用策略: {strategy_name}, 方法: 强制点击")
                        print(f"\n{'=' * 60}")
                        print(f"✅ 成功点击 {email} 行的 '{text}' 按钮")
                        print(f"{'=' * 60}\n")
                        return
                    except Exception as e:
                        print(f"      ✗ 强制点击 失败: {str(e)[:80]}")

                    # 方式3：JavaScript点击
                    try:
                        print(f"      尝试 JavaScript点击...")
                        action.evaluate("el => el.click()")
                        print(f"      ✅ 成功点击！使用策略: {strategy_name}, 方法: JavaScript点击")
                        print(f"\n{'=' * 60}")
                        print(f"✅ 成功点击 {email} 行的 '{text}' 按钮")
                        print(f"{'=' * 60}\n")
                        return
                    except Exception as e:
                        print(f"      ✗ JavaScript点击 失败: {str(e)[:80]}")

                    # 方式4：先hover再点击
                    try:
                        print(f"      尝试 先hover再点击...")
                        action.hover()
                        time.sleep(0.5)
                        action.click(timeout=5000)
                        print(f"      ✅ 成功点击！使用策略: {strategy_name}, 方法: 先hover再点击")
                        print(f"\n{'=' * 60}")
                        print(f"✅ 成功点击 {email} 行的 '{text}' 按钮")
                        print(f"{'=' * 60}\n")
                        return
                    except Exception as e:
                        print(f"      ✗ 先hover再点击 失败: {str(e)[:80]}")

                except Exception as e:
                    print(f"      ✗ {strategy_name}: {str(e)[:100]}")
                    continue

        # 步骤6：如果所有文本都失败，尝试点击行内的第一个按钮（备选方案）
        print(f"\n⚠️ 所有文本匹配都失败，尝试备选方案...")
        try:
            print("   查找行内的所有按钮...")
            buttons = row.locator("button, a[role='button'], .btn, [onclick], a").all()
            if buttons:
                print(f"   找到 {len(buttons)} 个按钮")
                for i, btn in enumerate(buttons[:3], 1):  # 尝试前3个
                    try:
                        btn_text = btn.text_content().strip()
                        print(f"   尝试点击第 {i} 个按钮: '{btn_text}'")
                        btn.scroll_into_view_if_needed()
                        btn.wait_for(state="visible", timeout=5000)
                        time.sleep(0.5)

                        # 尝试多种点击方式
                        # 方式1：普通点击
                        try:
                            print(f"     尝试 普通点击...")
                            btn.click(timeout=5000)
                            print(f"   ✅ 成功点击第 {i} 个按钮（普通点击）")
                            print(f"\n{'=' * 60}")
                            print(f"✅ 成功点击 {email} 行的按钮（备选方案）")
                            print(f"{'=' * 60}\n")
                            return
                        except Exception as e:
                            print(f"     ✗ 普通点击 失败: {str(e)[:80]}")

                        # 方式2：强制点击
                        try:
                            print(f"     尝试 强制点击...")
                            btn.click(force=True, timeout=5000)
                            print(f"   ✅ 成功点击第 {i} 个按钮（强制点击）")
                            print(f"\n{'=' * 60}")
                            print(f"✅ 成功点击 {email} 行的按钮（备选方案）")
                            print(f"{'=' * 60}\n")
                            return
                        except Exception as e:
                            print(f"     ✗ 强制点击 失败: {str(e)[:80]}")

                        # 方式3：JavaScript点击
                        try:
                            print(f"     尝试 JavaScript点击...")
                            btn.evaluate("el => el.click()")
                            print(f"   ✅ 成功点击第 {i} 个按钮（JavaScript点击）")
                            print(f"\n{'=' * 60}")
                            print(f"✅ 成功点击 {email} 行的按钮（备选方案）")
                            print(f"{'=' * 60}\n")
                            return
                        except Exception as e:
                            print(f"     ✗ JavaScript点击 失败: {str(e)[:80]}")

                        # 方式4：先hover再点击
                        try:
                            print(f"     尝试 先hover再点击...")
                            btn.hover()
                            time.sleep(0.5)
                            btn.click(timeout=5000)
                            print(f"   ✅ 成功点击第 {i} 个按钮（先hover再点击）")
                            print(f"\n{'=' * 60}")
                            print(f"✅ 成功点击 {email} 行的按钮（备选方案）")
                            print(f"{'=' * 60}\n")
                            return
                        except Exception as e:
                            print(f"     ✗ 先hover再点击 失败: {str(e)[:80]}")

                        print(f"   ✗ 第 {i} 个按钮所有点击方式都失败")
                    except Exception as e:
                        print(f"   ✗ 第 {i} 个按钮点击失败: {str(e)[:100]}")
                        continue
            else:
                print("   ❌ 未找到任何按钮")
        except Exception as e:
            print(f"   ❌ 备选方案失败: {e}")

        # 如果都失败了，抛出详细错误
        print(f"\n{'=' * 60}")
        print(f"❌ 所有尝试都失败")
        print(f"{'=' * 60}")
        raise Exception(
            f"未找到 {email} 行内的按钮。\n"
            f"尝试的文本：{action_texts}\n"
            f"请检查：\n"
            f"1. 按钮文本是否正确（注意大小写、空格）\n"
            f"2. 按钮是否在行内（可能在弹窗中）\n"
            f"3. 页面是否完全加载\n"
            f"4. 查看上面的调试信息"
        )

