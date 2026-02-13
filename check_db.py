# -*- coding: utf-8 -*-
import sqlite3
import sys

# Set UTF-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('aviner_database.db')

print("=== Sections in database ===")
cursor = conn.execute('SELECT section, COUNT(*) FROM articles GROUP BY section ORDER BY COUNT(*) DESC')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} פריטים")

print("\n=== Sample articles with sections ===")
cursor = conn.execute('SELECT title, section LIMIT 20')
for row in cursor.fetchall():
    print(f"{row[1]} | {row[0]}")

conn.close()
