import sqlite3
from app import app
from models import db
import os

def apply_migrations():
    db_path = 'instance/mohamed_saber.db'
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return

    # Add new column to questions if it doesn't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN question_type VARCHAR(20) NOT NULL DEFAULT 'mcq'")
        print("Added question_type to questions table.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print("Column question_type already exists.")
        else:
            print("Error adding column:", e)
    
    conn.commit()
    conn.close()

    # Create new tables
    with app.app_context():
        db.create_all()
        print("Created all new tables successfully.")

if __name__ == '__main__':
    apply_migrations()
