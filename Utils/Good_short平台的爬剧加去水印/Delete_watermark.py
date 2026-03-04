import cv2
import numpy as np
import time
import os


# 最简单的版本 - 直接在这里改数字
def simple_watermark_removal():
    input_video = "/Users/macbook/Desktop/管理2/output.mp4"
    output_video = "/Users/macbook/Desktop/管理2/output_no_watermark_simple.mp4"

    # ====== 在这里调整这4个数字 ======
    x = 60  # 左边距
    y = 80  # 上边距
    w = 90  # 宽度
    h = 90  # 高度
    # ==============================

    print(f"使用区域: x={x}, y={y}, w={w}, h={h}")

    cap = cv2.VideoCapture(input_video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # 创建预览图
    ret, frame = cap.read()
    if ret:
        preview = frame.copy()
        cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imwrite("/Users/macbook/Desktop/管理2/simple_preview.jpg", preview)
        print("预览图已生成: simple_preview.jpg")

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 回到视频开头

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 创建掩码
        mask = np.zeros((height, width), np.uint8)
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(width, x1 + w), min(height, y1 + h)
        mask[y1:y2, x1:x2] = 255

        # 修复水印
        inpainted = cv2.inpaint(frame, mask, 12, cv2.INPAINT_NS)
        out.write(inpainted)

        if frame_count % 30 == 0:
            progress = frame_count / total_frames * 100
            print(f"进度: {frame_count}/{total_frames} ({progress:.1f}%)")

    cap.release()
    out.release()
    print(f"完成! 输出文件: {output_video}")


if __name__ == "__main__":
    simple_watermark_removal()