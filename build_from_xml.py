#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה דאטה-בייס מקובץ backup.xml של MediaWiki
"""

import re
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_categories(wikitext):
    """
    חולץ קטגוריות מטקסט ויקי
    """
    categories = []
    # Pattern: [[קטגוריה:שם_קטגוריה]] או [[Category:שם]]
    cat_pattern = r'\[\[(?:קטגוריה|Category):([^\]|]+)(?:\|[^\]]*)?\]\]'
    matches = re.finditer(cat_pattern, wikitext, re.IGNORECASE)
    for match in matches:
        cat_name = match.group(1).strip()
        categories.append(cat_name)
    return categories

def extract_video_id(wikitext):
    """
    חולץ YouTube video ID מטקסט ויקי
    """
    # Pattern: <youtube>VIDEO_ID</youtube>
    video_pattern = r'<youtube>([^<]+)</youtube>'
    match = re.search(video_pattern, wikitext)
    if match:
        return match.group(1).strip()
    return None

def categorize_article(title, categories):
    """
    קובע את הקטגוריה הראשית ותת-הקטגוריה על פי הכותרת והקטגוריות
    """
    title_lower = title.lower()

    # קביעת קטגוריה ראשית לפי הסוגריים בכותרת
    main_category = 'כללי'
    subcategory = 'כללי'

    if '(וידאו)' in title or '(שיעור)' in title:
        main_category = 'וידאו'
    elif '(מאמר)' in title:
        main_category = 'מאמרים'
    elif '(שו"ת)' in title or '(שו_ת)' in title:
        main_category = 'שו"ת הלכה'
    elif '(סדרה)' in title:
        main_category = 'סדרות'

    # קביעת תת-קטגוריה לפי הקטגוריות מהוויקי
    # סדר עדיפויות: קטגוריות ספציפיות קודם

    priority_categories = {
        # סדרות (בדיקה ראשונה - הכי ספציפי)
        'אורות הקודש': 'אורות הקודש',
        'אורות התשובה': 'אורות התשובה',
        'ספר אורות': 'ספר אורות',
        'עין איה': 'עין איה',
        'כוזרי': 'כוזרי',
        'שמונה פרקים': 'שמונה פרקים לרמבם',
        'תפארת ישראל': 'תפארת ישראל - מהר"ל',

        # נושאים מיוחדים (בעדיפות גבוהה)
        'שו"ת סמס': 'שו"ת סמס',
        'אקטואליה': 'אקטואליה',

        # נושאים לשו"ת (עדיפות על פני "שו"ת" כללי)
        'זוגיות ומשפחה': 'זוגיות ומשפחה',
        'זוגיות': 'זוגיות ומשפחה',
        'משפחה': 'זוגיות ומשפחה',
        'נישואין': 'זוגיות ומשפחה',
        'חתונה': 'זוגיות ומשפחה',
        'שידוכים': 'זוגיות ומשפחה',

        'מדינת ישראל': 'מדינת ישראל',
        'ארץ ישראל': 'מדינת ישראל',
        'צה"ל': 'מדינת ישראל',
        'צבא': 'מדינת ישראל',

        'מוסר ומידות': 'מוסר ומידות',
        'מוסר': 'מוסר ומידות',
        'מידות': 'מוסר ומידות',

        'מועדים': 'מועדים',
        'חגים': 'מועדים',
        'שבת': 'מועדים',
        'פסח': 'מועדים',
        'סוכות': 'מועדים',
        'חנוכה': 'מועדים',
        'פורים': 'מועדים',
        'ראש השנה': 'מועדים',
        'יום כיפור': 'מועדים',

        'תפילה': 'תפילה',
        'תפילות': 'תפילה',
        'ברכות': 'תפילה',

        'תורה': 'תורה',
        'לימוד תורה': 'תורה',
        'תלמוד תורה': 'תורה',

        'חינוך': 'חינוך',

        'אמונה': 'אמונה',
        'אמונה ובטחון': 'אמונה',

        'מיוחדים': 'מיוחדים',

        # הלכה - רק אם לא מצאנו יותר ספציפי
        'הלכה': 'הלכה',

        # אורות - רק בסוף (הכי כללי)
        'אורות': 'אורות',
    }

    # חיפוש תת-קטגוריה לפי סדר עדיפויות
    # עוברים על סדר העדיפויות (מהספציפי לכללי)
    for key, value in priority_categories.items():
        # בודקים אם המפתח מופיע באחת מהקטגוריות
        for cat in categories:
            cat_lower = cat.lower()
            if key.lower() in cat_lower:
                subcategory = value
                break
        if subcategory != 'כללי':
            break

    # אם זו סדרה, נחפש את שם הסדרה בכותרת
    if main_category == 'סדרות':
        if 'אורות הקודש' in title:
            subcategory = 'אורות הקודש'
        elif 'אורות התשובה' in title:
            subcategory = 'אורות התשובה'
        elif 'אורות' in title:
            subcategory = 'אורות'
        elif 'עין איה' in title:
            subcategory = 'עין איה'
        elif 'כוזרי' in title:
            subcategory = 'כוזרי'

    return main_category, subcategory

def build_database_from_xml(xml_path, pages_folder, db_path='aviner_database.db'):
    """
    בונה דאטה-בייס מקובץ XML
    """
    logging.info("🚀 מתחיל בניית דאטה בייס מ-XML...")

    # מחיקת DB קיים
    if Path(db_path).exists():
        Path(db_path).unlink()

    # יצירת חיבור ל-DB
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
        wiki_categories TEXT,
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

    # Parse XML
    logging.info("📖 קורא קובץ XML...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # MediaWiki namespace
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}

    # יצירת מיפוי של קבצי HTML - מקודדים ולא מקודדים
    logging.info("🗂️ יוצר מיפוי של קבצי HTML...")
    from urllib.parse import unquote
    html_files_map = {}
    pages_dir = Path(pages_folder)
    for file_path in pages_dir.glob('*.html'):
        # נסיון לפענח את שם הקובץ
        try:
            decoded_name = unquote(file_path.name)
            html_files_map[decoded_name] = file_path
        except:
            pass
        # גם שם לא מקודד
        html_files_map[file_path.name] = file_path
    logging.info(f"📁 נמצאו {len(html_files_map)} קבצי HTML")

    # אוספים מידע על קטגוריות ותתי-קטגוריות
    categories_dict = {}
    subcategories_dict = {}

    pages = root.findall('.//mw:page', ns)
    logging.info(f"📄 נמצאו {len(pages)} עמודים ב-XML")

    articles_data = []
    processed = 0

    for page in pages:
        title_elem = page.find('mw:title', ns)
        if title_elem is None:
            continue

        title = title_elem.text

        # מדלגים על עמודי מערכת
        if title.startswith('קטגוריה:') or title.startswith('Category:') or \
           title.startswith('תבנית:') or title.startswith('Template:') or \
           title.startswith('מדיה ויקי:') or title.startswith('MediaWiki:'):
            continue

        # מוצאים את הגרסה האחרונה
        revisions = page.findall('mw:revision', ns)
        if not revisions:
            continue

        latest_revision = revisions[-1]  # הגרסה האחרונה

        text_elem = latest_revision.find('.//mw:text', ns)
        if text_elem is None or text_elem.text is None:
            continue

        wikitext = text_elem.text

        # חילוץ קטגוריות
        wiki_categories = extract_categories(wikitext)

        # חילוץ video ID
        video_id = extract_video_id(wikitext)

        # קביעת קטגוריה ראשית ותת-קטגוריה
        main_category, subcategory = categorize_article(title, wiki_categories)

        # יצירת filename מהכותרת
        filename = title + '.html'
        url_slug = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')

        # קריאת תוכן מקובץ HTML אם קיים
        content = ""
        content_length = 0

        # חיפוש הקובץ במיפוי - נסיון 1: שם מדויק
        html_path = html_files_map.get(filename)

        # נסיון 2: חיפוש גמיש - הכותרת עם סוגריים
        if not html_path or not html_path.exists():
            # ננסה למצוא קובץ שמתחיל בכותרת הזאת
            title_without_ext = title
            for mapped_filename, mapped_path in html_files_map.items():
                if mapped_filename.startswith(title_without_ext):
                    html_path = mapped_path
                    break

        if html_path and html_path.exists():
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                soup = BeautifulSoup(html_content, 'html.parser')
                content_div = soup.find('div', id='mw-content-text')
                if content_div:
                    content = content_div.get_text(separator='\n', strip=True)
                    content_length = len(content)
            except Exception as e:
                pass  # התעלמות משגיאות קריאה

        articles_data.append({
            'title': title,
            'filename': filename,
            'url_slug': url_slug,
            'section': main_category,
            'category': main_category,
            'subcategory': subcategory,
            'content': content,
            'content_length': content_length,
            'video_id': video_id,
            'wiki_categories': ', '.join(wiki_categories),
            'created_date': latest_revision.find('mw:timestamp', ns).text if latest_revision.find('mw:timestamp', ns) is not None else None
        })

        processed += 1
        if processed % 500 == 0:
            logging.info(f"🔄 עיבוד עמוד {processed}/{len(pages)}")

    logging.info(f"✅ עובדו {processed} עמודים")

    # הכנסת קטגוריות
    unique_categories = set(article['category'] for article in articles_data)
    for cat_name in unique_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat_name,))
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        categories_dict[cat_name] = cursor.fetchone()[0]

    # הכנסת תתי-קטגוריות
    unique_subcats = set((article['subcategory'], article['category']) for article in articles_data)
    for subcat_name, cat_name in unique_subcats:
        cat_id = categories_dict.get(cat_name)
        if cat_id:
            cursor.execute("INSERT OR IGNORE INTO subcategories (name, category_id) VALUES (?, ?)", (subcat_name, cat_id))
            cursor.execute("SELECT id FROM subcategories WHERE name = ? AND category_id = ?", (subcat_name, cat_id))
            result = cursor.fetchone()
            if result:
                subcategories_dict[(subcat_name, cat_name)] = result[0]

    # הכנסת מאמרים
    for article in articles_data:
        cat_id = categories_dict.get(article['category'])
        subcat_id = subcategories_dict.get((article['subcategory'], article['category']))

        try:
            cursor.execute("""
                INSERT INTO articles (title, filename, url_slug, section, category_id, subcategory_id,
                                    content, content_length, video_id, wiki_categories, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (article['title'], article['filename'], article['url_slug'], article['section'],
                  cat_id, subcat_id, article['content'], article['content_length'],
                  article['video_id'], article['wiki_categories'], article['created_date']))
        except sqlite3.IntegrityError:
            # כותרת כפולה - מדלגים
            pass

    # עדכון מונים
    cursor.execute("UPDATE categories SET article_count = (SELECT COUNT(*) FROM articles WHERE category_id = categories.id)")
    cursor.execute("UPDATE subcategories SET article_count = (SELECT COUNT(*) FROM articles WHERE subcategory_id = subcategories.id)")

    conn.commit()

    # סטטיסטיקות
    logging.info("\n📊 סטטיסטיקות סופיות:")
    cursor.execute("""
        SELECT c.name as category, COUNT(DISTINCT s.id) as subcategories_count, COUNT(a.id) as articles_count
        FROM categories c
        LEFT JOIN subcategories s ON c.id = s.category_id
        LEFT JOIN articles a ON c.id = a.category_id
        GROUP BY c.id
        ORDER BY articles_count DESC
    """)

    for row in cursor.fetchall():
        logging.info(f"  {row[0]}: {row[2]} מאמרים, {row[1]} תתי-קטגוריות")

    total_articles = cursor.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    logging.info(f"\n🎉 דאטה בייס הושלם!")
    logging.info(f"📁 מיקום: {db_path}")
    logging.info(f"📈 סה\"כ מאמרים: {total_articles:,}")

    conn.close()
    return db_path

if __name__ == "__main__":
    xml_path = "backup.xml"
    pages_folder = "./pages"
    db_file = build_database_from_xml(xml_path, pages_folder)
