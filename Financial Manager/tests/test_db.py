import sqlite3

db = sqlite3.connect('resources/financial_manager.db')
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Database Tables Created:')
for table in tables:
    print(f'  - {table[0]}')
db.close()
