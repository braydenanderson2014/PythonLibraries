#!/usr/bin/env python3
"""
Database utility script for SQLite operations
"""
import sqlite3
import os

def create_database():
    """Create a new database"""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database created successfully")

if __name__ == "__main__":
    create_database()
