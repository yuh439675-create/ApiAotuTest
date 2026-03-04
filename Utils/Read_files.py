import os
import platform
import re


def natural_sort_key(s):
    """自然排序的键函数"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def get_media_files(folder_path, cover_formats, video_formats):
    """
    获取指定文件夹中查找封面图片和视频文件

    Args:
        folder_path: 文件夹路径
        cover_formats: 封面文件格式列表或字符串
        video_formats: 视频文件格式列表或字符串

    Returns:
        dict: 包含封面信息和视频列表的字典
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return {"封面": None, "视频列表": []}

    # 检查是否是文件夹
    if not os.path.isdir(folder_path):
        print(f"错误：'{folder_path}' 不是一个有效的文件夹")
        return {"封面": None, "视频列表": []}

    # 确保格式参数是列表类型
    if isinstance(cover_formats, str):
        cover_formats = [cover_formats.lower()]
    else:
        cover_formats = [fmt.lower() for fmt in cover_formats]
        
    if isinstance(video_formats, str):
        video_formats = [video_formats.lower()]
    else:
        video_formats = [fmt.lower() for fmt in video_formats]

    # 预编译文件扩展名模式以提高性能
    cover_exts = {f".{fmt}" for fmt in cover_formats}
    video_exts = {f".{fmt}" for fmt in video_formats}

    cover_info = None
    video_list = []

    try:
        # 使用更高效的方式遍历文件
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            # 只处理文件，跳过子文件夹
            if os.path.isfile(file_path):
                # 转换为小写以进行比较
                lower_filename = filename.lower()
                
                # 检查是否为封面文件
                if any(lower_filename.endswith(ext) for ext in cover_exts):
                    file_size = os.path.getsize(file_path)  # 只计算一次文件大小
                    size_mb = round(file_size / (1024 * 1024), 2)
                    cover_info = {
                        "文件名": filename,
                        "大小": f"{size_mb}MB",
                        "路径": file_path
                    }
                # 检查是否为视频文件
                elif any(lower_filename.endswith(ext) for ext in video_exts):
                    try:
                        file_size = os.path.getsize(file_path)
                        size_mb = round(file_size / (1024 * 1024), 2)
                        video_list.append({
                            "文件名": filename,
                            "大小": f"{size_mb}MB",
                            "路径": file_path
                        })
                    except OSError as e:
                        print(f"警告：无法获取文件 '{filename}' 的大小 - {e}")
    except PermissionError:
        print(f"错误：没有访问文件夹 '{folder_path}' 的权限")
        return {"封面": None, "视频列表": []}
    except OSError as e:
        print(f"处理文件夹时发生错误：{e}")
        return {"封面": None, "视频列表": []}

    # 按视频文件名自然排序
    video_list.sort(key=lambda x: natural_sort_key(x["文件名"]))

    return {
        "封面": cover_info,
        "视频列表": video_list
    }


if __name__ == '__main__':
    # 调用示例
    result = get_media_files(
        r'/Users/macbook/Desktop/测试存剧/LET IT BE ME',
        ['jpg', 'png'],  # 封面格式
        ['mp4', 'avi']  # 视频格式
    )
    print('看看这个数量：', len(result['视频列表']))

    print("封面信息：")
    if result["封面"]:
        system_name = platform.system()
        if system_name == 'Windows':
            cover_sys = str(result["封面"]['路径']).split(r'\'')[0].split('\\')[-2]
            print(cover_sys)
        elif system_name == 'Darwin':
            cover_sys = str(result["封面"]['路径']).split('/')[-2]
            print(cover_sys)
    else:
        print("未找到封面文件")

    print("\n视频列表（按文件名自然排序）：")
    if result["视频列表"]:
        for idx, video in enumerate(result["视频列表"], 1):
            # system_name = platform.system()
            # if system_name == 'Windows':
            #     short_sys = str(video['路径']).split(r'\'')[0].split('\\')[-2]
            #     print(short_sys)
            # elif system_name == 'Darwin':
            #     short_sys = str(video['路径']).split('/')[-2]
            #     print(short_sys)
            print(idx, video)


    else:
        print("未找到视频文件")




