# -*- mode: python -*-
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 1. 收集 Django 静态文件和模板
django_data = []
for item in collect_data_files('django', include_py_files=True):
    django_data.append(item)

# 2. 分析阶段 (Analysis)
a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[
        ('verify_app.dll', '.'),
    ],
    # 这里的 datas 会被复制到生成的文件夹根目录或指定子目录中
    datas=django_data + [
        ('eyehospital/settings.py', '.'),
        ('eyehospital/urls.py', '.'),
        ('eyehospital/wsgi.py', '.'),
        ('templates/', 'templates'),
        ('static/', 'static'),
        ('db.sqlite3', '.'),
        # 注意：Tesseract 文件夹不建议在这里打包，因为太大了。
        # 建议继续使用 Inno Setup 在安装时复制 bin 文件夹。
    ],
    hiddenimports=[
        'django.contrib.admin.apps',
        'django.contrib.auth.apps',
        'django.contrib.contenttypes.apps',
        'django.contrib.sessions.apps',
        'django.contrib.messages.apps',
        'django.contrib.staticfiles.apps',
        'webview',
        'waitress',
        'matplotlib.backends.backend_agg',
        'scipy.special.cython_special', # 添加 scipy 常见隐式依赖
        'scipy.spatial.transform._rotation_groups',
        'patient.management.commands.init',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 3. EXE 阶段 (只生成主程序入口，不包含依赖)
exe = EXE(
    pyz,
    a.scripts,
    [], # 注意：这里去掉了 a.binaries, a.zipfiles, a.datas
    exclude_binaries=True, # 关键：排除二进制文件，放到 COLLECT 阶段
    name='iBrightAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # 关键优化：禁用 UPX 压缩，提升启动速度
    console=False, 
    icon='icon.ico', 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 4. COLLECT 阶段 (关键新增：生成单目录结构)
# 这会创建一个名为 'iBrightAI' 的文件夹，里面包含 exe 和所有依赖
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False, # 关键优化：禁用 UPX
    upx_exclude=[],
    name='iBrightAI', # 输出文件夹名称 (dist/iBrightAI)
)