import allure
import requests
import os
import subprocess
import time
import json
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from Config.config import Config


class TestAddUser:
    def test_pt_short(self):
        with allure.step('获取短剧信息并下载所有集数'):
            token_data = '421fe9ceaab7482a179fe3104c8601a5'
            book_id = 31000972291

            # 首先检查是否已经下载过
            if self.is_book_downloaded(book_id):
                print(f"⏭️  剧集 {book_id} 已下载过，跳过")
                return

            # 配置请求头
            heads = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Content-type': 'application/json;charset=UTF-8',
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://www.goodshort.com/'
            }

            # 步骤1: 获取书籍基本信息
            with allure.step('获取书籍基本信息'):
                book_data = {
                    "bookId": book_id
                }
                book_response = requests.post('https://www.goodshort.com/hwycreels/book/detail',
                                              json=book_data, headers=heads)
                book_info_data = book_response.json()

                print(f"📊 书籍API响应状态: {book_info_data.get('status')}")
                print(f"📊 书籍API响应消息: {book_info_data.get('message')}")

                if book_info_data.get('status') != 0:
                    print(f"❌ 获取书籍信息失败: {book_info_data.get('message')}")
                    return

                book_info = book_info_data['data']['book']
                book_details = {
                    'book_id': book_info['bookId'],
                    'book_name': book_info['bookName'],
                    'introduction': book_info.get('introduction', ''),
                    'total_chapters': book_info['chapterCount'],
                    'cover_url': book_info.get('cover') or book_info.get('cover2'),
                    'author': book_info.get('pseudonym', ''),
                    'language': book_info.get('language', ''),
                    'view_count': book_info.get('viewCount', 0),
                    'praise_count': book_info.get('praiseCount', 0),
                    'labels': book_info.get('typeTwoNames', []),
                    'status': book_info.get('writeStatusDisplay', ''),
                    'view_count_display': book_info.get('viewCountDisplay', ''),
                    'free': book_info.get('free', 2),
                    'write_status': book_info.get('writeStatus', ''),
                    'contract_status': book_info.get('contractStatus', ''),
                    'book_status': book_info.get('status', '')
                }

                print("🎬 剧集详细信息:")
                print(f"   📚 标题: {book_details['book_name']}")
                print(f"   📖 介绍: {book_details['introduction']}")
                print(f"   👤 作者: {book_details['author']}")
                print(f"   🌐 语言: {book_details['language']}")
                print(f"   📊 总集数: {book_details['total_chapters']}")

            # 步骤2: 创建输出目录
            with allure.step('创建输出目录'):
                safe_book_name = "".join(
                    c for c in book_details['book_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                base_dir = os.path.join(Config.util_path, 'Good_short平台的爬剧加去水印/放剧/')
                output_dir = os.path.join(base_dir, safe_book_name)
                os.makedirs(output_dir, exist_ok=True)
                print(f"📁 输出目录: {output_dir}")

            # 步骤3: 尝试多种方式获取章节信息
            with allure.step('获取章节信息'):
                all_chapters_data = []

                # 方法1: 先检查书籍详情API是否包含章节列表
                if 'chapterVoList' in book_info_data['data']:
                    chapters_from_book = book_info_data['data']['chapterVoList']
                    print(f"📄 从书籍API获取到 {len(chapters_from_book)} 集数据")
                    all_chapters_data.extend(chapters_from_book)

                # 方法2: 如果章节列表不完整，使用章节详情API补充
                if len(all_chapters_data) < book_details['total_chapters']:
                    print("🔄 使用章节详情API补充数据...")
                    additional_chapters = self.get_all_chapters_sequentially(book_id, book_details['total_chapters'],
                                                                             heads)
                    all_chapters_data.extend(additional_chapters)

                print(f"✅ 总共获取 {len(all_chapters_data)} 集数据")

            # 如果没有获取到任何章节，尝试备用方案
            if not all_chapters_data:
                print("🔄 尝试备用方案获取章节...")
                all_chapters_data = self.get_chapters_fallback(book_id, book_details['total_chapters'], heads)

            # 步骤4: 分析价格信息
            with allure.step('分析价格信息'):
                free_chapters = []
                paid_chapters = []
                total_price = 0
                per_episode_price = 0

                for chapter in all_chapters_data:
                    chapter_price = chapter.get('price', 0)
                    if chapter.get('m3u8Path'):  # 只要有m3u8链接就处理
                        if chapter_price == 0:
                            free_chapters.append(chapter)
                        else:
                            paid_chapters.append(chapter)
                            total_price += chapter_price
                            if chapter_price > 0:
                                per_episode_price = chapter_price

                print(f"💰 免费集数: {len(free_chapters)}")
                print(f"💵 付费集数: {len(paid_chapters)}")
                print(f"💳 总价格: {total_price}")
                print(f"🎫 每集价格: {per_episode_price}")

                # 更新书籍价格信息
                book_details['price'] = total_price
                book_details['per_episode_price'] = per_episode_price
                book_details['free_chapters'] = len(free_chapters)
                book_details['paid_chapters'] = len(paid_chapters)

                if not free_chapters and not paid_chapters:
                    print("❌ 没有找到任何可下载的集数")
                    return

            # 步骤5: 保存书籍信息到YAML文件
            with allure.step('保存书籍信息'):
                self.save_book_info_to_yaml(book_details, output_dir)

            # 步骤6: 下载封面
            with allure.step('下载封面'):
                if book_details['cover_url']:
                    cover_success = self.download_cover(book_details['cover_url'], output_dir)
                    if cover_success:
                        print("✅ 封面下载成功")
                    else:
                        print("❌ 封面下载失败")
                else:
                    print("⚠️ 未找到封面URL")

            # 步骤7: 下载所有免费集数并重命名
            with allure.step('下载视频集数'):
                if free_chapters:
                    success_count = self.download_all_chapters(free_chapters, output_dir)
                    print(f"🎉 免费集下载完成: {success_count}/{len(free_chapters)} 集成功")
                else:
                    print("ℹ️  没有免费集可下载")

            # 步骤8: 记录已下载的剧集
            if free_chapters:
                self.record_downloaded_book(book_id, book_details, output_dir, len(free_chapters))

    def is_book_downloaded(self, book_id):
        """检查剧集是否已经下载过"""
        try:
            record_file = os.path.join(Config.util_path, 'Good_short平台的爬剧加去水印/', 'downloaded_books.json')

            if not os.path.exists(record_file):
                return False

            with open(record_file, 'r', encoding='utf-8') as f:
                downloaded_books = json.load(f)

            return str(book_id) in downloaded_books

        except Exception as e:
            print(f"❌ 检查下载记录时出错: {e}")
            return False

    def get_all_chapters_sequentially(self, book_id, total_chapters, headers):
        """通过章节详情API顺序获取所有章节"""
        all_chapters = []

        print(f"🔍 开始顺序获取 {total_chapters} 集数据...")

        # 首先获取第1集
        first_chapter = self.get_chapter_detail(book_id, None, headers)
        if first_chapter:
            all_chapters.append(first_chapter)
            current_chapter_id = first_chapter.get('nextChapterId')
            print(f"✅ 已获取第 1/{total_chapters} 集 - ID: {first_chapter.get('id')}")
        else:
            print("❌ 无法获取第1集")
            return all_chapters

        # 通过next指针顺序获取后续章节
        chapter_count = 1
        while current_chapter_id and current_chapter_id != 0 and chapter_count < total_chapters:
            try:
                chapter_data = self.get_chapter_detail(book_id, current_chapter_id, headers)
                if chapter_data:
                    all_chapters.append(chapter_data)
                    current_chapter_id = chapter_data.get('nextChapterId')
                    chapter_count += 1
                    print(f"✅ 已获取第 {chapter_count}/{total_chapters} 集 - ID: {chapter_data.get('id')}")
                else:
                    print(f"❌ 无法获取第 {chapter_count + 1} 集")
                    break

                # 添加延迟避免请求过快
                time.sleep(0.5)

            except Exception as e:
                print(f"💥 获取章节时出错: {e}")
                break

        return all_chapters

    def get_chapter_detail(self, book_id, chapter_id, headers):
        """获取章节详情"""
        try:
            if chapter_id is None:
                # 获取第一集 - 尝试不同的参数格式
                chapter_data = {
                    "bookId": str(book_id)
                    # 第一集可能不需要chapterId参数
                }
            else:
                # 获取指定章节
                chapter_data = {
                    "bookId": str(book_id),
                    "chapterId": chapter_id
                }

            print(f"🔗 请求章节详情: bookId={book_id}, chapterId={chapter_id}")

            response = requests.post('https://www.goodshort.com/hwycreels/book/chapter/detail',
                                     json=chapter_data, headers=headers, timeout=10)

            print(f"📡 章节API响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📡 章节API响应状态: {data.get('status')}")
                print(f"📡 章节API响应消息: {data.get('message')}")

                if data.get('status') == 0:
                    chapter_info = data['data']
                    print(
                        f"📹 获取到章节: {chapter_info.get('chapterName')}, m3u8Path: {'有' if chapter_info.get('m3u8Path') else '无'}")
                    return chapter_info
                else:
                    print(f"❌ 章节API返回错误: {data.get('message')}")
            else:
                print(f"❌ 章节API请求失败: {response.status_code}")

            return None

        except Exception as e:
            print(f"💥 获取章节详情时出错: {e}")
            return None

    def get_chapters_fallback(self, book_id, total_chapters, headers):
        """备用方案：尝试通过章节列表API获取"""
        all_chapters = []
        print("🔄 尝试备用方案获取章节列表...")

        try:
            # 尝试获取章节列表
            list_data = {
                "bookId": str(book_id),
                "pageNum": 1,
                "pageSize": total_chapters
            }

            response = requests.post('https://www.goodshort.com/hwycreels/book/chapter/list',
                                     json=list_data, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 0 and 'list' in data['data']:
                    chapters = data['data']['list']
                    print(f"✅ 从章节列表API获取到 {len(chapters)} 集数据")
                    return chapters

        except Exception as e:
            print(f"💥 备用方案获取失败: {e}")

        return all_chapters

    def save_book_info_to_yaml(self, book_details, output_dir):
        """保存书籍信息到YAML文件"""
        try:
            yaml_data = {
                '短剧路径': output_dir.replace('/', '\\\\'),
                '语言': self.get_language_display(book_details['language']),
                '点赞量': book_details['praise_count'],
                '整剧价格': book_details['price'],
                '每集价格': book_details['per_episode_price'],
                '是否完结': '是' if book_details['write_status'] == 'COMPLETE' else '否',
                '是否收费': '是' if book_details['price'] > 0 else '否',
                '是否上架': '是' if book_details['book_status'] == 'PUBLISHED' else '否',
                '封面标签': ', '.join(book_details['labels']),
                '封面介绍': book_details['introduction']
            }

            yaml_file = os.path.join(output_dir, "书籍信息.yaml")
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, indent=2)

            print(f"📄 书籍信息已保存到: {yaml_file}")

        except Exception as e:
            print(f"❌ 保存书籍信息时出错: {e}")

    def get_language_display(self, language_code):
        """将语言代码转换为中文显示"""
        language_map = {
            'ENGLISH': '英语',
            'CHINESE': '中文',
            'SPANISH': '西班牙语',
            'FRENCH': '法语',
            'GERMAN': '德语',
            'JAPANESE': '日语',
            'KOREAN': '韩语',
            'PORTUGUESE': '葡萄牙语',
            'RUSSIAN': '俄语',
            'ARABIC': '阿拉伯语',
            'HINDI': '印地语',
            'INDONESIAN': '印度尼西亚语',
            'THAI': '泰语',
            'VIETNAMESE': '越南语',
            'ITALIAN': '意大利语'
        }
        return language_map.get(language_code, language_code)

    def record_downloaded_book(self, book_id, book_details, output_dir, downloaded_count):
        """记录已下载的剧集"""
        try:
            base_dir = os.path.join(Config.util_path, 'Good_short平台的爬剧加去水印/')
            record_file = os.path.join(base_dir, 'downloaded_books.json')

            os.makedirs(base_dir, exist_ok=True)

            downloaded_books = {}
            if os.path.exists(record_file):
                with open(record_file, 'r', encoding='utf-8') as f:
                    downloaded_books = json.load(f)

            downloaded_books[str(book_id)] = {
                'name': book_details['book_name'],
                'path': output_dir,
                'language': self.get_language_display(book_details['language']),
                'total_price': book_details['price'],
                'per_episode_price': book_details['per_episode_price'],
                'downloaded_count': downloaded_count,
                'download_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(downloaded_books, f, ensure_ascii=False, indent=2)

            print(f"📝 已记录下载信息: {book_details['book_name']} (ID: {book_id})")

        except Exception as e:
            print(f"❌ 记录下载信息时出错: {e}")

    def download_cover(self, cover_url, output_dir):
        """下载封面图片"""
        try:
            # 处理双URL情况（有些cover2字段包含重复的URL）
            if cover_url.startswith('https://acf.goodshort.com/https://'):
                cover_url = cover_url.replace('https://acf.goodshort.com/https://', 'https://')

            response = requests.get(cover_url, timeout=10)
            if response.status_code == 200:
                # 判断图片格式
                if cover_url.lower().endswith('.png'):
                    cover_filename = os.path.join(output_dir, "0.png")
                else:
                    cover_filename = os.path.join(output_dir, "0.jpg")

                with open(cover_filename, 'wb') as f:
                    f.write(response.content)

                print(f"🖼️ 封面已保存为: {cover_filename}")
                return True
            else:
                print(f"❌ 封面下载失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 封面下载异常: {e}")
            return False

    def download_all_chapters(self, chapters, output_dir):
        """下载所有章节"""
        if not self.check_ffmpeg():
            return 0

        success_count = 0

        print(f"\n🎬 开始下载 {len(chapters)} 集视频...")
        print("=" * 50)

        # 按章节名称排序，确保顺序正确
        sorted_chapters = sorted(chapters, key=lambda x: int(x['chapterName']))

        # 使用多线程下载（最多同时下载2个）
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            for index, chapter in enumerate(sorted_chapters, 1):
                future = executor.submit(self.download_single_chapter, chapter, output_dir, index)
                futures[future] = chapter['chapterName']

            for future in as_completed(futures):
                chapter_name = futures[future]
                try:
                    success, result_msg = future.result()
                    if success:
                        success_count += 1
                        print(f"✅ {chapter_name}: {result_msg}")
                    else:
                        print(f"❌ {chapter_name}: {result_msg}")
                except Exception as e:
                    print(f"💥 {chapter_name}: 下载异常 - {e}")

                # 添加延迟避免请求过快
                time.sleep(1)

        return success_count

    def download_single_chapter(self, chapter_data, output_dir, episode_number):
        """下载单个章节"""
        chapter_name = chapter_data['chapterName']
        m3u8_url = chapter_data['m3u8Path']

        # 使用数字命名：1.mp4, 2.mp4, 3.mp4...
        output_filename = os.path.join(output_dir, f"{episode_number}.mp4")

        # 检查文件是否已存在
        if os.path.exists(output_filename):
            return True, f"文件已存在，跳过下载 ({episode_number}.mp4)"

        try:
            # 使用ffmpeg下载m3u8
            cmd = [
                'ffmpeg',
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
                '-i', m3u8_url,
                '-c', 'copy',
                '-y',  # 覆盖已存在文件
                '-hide_banner',
                '-loglevel', 'error',  # 减少日志输出
                output_filename
            ]

            # 执行下载命令，设置超时时间10分钟
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                # 检查文件是否成功创建
                if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                    return True, f"下载成功 ({episode_number}.mp4)"
                else:
                    return False, f"文件创建失败 ({episode_number}.mp4)"
            else:
                error_msg = result.stderr[:200] if result.stderr else "未知错误"
                return False, f"FFmpeg错误: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, f"下载超时 ({episode_number}.mp4)"
        except Exception as e:
            return False, f"下载异常: {str(e)} ({episode_number}.mp4)"

    def check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
            return True
        except:
            print("❌ 错误: 未找到ffmpeg，请先安装ffmpeg")
            print("💡 安装方法: brew install ffmpeg 或从官网下载")
            return False


# 如果直接运行此脚本
if __name__ == "__main__":
    test = TestAddUser()
    test.test_pt_short()