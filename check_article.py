# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('aviner_database.db')

# Check specific article
title = "אורות הקודש ב', עמ' שיב' - שיג' (סדרה)"
cursor = conn.execute('''
    SELECT a.title, a.section, c.name as category, s.name as subcategory
    FROM articles a
    LEFT JOIN categories c ON a.category_id = c.id
    LEFT JOIN subcategories s ON a.subcategory_id = s.id
    WHERE a.title LIKE ?
    LIMIT 5
''', (f'%אורות הקודש%',))

print("=== Articles matching 'אורות הקודש' ===")
for row in cursor.fetchall():
    print(f"\nTitle: {row[0]}")
    print(f"Section: {row[1]}")
    print(f"Category: {row[2] if row[2] else 'None'}")
    print(f"Subcategory: {row[3] if row[3] else 'None'}")

# Check all articles in a section
print("\n\n=== Sample from 'סדרות' section ===")
cursor = conn.execute('''
    SELECT a.title, c.name as category, s.name as subcategory
    FROM articles a
    LEFT JOIN categories c ON a.category_id = c.id
    LEFT JOIN subcategories s ON a.subcategory_id = s.id
    WHERE a.section = 'סדרות'
    LIMIT 10
''')

for row in cursor.fetchall():
    print(f"\n{row[0]}")
    print(f"  Category: {row[1] if row[1] else 'None'}")
    print(f"  Subcategory: {row[2] if row[2] else 'None'}")

conn.close()
