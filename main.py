import os
import sys
import time
import threading
import logging
import shutil
import multiprocessing
import ctypes
import socket
import stat  # 导入 stat 模块用于修改文件权限
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# --- 关键库 ---
from filelock import Timeout, FileLock
import pygetwindow as gw

# ==========================================================
# =============  1. 全局配置 & 路径统一管理   ===============
# ==========================================================

# 1. 修改：文件夹重命名为 'iBrightAiData'
LOCAL_DATA_DIR = os.path.join(os.path.expanduser('~'), 'iBrightAiData')
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

# 配置文件 & 日志文件路径
CONFIG_FILE_PATH = os.path.join(LOCAL_DATA_DIR, 'config.json')
LOG_FILE_PATH = os.path.join(LOCAL_DATA_DIR, 'app.log')

# 环境变量
os.environ['DATABASE_PATH'] = os.path.join(LOCAL_DATA_DIR, 'db.sqlite3')
os.environ['MEDIA_ROOT'] = os.path.join(LOCAL_DATA_DIR, 'media')
os.environ['STATIC_ROOT'] = os.path.join(LOCAL_DATA_DIR, 'static')
os.environ['CONFIG_PATH'] = CONFIG_FILE_PATH

APP_WIDTH = 1200
APP_HEIGHT = 800
WINDOW_TITLE = '普诺瞳 AI'
SERVER_PORT = 8000
SERVER_HOST = '127.0.0.1'

window = None

# --- 关键类：重定向 Print 到 Log ---
class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message.strip() != "":
            self.level(message.strip())

    def flush(self):
        pass

# 配置日志 (输出到文件)
# logging.basicConfig(
#     filename=LOG_FILE_PATH,
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     encoding='utf-8'
# )
# --- 修改后的代码 (支持同时输出到屏幕和文件) ---
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
# 使用 sys.__stdout__ 确保直接输出到原始控制台，防止递归调用
console_handler = logging.StreamHandler(sys.__stdout__) 

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler] # 同时启用两个处理器
)
# ==========================================================
# =============    2. 启动画面 & 资源工具     ===============
# ==========================================================

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        if not os.path.exists(os.path.join(base_path, relative_path)):
            base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def show_splash_screen(image_path, app_width, app_height):
    try:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        root = tk.Tk()
        
        try:
            dpi_scale = root.winfo_fpixels('1i') / 96.0
        except Exception:
            dpi_scale = 1.0
            
        real_w = int(app_width * dpi_scale)
        real_h = int(app_height * dpi_scale)

        root.overrideredirect(True)
        root.attributes('-topmost', False)
        root.lower()
        root.configure(bg='black')

        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x_pos = (screen_w - real_w) // 2
        y_pos = (screen_h - real_h) // 2

        root.geometry(f"{real_w}x{real_h}+{x_pos}+{y_pos}")

        if not os.path.exists(image_path):
            label = tk.Label(root, text="正在启动...", font=("Arial", 16), padx=50, pady=50)
            label.pack()
        else:
            pil_image = Image.open(image_path)
            zoom_factor = 1.03 
            zoomed_w = int(real_w * zoom_factor)
            zoomed_h = int(real_h * zoom_factor)
            pil_image = pil_image.resize((zoomed_w, zoomed_h), Image.Resampling.LANCZOS)
            
            left = (zoomed_w - real_w) / 2
            top = (zoomed_h - real_h) / 2
            right = left + real_w
            bottom = top + real_h
            
            pil_image = pil_image.crop((left, top, right, bottom))
            tk_image = ImageTk.PhotoImage(pil_image)

            label = tk.Label(root, image=tk_image, borderwidth=0, highlightthickness=0)
            label.pack(fill='both', expand=True)

        root.mainloop()
    except Exception as e:
        with open(os.path.join(LOCAL_DATA_DIR, 'splash_error.txt'), 'w') as f:
            f.write(str(e))

def wait_for_server(host, port, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                logging.info(f"Server at {host}:{port} is ready!")
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)
    return False

# ==========================================================
# =============    3. 关键逻辑：初始化数据库     =============
# ==========================================================

