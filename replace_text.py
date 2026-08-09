import os
import sqlite3

def replace_in_files():
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(('.html', '.py', '.js', '.css', '.md')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'محافظة المنيا' in content:
                        print(f"Replacing in {path}")
                        content = content.replace('محافظة المنيا', 'محافظة المنيا')
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    elif 'مغاغة' in content:
                        print(f"Found 'مغاغة' in {path}, checking if it needs replacement...")
                        content = content.replace('مغاغة', '')
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                except Exception as e:
                    print(f"Error reading {path}: {e}")

def replace_in_db():
    try:
        conn = sqlite3.connect('instance/school.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                if col[2] in ('TEXT', 'VARCHAR'):
                    cursor.execute(f"UPDATE {table_name} SET {col[1]} = REPLACE({col[1]}, 'محافظة المنيا', 'محافظة المنيا')")
                    if cursor.rowcount > 0:
                        print(f"Updated {cursor.rowcount} rows in DB: {table_name}.{col[1]}")
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB Error:", e)

if __name__ == '__main__':
    replace_in_files()
    replace_in_db()
