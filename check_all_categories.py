# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('aviner_database.db')

print("=== All Categories ===")
cursor = conn.execute('SELECT name, article_count FROM categories ORDER BY article_count DESC')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} מאמרים")

print("\n\n=== Samples from new series categories ===")
series = ['אורות הקודש', 'אורות התשובה', 'מאמרי הרב שלמה אבינר', 'ספר אורות', 'כוזרי', 'נתיב התורה']
for series_name in series:
    cursor = conn.execute('SELECT title FROM articles WHERE category_id = (SELECT id FROM categories WHERE name = ?) LIMIT 3', (series_name,))
    results = cursor.fetchall()
    if results:
        print(f"\n{series_name}:")
        for row in results:
            print(f"  - {row[0]}")

conn.close()
