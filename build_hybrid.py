#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה דאטה-בייס משולב: קורא קבצים כמו build.py + קטגוריות מ-XML
"""
import os
import re
import sqlite3
from pathlib import Path
from collections import defaultdict
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_categories_from_xml(xml_path):
    """
    חולץ קטגוריות מ-XML לכל עמוד
    מחזיר dict: {title: [categories]}
    """
    logging.info("📖 קורא קטגוריות מ-XML...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}

    categories_map = {}
    pages = root.findall('.//mw:page', ns)

    for page in pages:
        title_elem = page.find('mw:title', ns)
        if title_elem is None:
            continue

        title = title_elem.text

        # מדלגים על עמודי מערכת
        if title.startswith('קטגוריה:') or title.startswith('Category:') or \
           title.startswith('תבנית:') or title.startswith('Template:'):
            continue

        # מוצאים את הגרסה האחרונה
        revisions = page.findall('mw:revision', ns)
        if not revisions:
            continue

        latest_revision = revisions[-1]
        text_elem = latest_revision.find('.//mw:text', ns)
        if text_elem is None or text_elem.text is None:
            continue

        wikitext = text_elem.text

        # חילוץ קטגוריות
        cat_pattern = r'\[\[(?:קטגוריה|Category):([^\]|]+)(?:\|[^\]]*)?\]\]'
        categories = []
        for match in re.finditer(cat_pattern, wikitext, re.IGNORECASE):
            cat_name = match.group(1).strip()
            categories.append(cat_name)

        if categories:
            categories_map[title] = categories

    logging.info(f"✅ נמצאו קטגוריות ל-{len(categories_map)} עמודים")
    return categories_map

def categorize_with_xml(title, xml_categories):
    """
    קביעת קטגוריה ותת-קטגוריה על פי קטגוריות מ-XML
    """
    # ברירת מחדל
    category = 'כללי'
    subcategory = 'כללי'

    # קביעת קטגוריה ראשית מהכותרת
    if '(וידאו)' in title or '(שיעור)' in title:
        category = 'וידאו'
    elif '(מאמר)' in title:
        category = 'מאמרים'
    elif '(שו"ת)' in title or '(שו_ת)' in title:
        category = 'שו"ת הלכה'
    elif '(סדרה)' in title:
        category = 'סדרות'

    # מיפוי קטגוריות לתתי-קטגוריות
    priority_map = {
        # סדרות
        'אורות הקודש': 'אורות הקודש',
        'אורות התשובה': 'אורות התשובה',
        'ספר אורות': 'ספר אורות',
        'עין איה': 'עין איה',
        'כוזרי': 'כוזרי',
        'שמונה פרקים': 'שמונה פרקים לרמבם',
        'תפארת ישראל': 'תפארת ישראל - מהר"ל',

        # שו"ת ספציפי
        'שו"ת סמס': 'שו"ת סמס',
        'סמס': 'שו"ת סמס',
        'SMS': 'שו"ת סמס',

        # נושאים
        'אקטואליה': 'אקטואליה',
        'זוגיות ומשפחה': 'זוגיות ומשפחה',
        'זוגיות': 'זוגיות ומשפחה',
        'משפחה': 'זוגיות ומשפחה',
        'נישואין': 'זוגיות ומשפחה',
        'חתונה': 'זוגיות ומשפחה',
        'מדינת ישראל': 'מדינת ישראל',
        'ארץ ישראל': 'מדינת ישראל',
        'צה"ל': 'מדינת ישראל',
        'מוסר ומידות': 'מוסר ומידות',
        'מוסר': 'מוסר ומידות',
        'מועדים': 'מועדים',
        'חגים': 'מועדים',
        'שבת': 'מועדים',
        'פסח': 'מועדים',
        'תפילה': 'תפילה',
        'תפילות': 'תפילה',
        'ברכות': 'תפילה',
        'תורה': 'תורה',
        'לימוד תורה': 'תורה',
        'חינוך': 'חינוך',
        'אמונה': 'אמונה',
        'מיוחדים': 'מיוחדים',
        'הלכה': 'הלכה',
        'אורות': 'אורות',
    }

    # אם אין קטגוריה XML, עבור שו"ת נשתמש בברירת מחדל
    if not xml_categories and category == 'שו"ת הלכה':
        subcategory = 'שו"ת לפי נושא'
        # זיהוי SMS
        if 'סמס' in title or 'SMS' in title or 'sms' in title:
            subcategory = 'שו"ת סמס'

    # חיפוש בקטגוריות XML
    for key, value in priority_map.items():
        for cat in xml_categories:
            if key.lower() in cat.lower():
                subcategory = value
                break
        if subcategory != 'כללי':
            break

    # עבור סדרות, נחפש גם בכותרת
    if category == 'סדרות':
        for key, value in priority_map.items():
            if key.lower() in title.lower():
                subcategory = value
                break

    return category, subcategory

def create_database(html_folder_path, xml_path, overwrite_db=False):
    """
    יוצר דאטה בייס משולב
    """
    logging.info("🚀 מתחיל בניית דאטה בייס משולבת...")

    db_path = 'aviner_database.db'
    if overwrite_db and os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # יצירת טבלאות
    tables_sql = """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        article_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS subcategories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        description TEXT,
        article_count INTEGER DEFAULT 0,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    );
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        filename TEXT UNIQUE NOT NULL,
        url_slug TEXT,
        section TEXT,
        category_id INTEGER,
        subcategory_id INTEGER,
        content TEXT,
        content_length INTEGER,
        video_id TEXT,
        link_count INTEGER DEFAULT 0,
        is_hub BOOLEAN DEFAULT 0,
        created_date TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (subcategory_id) REFERENCES subcategories (id)
    );
    CREATE INDEX IF NOT EXISTS idx_section ON articles(section);
    CREATE INDEX IF NOT EXISTS idx_category ON articles(category_id);
    CREATE INDEX IF NOT EXISTS idx_subcategory ON articles(subcategory_id);
    CREATE INDEX IF NOT EXISTS idx_filename ON articles(filename);
    """
    cursor.executescript(tables_sql)
    logging.info("✅ טבלאות נוצרו")

    # קריאת קטגוריות מ-XML
    xml_categories = extract_categories_from_xml(xml_path)

    # עיבוד קבצי HTML
    html_folder = Path(html_folder_path)
    html_files = list(html_folder.glob('*.html'))
    logging.info(f"📂 נמצאו {len(html_files):,} קבצי HTML")

    data = []
    categories_dict = defaultdict(int)
    subcategories_dict = defaultdict(int)

    for i, file_path in enumerate(html_files, 1):
        if i % 500 == 0:
            logging.info(f"🔄 עיבוד קובץ {i}/{len(html_files)}")

        filename = file_path.name

        # פענוח שם הקובץ אם הוא מקודד
        from urllib.parse import unquote
        try:
            decoded_filename = unquote(filename)
        except:
            decoded_filename = filename

        title = decoded_filename.replace('.html', '').strip()

        # חיפוש קטגוריות XML לפי הכותרת
        xml_cats = xml_categories.get(title, [])

        # קביעת קטגוריה ותת-קטגוריה
        category, subcategory = categorize_with_xml(title, xml_cats)
        section = category

        try:
            # חשוב: קוראים מה-file_path המקורי, לא מה-filename!
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            content_div = soup.find('div', id='mw-content-text') or \
                          soup.find('div', class_='mw-parser-output') or \
                          soup.find('div', class_='mw-content-ltr') or \
                          soup.find('div', class_='mw-content-rtl') or \
                          soup.find('body')
            content = content_div.get_text(separator='\n', strip=True) if content_div else ""

            # Video ID
            video_id = None
            youtube_match = re.search(r'youtube\.com/watch\?v=([^&"\s]+)', html_content)
            if youtube_match:
                video_id = youtube_match.group(1)

            # Link count
            link_count = len(soup.find_all('a'))

            # Hub detection
            is_hub = 1 if link_count > 50 and len(content) < 2000 else 0

            url_slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

            data.append({
                'title': title,
                'filename': filename,
                'url_slug': url_slug,
                'section': section,
                'category': category,
                'subcategory': subcategory,
                'content': content,
                'content_length': len(content),
                'video_id': video_id,
                'link_count': link_count,
                'is_hub': is_hub,
                'created_date': datetime.datetime.now().isoformat()
            })

        except Exception as e:
            logging.warning(f"⚠️ שגיאה בעיבוד {filename}: {e}")
            continue

    df = pd.DataFrame(data)

    # הכנסת קטגוריות
    unique_categories = df['category'].dropna().unique()
    for cat_name in unique_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat_name,))
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        categories_dict[cat_name] = cursor.fetchone()[0]

    # הכנסת תתי-קטגוריות
    unique_subcats = df['subcategory'].dropna().unique()
    for subcat_name in unique_subcats:
        cat_name = df[df['subcategory'] == subcat_name]['category'].iloc[0] if not df[df['subcategory'] == subcat_name].empty else None
        cat_id = categories_dict.get(cat_name)
        if cat_id:
            cursor.execute("INSERT OR IGNORE INTO subcategories (name, category_id) VALUES (?, ?)", (subcat_name, cat_id))
            cursor.execute("SELECT id FROM subcategories WHERE name = ? AND category_id = ?", (subcat_name, cat_id))
            subcategories_dict[subcat_name] = cursor.fetchone()[0]

    # הכנסת מאמרים
    for _, row in df.iterrows():
        cat_id = categories_dict.get(row['category'])
        subcat_id = subcategories_dict.get(row['subcategory'])
        cursor.execute("""
            INSERT INTO articles (title, filename, url_slug, section, category_id, subcategory_id, content, content_length, video_id, link_count, is_hub, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['title'], row['filename'], row['url_slug'], row['section'], cat_id, subcat_id, row['content'], row['content_length'], row['video_id'], row['link_count'], row['is_hub'], row['created_date']))

    # עדכון מונים
    cursor.execute("UPDATE categories SET article_count = (SELECT COUNT(*) FROM articles WHERE category_id = categories.id)")
    cursor.execute("UPDATE subcategories SET article_count = (SELECT COUNT(*) FROM articles WHERE subcategory_id = subcategories.id)")

    conn.commit()

    # סטטיסטיקות
    stats = pd.read_sql_query("""
        SELECT c.name as category, COUNT(DISTINCT s.id) as subcategories_count, COUNT(a.id) as articles_count
        FROM categories c
        LEFT JOIN subcategories s ON c.id = s.category_id
        LEFT JOIN articles a ON c.id = a.category_id
        GROUP BY c.id
        ORDER BY articles_count DESC
    """, conn)
    logging.info("\n📊 סטטיסטיקות סופיות:")
    logging.info(stats.to_string(index=False))

    # בדיקת תוכן
    cursor.execute("SELECT COUNT(*) FROM articles WHERE content_length > 0")
    with_content = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]

    logging.info(f"\n✅ תוכן: {with_content}/{total} ({with_content/total*100:.1f}%)")
    logging.info(f"📁 מיקום: {db_path}")
    logging.info(f"📈 מאמרים: {len(df):,}")

    conn.close()
    return db_path

if __name__ == "__main__":
    xml_path = "backup.xml"
    folder_path = "./pages"
    db_file = create_database(folder_path, xml_path, overwrite_db=True)
