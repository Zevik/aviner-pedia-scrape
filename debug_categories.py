# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('aviner_database.db')

print("=== Categories ===")
cursor = conn.execute('SELECT name, article_count FROM categories ORDER BY article_count DESC LIMIT 20')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== Subcategories ===")
cursor = conn.execute('SELECT name, article_count FROM subcategories ORDER BY article_count DESC LIMIT 20')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n=== Sample articles from 'כללי' category ===")
cursor = conn.execute('''
    SELECT a.title, a.section, s.name as subcategory
    FROM articles a
    LEFT JOIN subcategories s ON a.subcategory_id = s.id
    WHERE a.category_id = (SELECT id FROM categories WHERE name = 'כללי')
    LIMIT 10
''')
for row in cursor.fetchall():
    print(f"{row[1]} | {row[2] if row[2] else 'None'} | {row[0][:60]}")

conn.close()
