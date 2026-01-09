import sqlite3
import os

# 尝试两个可能的数据库路径
paths = [
    os.path.join(os.path.expanduser('~'), 'EyeHospitalData', 'db.sqlite3'),
    os.path.join('D:\\hospital-server', 'db.sqlite3')
]

db_path = None
for p in paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print('数据库文件未找到')
else:
    print(f'数据库路径: {db_path}')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print('\n=== 搜索包含 终端客户/terminal/customer/client 的字段 ===\n')

    found = False
    for table in tables:
        table_name = table[0]
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = cursor.fetchall()
        for col in columns:
            col_name = col[1].lower()
            if 'terminal' in col_name or 'customer' in col_name or 'client' in col_name:
                print(f'表: {table_name}, 字段: {col[1]}, 类型: {col[2]}')
                found = True

    if not found:
        print('未找到相关字段')

    print('\n=== 所有业务表及其字段 ===\n')
    for table in tables:
        table_name = table[0]
        if not table_name.startswith('sqlite_') and not table_name.startswith('django_') and not table_name.startswith('auth_'):
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            print(f'{table_name}: {col_names}')

    conn.close()
