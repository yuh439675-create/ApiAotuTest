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
        book_id = 31000972291

        # 使用你的token
        token = "ZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnlaV2RwYzNSbGNsUjVjR1VpT2lKUVJWSk5RVTVGVGxRaUxDSjFjMlZ5U1dRaU9qRTJPVFUyTnpnME5YMC5JelZBSEhPZjBjMDFtUDE3QXlrR1pRMFJRaVQ1UmFpS3JHLUZUUlhrRWdz"

        if self.is_book_downloaded(book_id):
            print(f"已下载过 {book_id}，跳过")
            return

        heads = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-type': 'application/json;charset=UTF-8',
            'token': token
        }

        book_data = {"bookId": book_id}
        book_response = requests.post('https://www.goodshort.com/hwycreels/book/detail', json=book_data, headers=heads)
        book_info_data = book_response.json()

        print(f"书籍详情响应: {book_info_data}")

        if book_info_data.get('status') != 0:
            print(f"获取书籍信息失败: {book_info_data.get('message')}")
            return

        book_info = book_info_data['data']['book']
        book_details = {
            'book_id': book_info['bookId'],
            'book_name': book_info['bookName'],
            'total_chapters': book_info['chapterCount'],
            'cover_url': book_info.get('cover') or book_info.get('cover2'),
            'author': book_info.get('pseudonym', ''),
        }

        safe_book_name = "".join(c for c in book_details['book_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        base_dir = os.path.join(Config.util_path, 'Good_short平台的爬剧加去水印/放剧/')
        output_dir = os.path.join(base_dir, safe_book_name)
        os.makedirs(output_dir, exist_ok=True)

        # 获取所有章节
        all_chapters_data = self.get_all_chapters_direct(book_id, heads)
        print(f"获取到 {len(all_chapters_data)} 集数据")

        # 显示章节价格信息
        free_count = len([ch for ch in all_chapters_data if ch.get('price', 0) == 0])
        paid_count = len([ch for ch in all_chapters_data if ch.get('price', 0) > 0])
        print(f"免费集数: {free_count}, 付费集数: {paid_count}")

        downloadable_chapters = []
        for chapter in all_chapters_data:
            m3u8_url = self.get_chapter_m3u8_with_token(book_id, chapter['id'], heads)
            if m3u8_url:
                chapter['m3u8Path'] = m3u8_url
                downloadable_chapters.append(chapter)
                price_info = "免费" if chapter.get('price', 0) == 0 else f"付费({chapter.get('price', 0)})"
                print(f"✅ 第{chapter['chapterName']}集 {price_info} - 获取成功")
            else:
                print(f"❌ 第{chapter['chapterName']}集 - 获取失败")

        if downloadable_chapters:
            success_count = self.download_all_chapters(downloadable_chapters, output_dir)
            print(f"下载完成: {success_count}/{len(downloadable_chapters)} 集成功")
            self.record_downloaded_book(book_id, book_details, output_dir, len(downloadable_chapters))
        else:
            print("❌ 没有可下载的章节")

    def get_all_chapters_direct(self, book_id, headers):
        """直接获取所有章节数据"""
        data = {
            "bookId": str(book_id),
            "current": 1,
            "size": 500
        }

        try:
            response = requests.post('https://www.goodshort.com/hwycreels/book/chapter/records',
                                     json=data, headers=headers, timeout=10)
            print(f"章节记录API响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"章节记录API数据: {result}")

                if result.get('status') == 0 and 'records' in result['data']:
                    chapters = result['data']['records']
                    print(f"成功获取 {len(chapters)} 集章节数据")
                    return chapters
                else:
                    print(f"API返回错误: {result.get('message')}")
        except Exception as e:
            print(f"获取章节记录失败: {e}")

        return []

    def get_chapter_m3u8_with_token(self, book_id, chapter_id, headers):
        """使用token获取章节m3u8链接"""
        # 方法1: 章节详情API
        detail_data = {
            "bookId": str(book_id),
            "chapterId": chapter_id
        }

        try:
            response = requests.post('https://www.goodshort.com/hwycreels/book/chapter/detail',
                                     json=detail_data, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 0 and 'data' in data:
                    m3u8 = data['data'].get('m3u8Path')
                    if m3u8:
                        return m3u8
                    else:
                        print(f"章节 {chapter_id} 无m3u8Path字段")
                else:
                    print(f"详情API错误: {data.get('message')}")
        except Exception as e:
            print(f"详情API请求失败: {e}")

        # 方法2: 播放API
        play_data = {
            "bookId": str(book_id),
            "chapterId": chapter_id
        }

        try:
            response = requests.post('https://www.goodshort.com/hwycreels/book/chapter/play',
                                     json=play_data, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"播放API响应: {data}")
                if data.get('status') == 0 and 'data' in data:
                    return data['data'].get('m3u8Path')
                else:
                    print(f"播放API错误: {data.get('message')}")
        except Exception as e:
            print(f"播放API请求失败: {e}")

        return None

    def download_all_chapters(self, chapters, output_dir):
        if not self.check_ffmpeg():
            return 0

        def safe_chapter_sort(chapter):
            try:
                return int(chapter['chapterName'])
            except:
                return chapter['chapterName']

        sorted_chapters = sorted(chapters, key=safe_chapter_sort)
        success_count = 0

        print(f"开始下载 {len(sorted_chapters)} 集视频...")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            for index, chapter in enumerate(sorted_chapters, 1):
                future = executor.submit(self.download_single_chapter, chapter, output_dir, index)
                futures[future] = chapter['chapterName']

            completed = 0
            for future in as_completed(futures):
                chapter_name = futures[future]
                completed += 1
                try:
                    success, msg = future.result()
                    if success:
                        success_count += 1
                        print(f"✅ [{completed}/{len(chapters)}] 第{chapter_name}集: {msg}")
                    else:
                        print(f"❌ [{completed}/{len(chapters)}] 第{chapter_name}集: {msg}")
                except Exception as e:
                    print(f"💥 [{completed}/{len(chapters)}] 第{chapter_name}集: 异常 - {e}")

        return success_count

    def download_single_chapter(self, chapter_data, output_dir, episode_number):
        m3u8_url = chapter_data.get('m3u8Path')
        if not m3u8_url:
            return False, "无视频链接"

        output_filename = os.path.join(output_dir, f"{episode_number}.mp4")
        if os.path.exists(output_filename):
            return True, "文件已存在"

        try:
            cmd = [
                'ffmpeg',
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
                '-i', m3u8_url,
                '-c', 'copy',
                '-y',
                '-hide_banner',
                '-loglevel', 'error',
                output_filename
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                return True, "下载成功"
            return False, f"FFmpeg错误: {result.stderr[:100]}"
        except subprocess.TimeoutExpired:
            return False, "下载超时"
        except Exception as e:
            return False, f"下载异常: {str(e)}"

    def is_book_downloaded(self, book_id):
        try:
            record_file = os.path.join(Config.util_path, 'Good_short平台的爬剧加去水印/', 'downloaded_books.json')
            if not os.path.exists(record_file):
                return False
            with open(record_file, 'r', encoding='utf-8') as f:
                downloaded_books = json.load(f)
            return str(book_id) in downloaded_books
        except:
            return False

    def record_downloaded_book(self, book_id, book_details, output_dir, downloaded_count):
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
                'download_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(downloaded_books, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"记录下载信息失败: {e}")

    def check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
            return True
        except:
            print("未找到ffmpeg")
            return False


if __name__ == "__main__":
    test = TestAddUser()
    test.test_pt_short()