def initialize_database():
    """
    检查用户目录下是否存在数据库。
    如果不存在，则从打包资源中复制预置的数据库（包含1万个账号）。
    如果存在，则跳过（防止覆盖用户数据）。
    """
    target_db_path = os.environ['DATABASE_PATH']
    
    # 获取打包后的源文件路径
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包环境
        base_path = os.path.dirname(sys.executable)
        # 优先查找 _internal 目录 (PyInstaller > 6.0 默认目录)
        bundled_db_path = os.path.join(base_path, '_internal', 'db.sqlite3')
        if not os.path.exists(bundled_db_path):
            # 回退：查找 EXE 同级目录
            bundled_db_path = os.path.join(base_path, 'db.sqlite3')
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
        bundled_db_path = os.path.join(base_path, 'db.sqlite3')

    # 逻辑判断
    if os.path.exists(target_db_path):
        logging.info("检测到用户数据库已存在，跳过初始化复制 (保留用户数据)。")
    else:
        if os.path.exists(bundled_db_path):
            logging.info(f"首次运行，正在部署预置数据库: {bundled_db_path} -> {target_db_path}")
            try:
                # 复制文件
                shutil.copy2(bundled_db_path, target_db_path)
                
                # 关键：赋予读写权限 (去除只读属性)
                os.chmod(target_db_path, stat.S_IWRITE)
                logging.info("数据库部署成功，已赋予读写权限。")
            except Exception as e:
                logging.error(f"部署数据库失败: {e}")
                # 如果复制失败，Django 后面会自动创建一个空的，但没有预置数据
        else:
            logging.warning("未找到预置的 db.sqlite3 文件，系统将自动创建新的空数据库。")

# ==========================================================
# =============        4. API 逻辑类         ===============
# ==========================================================

