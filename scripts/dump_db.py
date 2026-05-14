import sqlite3
import json

import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(ROOT_DIR, "internship_hunt.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)

    for table in tables:
        table_name = table[0]
        print(f"\n--- Schema for {table_name} ---")
        cursor.execute(f"PRAGMA table_info({table_name})")
        print(cursor.fetchall())
        
        print(f"\n--- Data from {table_name} (latest 3 rows) ---")
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
