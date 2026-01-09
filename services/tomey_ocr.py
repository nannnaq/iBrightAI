import pygetwindow as gw
import pyautogui
import cv2
import numpy as np
import pytesseract
import re
import time
import os
from django.conf import settings
import sys

# ============================================================
# 🎯 动态获取 Tesseract 路径 (兼容开发和打包环境)
# ============================================================
def get_tesseract_cmd():
    """
    根据运行环境动态计算 tesseract.exe 的路径。
    如果找不到，直接抛出异常。
    """
    # 1. 确定基准目录
    if getattr(sys, 'frozen', False):
        # 【打包环境】 EXE 所在目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 【开发环境】 项目根目录 (假设 services 在根目录下)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 2. 定义查找清单 (优先级从高到低)
    potential_paths = [
        # 优先级 1: 打包后的标准路径 (EXE同级/bin/Tesseract-OCR)
        os.path.join('bin', 'Tesseract-OCR', 'tesseract.exe'),
        
        # 优先级 2: 你本机的特殊开发路径 (根目录/bin/bin/Tesseract-OCR)
        os.path.join('bin', 'bin', 'Tesseract-OCR', 'tesseract.exe'),
        
        # 优先级 3: 标准开发路径 (根目录/bin/Tesseract-OCR)
        os.path.join('bin', 'Tesseract-OCR', 'tesseract.exe'),
    ]

    # 3. 遍历查找
    for rel_path in potential_paths:
        full_path = os.path.join(base_path, rel_path)
        if os.path.exists(full_path):
            print(f" 成功定位 OCR 引擎: {full_path}")
            return full_path

    # 4.  如果都找不到，直接报错，不瞎猜
    raise FileNotFoundError(
        f"严重错误：在以下路径中均未找到 Tesseract-OCR 引擎，请检查 bin 文件夹是否完整打包。\n"
        f"搜索基准路径: {base_path}\n"
        f"尝试过的相对路径: {potential_paths}"
    )

# 全局初始化路径
try:
    tesseract_cmd_path = get_tesseract_cmd()
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
    OCR_READY = True
except FileNotFoundError as e:
    print(e)
    OCR_READY = False
    OCR_ERROR_MSG = str(e)

# 获取并设置路径
cmd_path = get_tesseract_cmd()
print(f"OCR 引擎路径: {cmd_path}") # 调试打印

if not os.path.exists(cmd_path):
    print(f" 严重错误: 找不到 OCR 引擎，请检查 bin 文件夹结构")
else:
    pytesseract.pytesseract.tesseract_cmd = cmd_path

# ============================================================

class TomeyOCR:
    def __init__(self):
        self.window_title = "Single Map" 

    def find_and_capture(self):
        try:
            # 1. 查找并激活窗口
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                return {'success': False, 'error': '未找到 Single Map 窗口'}
            
            window = windows[0]
            if window.isMinimized: window.restore()
            try:
                window.activate()
                time.sleep(0.2)
            except: pass

            # ============================================================
            # 2. 🎯 关键参数：截图区域微调 (针对你的截图进行的优化)
            # ============================================================
            
            # 宽度缩小：避开右侧的色阶条 (原250 -> 150)
            roi_w = 80 
            
            # 高度减小：只截一行字的高度 (原60 -> 30)
            roi_h = 20 
            # 调整左右 (负数表示向左移，正数表示向右移)
            # 比如现在觉得太靠右了，就多减一点
            left_offset = -150 
            left = window.left + window.width - roi_w + left_offset

            # 调整上下
            # 比如现在觉得太靠上了，截到了上面的字，就加大这个数
            top_offset = 50 
            top = window.top + top_offset

            # 3. 截图
            screenshot = pyautogui.screenshot(region=(left, top, roi_w, roi_h))
            
            # 保存调试图片 (每次必看这个图片，确认是否只有 "101.TMS" 纯净文字)
            debug_path = os.path.join(settings.BASE_DIR, 'ocr_debug.png')
            screenshot.save(debug_path)
            print(f"调试截图已保存至: {debug_path}")

            # 4. 图像处理 (放大 + 二值化)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # [新增] 放大图片 3 倍，极大提高识别率
            img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 反转颜色：黑底白字 -> 白底黑字
            inverted = cv2.bitwise_not(gray)
            
            # 二值化：使用 OTSU 自动寻找最佳阈值
            _, binary = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 5. 识别 (添加白名单)
            # --psm 7: 单行模式
            # -c tessedit_char_whitelist: 只允许识别字母、数字、点、下划线、横杠
            custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ._-'
            
            text = pytesseract.image_to_string(binary, config=custom_config)
            clean_text = text.strip()
            print(f"OCR 原始识别结果: [{clean_text}]")

            # 6. 正则提取 .TMS 文件名
            match = re.search(r'([a-zA-Z0-9_-]+\.TMS)', clean_text, re.IGNORECASE)
            
            if match:
                filename = match.group(1)
                return {'success': True, 'filename': filename}
            else:
                # 如果正则没匹配到，但在白名单模式下，OCR结果很可能就是文件名
                # 只要它以 .TMS 结尾
                if clean_text.upper().endswith('.TMS'):
                     return {'success': True, 'filename': clean_text}
                     
                return {'success': False, 'error': f'未识别到有效文件名，结果: {clean_text}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    if not settings.configured:
        settings.configure(BASE_DIR=os.path.dirname(os.path.abspath(__file__)))
    ocr = TomeyOCR()
    print(ocr.find_and_capture())