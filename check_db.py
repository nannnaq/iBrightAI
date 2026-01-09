import sqlite3
import os

db_path = os.path.join(os.path.expanduser('~'), 'EyeHospitalData', 'db.sqlite3')
print(f"Database path: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查 BasicParams 表
cursor.execute('PRAGMA table_info(patient_basicparams)')
columns = cursor.fetchall()

print("\nBasicParams table columns:")
for col in columns:
    print(f"  {col[1]}: {col[2]} (notnull={col[3]}, default={col[4]})")

conn.close()
