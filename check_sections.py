# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('aviner_database.db')

print("=== Sections in database ===")
cursor = conn.execute('SELECT section, COUNT(*) FROM articles GROUP BY section ORDER BY COUNT(*) DESC')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} פריטים")

print("\n=== Sample articles by section ===")
cursor = conn.execute('''
    SELECT section, COUNT(*) as cnt,
           GROUP_CONCAT(title, " | ") as samples
    FROM (
        SELECT section, title
        FROM articles
        GROUP BY section
        HAVING MIN(id)
        LIMIT 3
    )
    GROUP BY section
''')

sections = ['מאמרים', 'וידאו', 'שו"ת', 'סדרות', 'כללי']
for sec in sections:
    cursor = conn.execute('SELECT title FROM articles WHERE section = ? LIMIT 3', (sec,))
    print(f"\n{sec}:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

conn.close()
