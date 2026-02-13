#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

conn = sqlite3.connect('aviner_database.db')
cursor = conn.cursor()

# בדיקה כמה מאמרים יש בלי תוכן
empty = cursor.execute('SELECT COUNT(*) FROM articles WHERE content_length = 0 OR content IS NULL OR content = ""').fetchone()[0]
total = cursor.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
with_content = total - empty

print(f'Total articles: {total}')
print(f'With content: {with_content}')
print(f'Without content: {empty}')
print(f'Empty percentage: {empty/total*100:.1f}%')

# דוגמאות למאמרים ריקים
print('\nSample empty articles:')
cursor.execute('SELECT title, filename FROM articles WHERE content_length = 0 LIMIT 10')
for title, filename in cursor.fetchall():
    print(f'  - {title}')
    print(f'    File: {filename}')

    # בדיקה אם הקובץ קיים
    file_path = Path('pages') / filename
    if file_path.exists():
        print(f'    File EXISTS - size: {file_path.stat().st_size} bytes')
    else:
        print(f'    File NOT FOUND')

# בדיקה של המאמר הספציפי שהמשתמש ציין
print('\n\nChecking specific article:')
cursor.execute("SELECT title, filename, content_length FROM articles WHERE title LIKE '%העולם הזה אינו שלך%'")
result = cursor.fetchone()
if result:
    title, filename, content_length = result
    print(f'Title: {title}')
    print(f'Filename: {filename}')
    print(f'Content length: {content_length}')

    file_path = Path('pages') / filename
    if file_path.exists():
        print(f'File EXISTS - size: {file_path.stat().st_size} bytes')
    else:
        print(f'File NOT FOUND')

conn.close()
