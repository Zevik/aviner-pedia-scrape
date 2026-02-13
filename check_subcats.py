#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('aviner_database.db')
cursor = conn.cursor()

with open('subcats_analysis.txt', 'w', encoding='utf-8') as f:
    # סדרות
    f.write('===== סדרות =====\n')
    cursor.execute('''
        SELECT s.name, s.article_count
        FROM subcategories s
        JOIN categories c ON s.category_id = c.id
        WHERE c.name = ?
        ORDER BY s.article_count DESC
    ''', ('סדרות',))
    for name, count in cursor.fetchall():
        f.write(f'{name}: {count}\n')

    # שו"ת הלכה
    f.write('\n===== שו"ת הלכה =====\n')
    cursor.execute('''
        SELECT s.name, s.article_count
        FROM subcategories s
        JOIN categories c ON s.category_id = c.id
        WHERE c.name = ?
        ORDER BY s.article_count DESC
    ''', ('שו"ת הלכה',))
    results = cursor.fetchall()
    if results:
        for name, count in results:
            f.write(f'{name}: {count}\n')
    else:
        f.write('אין תתי-קטגוריות!\n')

        # בואו נבדוק כמה יש בכלל
        cursor.execute('SELECT COUNT(*) FROM articles WHERE section = ?', ('שו"ת הלכה',))
        total = cursor.fetchone()[0]
        f.write(f'סה"כ מאמרים בשו"ת: {total}\n')

        # נראה דוגמאות
        cursor.execute('SELECT title FROM articles WHERE section = ? LIMIT 10', ('שו"ת הלכה',))
        f.write('\nדוגמאות:\n')
        for (title,) in cursor.fetchall():
            f.write(f'  - {title}\n')

print('Analysis saved to subcats_analysis.txt')
