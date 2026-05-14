import sqlite3
import os
from .models import RawSignal

class DatabaseManager:
    def __init__(self, db_path="data/leads.db"):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,  -- Prevents duplicates
            title TEXT,
            source TEXT,
            published_at DATETIME,
            scraped_at DATETIME
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def save_signal(self, signal: RawSignal) -> bool:
        """Saves signal to DB. Returns True if new, False if duplicate."""
        query = """
        INSERT OR IGNORE INTO signals 
        (url, title, source, published_at, scraped_at) 
        VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.conn.cursor()
        try:
            pub_date = signal.published_at.isoformat() if signal.published_at else None
            cursor.execute(query, (
                signal.url, 
                signal.title, 
                signal.source, 
                pub_date, 
                signal.scraped_at.isoformat()
            ))
            self.conn.commit()
            return cursor.rowcount > 0 # Returns True only if a new row was added
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
            