class Api:
    # tms文件解析用于用户手动上传文件
    def processTomeyFile(self, params):
        """
        处理前端手动上传的 Tomey 文件 (.tms)
        对应前端 JS: window.pywebview.api.processTomeyFile(params)
        """
        import requests
        import base64
        import tempfile
        from pathlib import Path
        
        # 引入我们在 tomey_parser 中定义的解析器
        # 确保 tomey_parser 包在项目根目录下
        from tomey_parser.tms.stat_extractor import StatExtractor
        from tomey_parser.tms.radius_extractor import RadiusExtractor
        from tomey_parser.tms.height_extractor import HeightExtractor

        try:
            # 1. 提取文件内容和信息
            file_content_base64 = params.pop('file_content', None)
            file_name = params.pop('file_name', None)
            
            if not file_content_base64:
                return {'success': False, 'error': '请先选择一个 .tms 地形图文件。'}

            # 2. 解码并保存为临时文件
            try:
                file_content = base64.b64decode(file_content_base64)
            except Exception:
                return {'success': False, 'error': '文件解码失败，请重试。'}

            # 创建临时文件用于解析 (因为解析器需要文件路径)
            # delete=False 让我们能手动控制何时删除
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tms") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = Path(tmp_file.name)

            try:
                logging.info(f"正在解析上传的文件: {file_name} (Temp: {tmp_file_path})")

                # 3. 执行解析
                # A. 提取 Stats (平K, 陡K, 角度等)
                stat_ext = StatExtractor()
                stats = stat_ext.extract_data(tmp_file_path)
                
                # B. 提取 Radius CSV 数据
                rad_ext = RadiusExtractor()
                rad_csv = rad_ext.extract_to_csv_string(tmp_file_path)
                
                # C. 提取 Height CSV 数据
                hit_ext = HeightExtractor()
                hit_csv = hit_ext.extract_to_csv_string(tmp_file_path)

                # 4. 构造 Django 请求数据
                # 构造文件名
                timestamp = int(time.time())
                name_stem = Path(file_name).stem if file_name else "upload"
                rad_filename = f"RAD_{name_stem}_{timestamp}.dat"
                hit_filename = f"HIT_{name_stem}_{timestamp}.dat"

                # 构造 POST 数据 (表单参数 + 解析出的参数)
                payload = {
                    'patient_id': params.get('patient_id') or params.get('patient'),
                    'eye': params.get('eye'),
                    # 解析出的参数
                    'flat_k': stats.get('SimK1/ks', 0),
                    'plane_angle': stats.get('SimK1/ks Ang', 0),
                    'steep_k': stats.get('SimK2/kf', 0),
                    'inclined_angle': stats.get('SimK2/kf Ang', 0),
                    'delta_k': stats.get('Cyl', 0),
                    # 用户表单填写的其他参数 (透传给后端)
                    'overall_diameter': params.get('overall_diameter'),
                    'optical_zone_diameter': params.get('optical_zone_diameter'),
                    'mirror_degree': params.get('mirror_degree'),
                    'cylindrical_power': params.get('cylindrical_power'),
                    'overpressure': params.get('overpressure'),
                    'custom_type': '4', # 明确指定为 Tomey 普通定制
                }

                # 构造文件
                files = {
                    'radius_file': (rad_filename, rad_csv.encode('utf-8'), 'text/plain'),
                    'height_file': (hit_filename, hit_csv.encode('utf-8'), 'text/plain'),
                }

                # 5. 发送给 Django
                django_api_url = f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/process-tomey-data/'
                
                response = requests.post(django_api_url, data=payload, files=files, timeout=30)
                
                # 处理非 200 响应
                if response.status_code != 200:
                    logging.error(f"Django API Error: {response.text}")
                    try:
                        err_msg = response.json().get('error', '未知服务器错误')
                    except:
                        err_msg = f"服务器返回状态码 {response.status_code}"
                    return {'success': False, 'error': err_msg}

                return response.json()

            finally:
                # 6. 清理临时文件
                if os.path.exists(tmp_file_path):
                    try:
                        os.remove(tmp_file_path)
                    except:
                        pass

        except Exception as e:
            logging.error(f"Tomey 定制处理异常: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    # tms文件解析
    def process_tms_file(self, ocr_filename, patient_id=None, eye_type='right'):
        from pathlib import Path
        from tomey_parser.tms.stat_extractor import StatExtractor
        from tomey_parser.tms.radius_extractor import RadiusExtractor
        from tomey_parser.tms.height_extractor import HeightExtractor
        """
        处理 Tomey 文件并上传
        :param ocr_filename: OCR 识别出的文件名 (如 "101")
        :param patient_id: 关联的患者ID (可选，如果业务需要)
        :param eye_type: 眼别 ('left' 或 'right')
        """
        import requests
        
        # 1. 获取目录
        tomey_data_dir = self._read_config_value('tomey_data_path')
        if not tomey_data_dir:
            return {'success': False, 'error': '请先在设置中配置 Tomey 数据文件目录。'}
        
        # 2. 定位文件
        filename = f"{ocr_filename}.tms" if not ocr_filename.lower().endswith('.tms') else ocr_filename
        tms_file_path = Path(os.path.join(tomey_data_dir, filename))
        
        if not tms_file_path.exists():
            return {'success': False, 'error': f'未找到文件: {tms_file_path}\n请确认OCR识别正确且文件在指定目录下。'}

        try:
            logging.info(f"解析文件: {tms_file_path}")

            # 3. 解析 Stats
            stat_ext = StatExtractor()
            stats = stat_ext.extract_data(tms_file_path) # 返回字典
            
            # 4. 解析 CSV 内容
            rad_ext = RadiusExtractor()
            rad_csv = rad_ext.extract_to_csv_string(tms_file_path)
            
            hit_ext = HeightExtractor()
            hit_csv = hit_ext.extract_to_csv_string(tms_file_path)

            # 5. 准备上传数据
            payload = {
                'patient_id': patient_id, # 如果需要关联患者
                'eye': eye_type,
                'flat_k': stats.get('SimK1/ks', 0),
                'plane_angle': stats.get('SimK1/ks Ang', 0),
                'steep_k': stats.get('SimK2/kf', 0),
                'inclined_angle': stats.get('SimK2/kf Ang', 0),
                'delta_k': stats.get('Cyl', 0), # Cyl 对应 Delta K (散光)
            }

            # 6. 准备文件流
            # 使用时间戳防止重名
            ts = int(time.time())
            files = {
                'radius_file': (f'RAD_{ocr_filename}_{ts}.dat', rad_csv.encode('utf-8'), 'text/plain'),
                'height_file': (f'HIT_{ocr_filename}_{ts}.dat', hit_csv.encode('utf-8'), 'text/plain'),
            }

            # 7. 发送
            url = f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/process-tomey-data/'
            response = requests.post(url, data=payload, files=files, timeout=30)
            response.raise_for_status()
            
            return response.json()

        except Exception as e:
            logging.error(f"处理 Tomey 文件失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    def start_tomey_automation(self, context=None):
        import subprocess
        import webview 
        import pyautogui 
        global window
        
        # 存储上下文，供 finish_tomey_automation 使用
        if context:
            self.current_context = context
            logging.info(f"Tomey 自动化启动，上下文: {self.current_context}")
        
        tomey_dir = self._read_config_value('tomey_path')
        if not tomey_dir or not os.path.exists(tomey_dir):
            return {'success': False, 'error': '未配置 Tomey 程序目录。'}

        exe_path = os.path.join(tomey_dir, 'TmsSw.exe')
        if not os.path.exists(exe_path):
             return {'success': False, 'error': f'找不到 TmsSw.exe'}

        try:
            subprocess.Popen(exe_path, cwd=tomey_dir)
            if window: window.hide()
            
            screen_width, screen_height = pyautogui.size()
            win_w, win_h = 500, 480 
            x_pos = screen_width - win_w - 20
            y_pos = screen_height - win_h - 80

            self._overlay_window = webview.create_window(
                title='Tomey 助手', 
                html=self._get_overlay_html(), 
                width=win_w, height=win_h, x=x_pos, y=y_pos,
                on_top=True, resizable=False, frameless=True, easy_drag=False,
                js_api=self        
            )
            return {'success': True}
        except Exception as e:
            if window: window.show()
            return {'success': False, 'error': str(e)}

    def perform_ocr_recognition(self):
        try:
            from services.tomey_ocr import TomeyOCR
            logging.info("开始执行 OCR 识别...")
            ocr = TomeyOCR()
            result = ocr.find_and_capture()
            if result['success']:
                return {'success': True, 'filename': result['filename']}
            else:
                return {'success': False, 'error': result['error']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def finish_tomey_automation(self, filename, preview_data=None):
        """
        核心逻辑：
        1. 读取 .tms 文件
        2. 提取 Stats, Radius, Height 数据
        3. 结合之前的 current_context (患者ID等)
        4. 直接 POST 发送给 Django 后端接口
        5. 成功后刷新主界面
        """
        import requests
        import time
        from pathlib import Path
        from tomey_parser.tms.stat_extractor import StatExtractor
        from tomey_parser.tms.radius_extractor import RadiusExtractor
        from tomey_parser.tms.height_extractor import HeightExtractor

        global window
        
        # 关闭悬浮窗
        if hasattr(self, '_overlay_window'):
            self._overlay_window.destroy()
            del self._overlay_window
        
        if not window: return

        window.show()
        
        # 显示加载状态 (可选)
        # window.evaluate_js("alert('正在处理数据并生成方案，请稍候...')")

        try:
            # 1. 准备文件路径
            tomey_data_dir = self._read_config_value('tomey_data_path')
            name_stem = Path(filename).stem
            target_path = Path(os.path.join(tomey_data_dir, f"{name_stem}.tms"))
            
            if not target_path.exists():
                raise Exception(f"文件未找到: {target_path}")

            # 2. 执行解析
            logging.info(f"开始处理确认的文件: {target_path}")
            
            # 解析指标
            stat_ext = StatExtractor()
            stats = stat_ext.extract_data(target_path)
            
            # 解析 CSV 数据流
            rad_ext = RadiusExtractor()
            rad_csv = rad_ext.extract_to_csv_string(target_path)
            
            hit_ext = HeightExtractor()
            hit_csv = hit_ext.extract_to_csv_string(target_path)

            # 3. 构造提交数据
            ts = int(time.time())
            
            # 合并 OCR 解析的数据和之前暂存的前端上下文
            payload = {
                'patient_id': self.current_context.get('patient_id'),
                'eye': self.current_context.get('eye', 'right'),
                'overall_diameter': self.current_context.get('overall_diameter', 10.6),
                'optical_zone_diameter': self.current_context.get('optical_zone_diameter', 6.0),
                'mirror_degree': self.current_context.get('mirror_degree', 0),
                'cylindrical_power': self.current_context.get('cylindrical_power', 0),
                'overpressure': self.current_context.get('overpressure', 0),
                
                # 解析出的地形图数据
                'flat_k': stats.get('SimK1/ks', 0),
                'plane_angle': stats.get('SimK1/ks Ang', 0),
                'steep_k': stats.get('SimK2/kf', 0),
                'inclined_angle': stats.get('SimK2/kf Ang', 0),
                'delta_k': stats.get('Cyl', 0),
                
                # 其他默认值
                'custom_type': '4', 
            }

            files = {
                'radius_file': (f"RAD_{name_stem}_{ts}.dat", rad_csv.encode('utf-8'), 'text/plain'),
                'height_file': (f"HIT_{name_stem}_{ts}.dat", hit_csv.encode('utf-8'), 'text/plain'),
            }

            # 4. 发送请求给 Django
            logging.info("正在上传数据到 Django...")
            url = f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/process-tomey-data/'
            response = requests.post(url, data=payload, files=files, timeout=60)
            
            if response.status_code == 200:
                # 5. 成功：通知前端刷新
                logging.info("自动定制成功，刷新页面")
                # 这里的 handleTomeyData 实际上会执行 window.location.reload()
                window.evaluate_js(f"window.handleTomeyData('{filename}', null)")
            else:
                # 失败
                try: err_msg = response.json().get('error')
                except: err_msg = response.text
                window.evaluate_js(f"alert('自动定制失败: {err_msg}')")

        except Exception as e:
            logging.error(f"自动化处理流程异常: {e}", exc_info=True)
            window.evaluate_js(f"alert('系统错误: {str(e)}')")

    def cancel_tomey_automation(self):
        global window
        if hasattr(self, '_overlay_window'):
            self._overlay_window.destroy()
            del self._overlay_window
        if window: window.show()

    # ---在弹窗中预览解析的 Tomey 文件 ---
    def preview_tomey_file(self, filename):
        """
        根据文件名解析 .tms 文件，返回关键指标供前端预览
        """
        from tomey_parser.tms.stat_extractor import StatExtractor
        from pathlib import Path
        
        try:
            # 1. 获取数据目录
            tomey_data_dir = self._read_config_value('tomey_data_path')
            if not tomey_data_dir:
                return {'success': False, 'error': '未配置 Tomey 数据目录'}
            
            # 2. 拼接文件路径 (处理后缀)
            if not filename.lower().endswith('.tms'):
                real_filename = f"{filename}.tms"
            else:
                real_filename = filename
                
            file_path = Path(os.path.join(tomey_data_dir, real_filename))
            
            if not file_path.exists():
                return {'success': False, 'error': f'未找到文件: {real_filename}\n请确认已导出数据'}

            # 3. 解析 Stats
            logging.info(f"预览解析: {file_path}")
            stat_ext = StatExtractor()
            stats = stat_ext.extract_data(file_path)
            
            if not stats:
                return {'success': False, 'error': '解析成功但无数据'}

            # 4. 组装返回数据 (保留两位小数)
            data = {
                'flat_k': round(stats.get('SimK1/ks', 0), 2),
                'plane_angle': round(stats.get('SimK1/ks Ang', 0), 2),
                'steep_k': round(stats.get('SimK2/kf', 0), 2),
                'inclined_angle': round(stats.get('SimK2/kf Ang', 0), 2),
                'delta_k': round(stats.get('Cyl', 0), 2)
            }
            return {'success': True, 'data': data}

        except Exception as e:
            logging.error(f"预览失败: {e}")
            return {'success': False, 'error': str(e)}

    def _get_overlay_html(self):
        return """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: "Microsoft YaHei", sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                box-sizing: border-box;
                overflow: hidden
            }

            h4 {
                margin: 0 0 15px 0;
                color: #495057;
                font-size: 16px
            }

            .btn {
                padding: 8px 18px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin: 0;
                width: 100px; /* 稍微调小宽度以容纳更多按钮 */
            }
            .footer-actions {
                display: flex;          
                flex-direction: row;    
                justify-content: center;
                gap: 15px;              
                margin-top: 10px;       
                width: 100%;            
            }

            .btn-primary { background-color: #206bc4; color: white }
            .btn-success { background-color: #2fb344; color: white; display: none }
            .btn-warning { background-color: #f76707; color: white; display: none } /* 重新识别按钮颜色 */
            .btn-danger { background-color: #d63939; color: white }

            #status-text {
                margin-bottom: 15px;
                font-size: 14px;
                color: #666;
                height: 20px
            }

            .text-success { color: #2fb344 !important; font-weight: bold }
            .text-error { color: #d63939 !important }

            /* 卡片样式 */
            .topo-card {
                background: #ffffff;
                border: 1px solid #e6e7e9;
                border-radius: 8px;
                padding: 20px;
                width: 90%;
                max-width: 400px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
            }

            .topo-header {
                display: flex;
                align-items: center;
                color: #2fb344;
                font-weight: bold;
                font-size: 15px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #f0f0f0;
            }

            .topo-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                column-gap: 15px;
                row-gap: 15px;
            }

            .form-group {
                display: flex;
                flex-direction: column;
            }

            .form-label {
                font-size: 12px;
                color: #6c757d;
                margin-bottom: 6px;
                font-weight: 500;
            }

            .form-input {
                display: block;
                width: 85%;
                padding: 8px 12px;
                font-size: 14px;
                line-height: 1.42857143;
                color: #495057;
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
                cursor: not-allowed;
                opacity: 1;
            }
        </style>
    </head>
    <body>
        <h4 id="title">Tomey 助手</h4>
        <div id="status-text">请打开地形图后点击识别</div>

        <div class="topo-card">
            <div class="topo-header">
                <span id="file-info">地形图信息</span>
            </div>

            <div class="topo-grid">
                <div class="form-group">
                    <label class="form-label">平K(D)</label>
                    <input type="text" class="form-input" id="flat_k" readonly placeholder="-">
                </div>
                <div class="form-group">
                    <label class="form-label">平角度(°)</label>
                    <input type="text" class="form-input" id="plane_angle" readonly placeholder="-">
                </div>
                <div></div>

                <div class="form-group">
                    <label class="form-label">陡K(D)</label>
                    <input type="text" class="form-input" id="steep_k" readonly placeholder="-">
                </div>
                <div class="form-group">
                    <label class="form-label">斜角度(°)</label>
                    <input type="text" class="form-input" id="inclined_angle" readonly placeholder="-">
                </div>
                <div class="form-group">
                    <label class="form-label">▲K(D)</label>
                    <input type="text" class="form-input" id="delta_k" readonly placeholder="-">
                </div>
            </div>
        </div>

        <div class="footer-actions">
            <button class="btn btn-primary" id="btn-identify" onclick="doIdentify()">识别</button>
            <button class="btn btn-warning" id="btn-reidentify" onclick="doIdentify()">重新识别</button>
            <button class="btn btn-success" id="btn-confirm" onclick="doConfirm()">开始定制</button>
            <button class="btn btn-danger" id="btn-cancel" onclick="doCancel()">取消</button>
        </div>

        <script>
            let currentFilename = '';
            let currentData = null; // 存储解析到的数据

            function doIdentify() {
                const status = document.getElementById('status-text');
                const btnId = document.getElementById('btn-identify');
                const btnReId = document.getElementById('btn-reidentify');
                const btnConfirm = document.getElementById('btn-confirm');
                
                // 重置界面状态
                status.innerText = "正在识别屏幕...";
                status.className = "";
                btnId.disabled = true;
                btnId.innerText = "识别中...";
                btnReId.style.display = 'none';
                btnConfirm.style.display = 'none';
                
                // 清空旧数据
                clearInputs();

                // 1. 调用 OCR
                window.pywebview.api.perform_ocr_recognition().then(res => {
                    if (res.success) {
                        currentFilename = res.filename;
                        status.innerText = "识别成功(" + res.filename + ")，正在读取数据...";
                        
                        // 2. 调用预览解析接口
                        window.pywebview.api.preview_tomey_file(currentFilename).then(previewRes => {
                            btnId.style.display = 'none'; // 隐藏原始识别按钮
                            btnId.disabled = false;
                            btnId.innerText = "识别";

                            if (previewRes.success) {
                                // 3. 填充数据
                                currentData = previewRes.data;
                                fillInputs(currentData);
                                
                                status.innerHTML = "读取成功: " + currentFilename;
                                status.className = "text-success";
                                document.getElementById('file-info').innerText = "地形图信息: " + currentFilename;
                                
                                // 显示操作按钮
                                btnConfirm.style.display = 'inline-block';
                                btnReId.style.display = 'inline-block';
                            } else {
                                status.innerText = "读取文件失败: " + previewRes.error;
                                status.className = "text-error";
                                // 即使读取失败，也允许重新识别
                                btnReId.style.display = 'inline-block';
                            }
                        });

                    } else {
                        btnId.disabled = false;
                        btnId.innerText = "识别";
                        status.innerText = "识别失败: " + res.error;
                        status.className = "text-error";
                    }
                }).catch(err => {
                    btnId.disabled = false;
                    btnId.innerText = "识别";
                    status.innerText = "系统错误: " + err;
                    status.className = "text-error";
                });
            }

            function fillInputs(data) {
                document.getElementById('flat_k').value = data.flat_k;
                document.getElementById('plane_angle').value = data.plane_angle;
                document.getElementById('steep_k').value = data.steep_k;
                document.getElementById('inclined_angle').value = data.inclined_angle;
                document.getElementById('delta_k').value = data.delta_k;
            }

            function clearInputs() {
                const inputs = document.querySelectorAll('.form-input');
                inputs.forEach(input => input.value = '');
                currentData = null;
            }

            function doConfirm() {
                if (!currentFilename || !currentData) return;
                // 将文件名和完整数据回传给后端/主窗口
                window.pywebview.api.finish_tomey_automation(currentFilename, currentData);
            }

            function doCancel() {
                window.pywebview.api.cancel_tomey_automation();
            }
        </script>
    </body>
</html>"""
    def _read_config_value(self, key):
        import json
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f).get(key)
            except: pass
        return None

    def _save_config_value(self, key, value):
        import json
        data = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except: pass
        data[key] = value
        try:
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Config save error: {e}")

    def load_tomey_path(self):
        return self._read_config_value('tomey_path')
    def load_tomey_data_path(self):
        # 读取数据路径
        return self._read_config_value('tomey_data_path')

    def select_and_configure_tomey(self):
        import webview
        global window
        if not window: return {'success': False, 'error': 'Window not init'}
        
        try:
            # 修改：使用 FOLDER_DIALOG 选择目录
            result = window.create_file_dialog(webview.FOLDER_DIALOG)
            if not result: return {'success': False, 'error': '用户取消'}
            
            selected_path = result[0]
            
            # 检查目录下是否存在 exe
            exe_path = os.path.join(selected_path, 'TmsSw.exe')
            if not os.path.exists(exe_path):
                # 尝试大小写不敏感查找 (保险起见)
                found = False
                for f in os.listdir(selected_path):
                    if f.lower() == 'tmssw.exe':
                        exe_path = os.path.join(selected_path, f)
                        found = True
                        break
                if not found:
                    return {'success': False, 'error': f'在该目录下未找到 TmsSw.exe 程序。\n请选择正确的安装目录。'}

            # 保存的是目录路径
            self._save_config_value('tomey_path', selected_path)
            return {'success': True, 'message': 'Tomey 程序目录配置成功', 'path': selected_path}
        except Exception as e: 
            return {'success': False, 'error': str(e)}
    # --- 3. 配置 Tomey 数据目录 ---
    def select_and_configure_tomey_data(self):
        import webview
        global window
        if not window: return {'success': False, 'error': 'Window not init'}
        
        try:
            result = window.create_file_dialog(webview.FOLDER_DIALOG)
            if not result: return {'success': False, 'error': '用户取消'}
            
            selected_path = result[0]
            # 这里不强制检查是否存在 .tms 文件，因为目录可能是空的
            
            self._save_config_value('tomey_data_path', selected_path)
            return {'success': True, 'message': 'Tomey 数据目录配置成功', 'path': selected_path}
        except Exception as e: 
            return {'success': False, 'error': str(e)}

    def load_medmont_path(self):
        return self._read_config_value('medmont_path')

    def select_and_configure_medmont(self):
        import webview
        import codecs
        global window
        if not window: return {'success': False, 'error': 'Window not init'}
        try:
            result = window.create_file_dialog(webview.FOLDER_DIALOG)
            if not result: return {'success': False, 'error': '用户取消'}
            selected_path = result[0]
            
            if getattr(sys, 'frozen', False):
                ExePath = sys.executable
                AppPath = os.path.dirname(ExePath)
            else:
                AppPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
                ExePath = os.path.join(AppPath, 'iBrightAI.exe')

            XmlContent = f"""<?xml version="1.0" encoding="GBK"?>
<Link xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<Command>{ExePath}</Command>
<Arguments>%f</Arguments>
<ExportPath>{AppPath}</ExportPath>
<ExportName>LinkExport</ExportName>
<ExportFormat>UTF16</ExportFormat>
<Text>导出至普诺瞳 AI</Text>
<Tooltip>Export topographical data to the iBrightAI</Tooltip>
<IconFile />
<ExportableItems><ExportType>E300Exam</ExportType></ExportableItems>
<Flags><Flag><Key>ExportE300Bitmaps</Key><Value>false</Value></Flag></Flags>
</Link>"""
            links_path = os.path.join(selected_path, 'Links')
            os.makedirs(links_path, exist_ok=True)
            with codecs.open(os.path.join(links_path, 'ibrightAI.linksettings'), 'w', encoding='gbk') as f:
                f.write(XmlContent)
            self._save_config_value('medmont_path', selected_path)
            return {'success': True, 'message': 'Medmont配置成功', 'path': selected_path}
        except Exception as e: return {'success': False, 'error': str(e)}

    def processMxfFile(self, params):
        import requests
        import base64
        try:
            file_content_base64 = params.pop('file_content', None)
            file_name = params.pop('file_name', None)
            if file_content_base64 and file_name:
                logging.info(f"使用用户选择的文件: {file_name}")
                file_content = base64.b64decode(file_content_base64)
                used_file_name = file_name
            else:
                if getattr(sys, 'frozen', False):
                    application_path = os.path.dirname(sys.executable)
                else:
                    application_path = os.path.dirname(__file__)
                muf_path = os.path.join(application_path, 'LinkExport.muf')
                mxf_path = os.path.join(application_path, 'LinkExport.mxf')
                if os.path.exists(muf_path):
                    logging.info(f"重命名 {muf_path} -> {mxf_path}")
                    shutil.move(muf_path, mxf_path)
                elif not os.path.exists(mxf_path):
                    return {'success': False, 'error': f"未找到 LinkExport 文件在 {application_path}"}
                with open(mxf_path, 'rb') as f: file_content = f.read()
                used_file_name = 'LinkExport.mxf'

            django_api_url = f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/process-mxf/'
            files = {'corneal_file': (used_file_name, file_content, 'application/octet-stream')}
            response = requests.post(django_api_url, files=files, data=params, timeout=300)
            if response.status_code == 400:
                return {'success': False, 'error': '地形图数据量不足，请重新采集地形图'}
            response.raise_for_status()
            return response.json()
        except Exception as e: return {'success': False, 'error': str(e)}

    def export_patients(self, patient_ids, username='', *args):
        global window
        import webview
        import requests
        import base64
        try:
            if not window: raise Exception("Window not ready")
            save_path = window.create_file_dialog(webview.SAVE_DIALOG, directory=os.path.expanduser('~'), save_filename='customized_data.xlsx')
            if not save_path: return {'success': False, 'error': '操作取消'}
            if isinstance(save_path, tuple):
                save_path = save_path[0]
            django_api_url = f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/generate-export-data/'
            response = requests.post(django_api_url, data={'patient_ids': patient_ids, 'username': username}, timeout=300)
            response.raise_for_status()
            res_data = response.json()
            if not res_data.get('success'): raise Exception(res_data.get('error'))
            excel_data = base64.b64decode(res_data.get('excel_data'))
            with open(save_path, 'wb') as f: f.write(excel_data)
            requests.post(f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/update-export-count/', data={'patient_ids': patient_ids}, timeout=30)
            return {'success': True, 'path': save_path}
        except Exception as e: return {'success': False, 'error': str(e)}

# ==========================================================
# =============        5. 运行服务           ===============
# ==========================================================

def run_server():
    # 关键修复：重定向标准输出，防止无控制台模式下崩溃
    sys.stdout = LoggerWriter(logging.info)
    sys.stderr = LoggerWriter(logging.error)

    from waitress import serve
    import django
    from django.core.management import execute_from_command_line
    import matplotlib
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eyehospital.settings")
    os.environ['DATABASE_PATH'] = os.path.join(LOCAL_DATA_DIR, 'db.sqlite3')
    os.environ['MEDIA_ROOT'] = os.path.join(LOCAL_DATA_DIR, 'media')
    os.environ['STATIC_ROOT'] = os.path.join(LOCAL_DATA_DIR, 'static')
    os.environ['CONFIG_PATH'] = CONFIG_FILE_PATH

    matplotlib.use('Agg')
    django.setup()
    
    try:
        logging.info("初始化 Django 环境...")
        
        # 1. 数据库迁移 (确保兼容性)
        # 即使复制了数据库，运行 migrate 也是安全的，它会确保表结构最新
        logging.info("Run migration...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])

        # 2. 收集静态文件
        static_dir = os.environ['STATIC_ROOT']
        if not os.path.exists(static_dir) or not os.listdir(static_dir):
            logging.info("Run collectstatic...")
            execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--clear'])

        # 3. 创建超级用户 (如果数据库是空的)
        from django.conf import settings
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            logging.info("Creating superuser...")
            User.objects.create_superuser('admin', '', '123456')
            
        # 4. 启动 WSGI
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
        logging.info(f"Starting Waitress server on {SERVER_HOST}:{SERVER_PORT}...")
        serve(application, host=SERVER_HOST, port=SERVER_PORT, threads=4, _quiet=True)
    except Exception as e:
        logging.error(f"Server error: {str(e)}", exc_info=True)

# ==========================================================
# =============        6. 程序主入口         ===============
# ==========================================================

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # 关键修复：主进程也需要重定向输出
    sys.stdout = LoggerWriter(logging.info)
    sys.stderr = LoggerWriter(logging.error)
    
    lock_file_path = os.path.join(os.path.expanduser('~'), 'EyeHospitalApp.lock')
    lock = FileLock(lock_file_path, timeout=0)
    
    try:
        lock.acquire()
        
        # --- 正常启动 ---
        logging.info("程序启动...")
        
        # 1. 启动 Splash Screen (独立进程，非阻塞)
        splash_img_path = get_resource_path(os.path.join('static', 'img', 'login', 'loginBackground.png'))
        splash_process = None
        if os.path.exists(splash_img_path):
            splash_process = multiprocessing.Process(
                target=show_splash_screen, 
                args=(splash_img_path, APP_WIDTH, APP_HEIGHT)
            )
            splash_process.daemon = True 
            splash_process.start()
        
        # 2. 初始化数据库 (关键步骤：复制预置数据)
        # 此步骤必须在 Django 启动前完成
        initialize_database()

        # 3. 启动 Server 线程
        t = threading.Thread(target=run_server)
        t.daemon = True
        t.start()
        
        # 4. 创建 Webview 窗口 (先隐藏，等 Server 就绪再显示)
        from webview import create_window, start
        import webview
        api = Api()
        
        logging.info("Creating webview window...")
        window = create_window(
            WINDOW_TITLE,
            f'http://{SERVER_HOST}:{SERVER_PORT}',
            width=APP_WIDTH, height=APP_HEIGHT,
            min_size=(800, 600),
            text_select=True,
            js_api=api,
            hidden=True 
        )
        
        def on_loaded():
            logging.info("Webview loaded, showing window.")
            window.show() 
            if splash_process and splash_process.is_alive():
                splash_process.terminate() 

        window.events.loaded += on_loaded
        
        # 5. 等待 Server 就绪
        logging.info("Waiting for server...")
        if wait_for_server(SERVER_HOST, SERVER_PORT, timeout=60):
            logging.info("Server ready, start UI.")
            webview.start(debug=False)
        else:
            if splash_process and splash_process.is_alive():
                splash_process.terminate()
            logging.error("Server startup timeout.")
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动失败", "服务启动超时。请检查日志文件: " + LOG_FILE_PATH)
            root.destroy()

    except Timeout:
        # --- 第二次启动 (Medmont 调用) ---
        logging.warning("程序已在运行中...")
        try:
            import requests
            if len(sys.argv) > 1:
                export_file_path = sys.argv[1]
                if os.path.exists(export_file_path):
                    if getattr(sys, 'frozen', False):
                        app_path = os.path.dirname(sys.executable)
                    else:
                        app_path = os.path.dirname(os.path.abspath(__file__))
                    
                    target_mxf = os.path.join(app_path, 'LinkExport.mxf')
                    shutil.copy2(export_file_path, target_mxf)
                    
                    try:
                        requests.post(f'http://{SERVER_HOST}:{SERVER_PORT}/patient/api/notify-medmont/', data={}, timeout=2)
                    except: pass
            
            windows = gw.getWindowsWithTitle(WINDOW_TITLE)
            if windows:
                win = windows[0]
                if win.isMinimized: win.restore()
                win.activate()

        except Exception: pass
        sys.exit(0)

    except Exception as e:
        logging.error(f"Startup failed: {e}")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("系统错误", str(e))
            root.destroy()
        except: pass
        sys.exit(1)

    finally:
        if lock.is_locked: lock.release()