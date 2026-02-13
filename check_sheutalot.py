import sqlite3

conn = sqlite3.connect('aviner_database.db')
conn.row_factory = sqlite3.Row

# Check all subcategories
result = conn.execute('''
    SELECT c.name as cat, s.name as subcat, s.article_count
    FROM subcategories s
    JOIN categories c ON s.category_id = c.id
    ORDER BY c.name, s.article_count DESC
''').fetchall()

with open('subcategories_report.txt', 'w', encoding='utf-8') as f:
    f.write('All subcategories:\n\n')
    current_cat = None
    for r in result:
        if r['cat'] != current_cat:
            f.write(f'\n{r["cat"]}:\n')
            current_cat = r['cat']
        f.write(f'  - {r["subcat"]}: {r["article_count"]}\n')

conn.close()
print("Report saved to subcategories_report.txt")
