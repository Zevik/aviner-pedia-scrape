#!/usr/bin/env python3
# aviner_database_builder_improved.py
# יוצר דאטה בייס מאורגן מ-7500 קבצי HTML של אתר אבינרפדיה (גרסה משופרת)
import os
import re
import sqlite3
from pathlib import Path
from collections import defaultdict
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_aviner_database(html_folder_path, overwrite_db=False):
    """יוצר דאטה בייס SQLite מאורגן מ-7500 קבצי HTML"""
    logging.info("🚀 מתחיל בניית דאטה בייס אבינרפדיה...")
    
    db_path = 'aviner_database.db'
    if overwrite_db and os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
    logging.info("✅ טבלאות נוצרו/עודכנו")
    
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
        title = filename.replace('.html', '').strip()
        category, subcategory = parse_filename(filename)
        
        # Extract Section (Main Category) from filename - looking inside parentheses
        section = 'כללי'
        # Check for content in parentheses first
        paren_match = re.search(r'\(([^)]+)\)', filename)
        if paren_match:
            paren_content = paren_match.group(1)
            if 'וידאו' in paren_content:
                section = 'וידאו'
            elif 'מאמר' in paren_content:
                section = 'מאמרים'
            elif 'שו"ת' in paren_content or 'שו_ת' in paren_content:
                section = 'שו"ת'
            elif 'סדרה' in paren_content:
                section = 'סדרות'
        # Fallback to checking entire filename if no parentheses found
        elif 'וידאו' in filename:
            section = 'וידאו'
        elif 'מאמר' in filename:
            section = 'מאמרים'
        elif 'שו"ת' in filename or 'שו_ת' in filename:
            section = 'שו"ת'
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            content_div = soup.find('div', id='mw-content-text') or \
                          soup.find('div', class_='mw-parser-output') or \
                          soup.find('div', class_='mw-content-ltr') or \
                          soup.find('div', class_='mw-content-rtl') or \
                          soup.find('body') or \
                          soup
            content = content_div.get_text(separator='\n', strip=True) if content_div else ""
            
            # Extract Video ID if exists
            video_iframe = soup.find('iframe', src=re.compile(r'youtube|embed'))
            video_id = None
            if video_iframe:
                src = video_iframe.get('src', '')
                vid_match = re.search(r'embed/([^/?]+)', src)
                if vid_match:
                    video_id = vid_match.group(1)

            # Count internal links (links to other .html files, excluding fragments)
            all_links = soup.find_all('a', href=True)
            link_count = 0
            for link in all_links:
                href = link.get('href', '')
                if not href.startswith('http') and not href.startswith('#'):
                    link_count += 1
            
            # User defined threshold: > 5 links. 
            # Also user explicitly requested to exclude Q&A index pages from being hubs.
            # Catching both "שו"ת" and "שו_ת" variants.
            is_hub = 1 if (link_count > 5 and 'שו"ת' not in title and 'שו_ת' not in title) else 0

            # Manual Patch for known missing videos (e.g. from Machon Meir links that don't auto-resolve)
            if "L'éthique de l'amour 12" in title:
                video_id = "VtBZSwrdM5A"

            created_date = datetime.datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logging.warning(f"⚠️ שגיאה בעיבוד {filename}: {e}")
            content = ""
            video_id = None
            link_count = 0
            is_hub = 0
            created_date = ""
        
        data.append({
            'title': title,
            'filename': filename,
            'url_slug': re.sub(r'[^a-zA-Z0-9_-]', '_', title),  # ניקוי טוב יותר
            'section': section,
            'category': category,
            'subcategory': subcategory,
            'content': content,
            'content_length': len(content),
            'video_id': video_id,
            'link_count': link_count,
            'is_hub': is_hub,
            'created_date': created_date
        })
    
    df = pd.DataFrame(data)
    
    unique_categories = df['category'].dropna().unique()
    for cat_name in unique_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat_name,))
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        categories_dict[cat_name] = cursor.fetchone()[0]
    
    unique_subcats = df['subcategory'].dropna().unique()
    for subcat_name in unique_subcats:
        cat_name = df[df['subcategory'] == subcat_name]['category'].iloc[0] if not df[df['subcategory'] == subcat_name].empty else None
        cat_id = categories_dict.get(cat_name)
        if cat_id:
            cursor.execute("INSERT OR IGNORE INTO subcategories (name, category_id) VALUES (?, ?)", (subcat_name, cat_id))
            cursor.execute("SELECT id FROM subcategories WHERE name = ? AND category_id = ?", (subcat_name, cat_id))
            subcategories_dict[subcat_name] = cursor.fetchone()[0]
    
    for _, row in df.iterrows():
        cat_id = categories_dict.get(row['category'])
        subcat_id = subcategories_dict.get(row['subcategory'])
        cursor.execute("""
            INSERT INTO articles (title, filename, url_slug, section, category_id, subcategory_id, content, content_length, video_id, link_count, is_hub, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['title'], row['filename'], row['url_slug'], row['section'], cat_id, subcat_id, row['content'], row['content_length'], row['video_id'], row['link_count'], row['is_hub'], row['created_date']))
    
    cursor.execute("UPDATE categories SET article_count = (SELECT COUNT(*) FROM articles WHERE category_id = categories.id)")
    cursor.execute("UPDATE subcategories SET article_count = (SELECT COUNT(*) FROM articles WHERE subcategory_id = subcategories.id)")
    
    conn.commit()
    
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
    logging.info(f"\n🎉 דאטה בייס הושלם!")
    logging.info(f"📁 מיקום: {db_path}")
    logging.info(f"📈 מאמרים: {len(df):,}")
    logging.info(f"📂 קטגוריות: {len(unique_categories)}")
    
    conn.close()
    return db_path

def parse_filename(filename):
    """חולץ קטגוריה ותת-קטגוריה משם קובץ (משופר עם regex)"""
    category_patterns = {
        # סדרות ספרים - בסדר חשיבות (מהספציפי לכללי)
        'אורות הקודש': r'אורות\s+הקודש',
        'אורות התשובה': r'אורות\s+התשובה',
        'ספר אורות': r'ספר\s+אורות',
        'אורות': r'אורות(?!\s+הקודש|\s+התשובה)',  # אורות שאינו הקודש/התשובה
        'עין איה': r'עין\s+איה',
        'כוזרי': r'כוזרי',
        'שמונה פרקים לרמבם': r'שמונה\s+פרקים|רמב"?ם',
        'תפארת ישראל - מהר"ל': r'תפארת\s+ישראל|מהר"?ל',
        'נתיב התורה': r'נתיב\s+התורה',
        # ערוצים ופלטפורמות
        'ספריית חוה': r'ספריית\s+חוה',
        'כי מציון': r'כי\s+מציון',
        'בלוג הוידאו של הרב אבינר': r'בלוג\s+הוידאו|בלוג.*וידאו',
        'ישיבת עטרת ירושלים': r'עטרת\s+ירושלים|ישיבת\s+עטרת',
        'מאמרי הרב שלמה אבינר': r'מאמרי\s+הרב|שלמה\s+אבינר',
        'ערוץ מאיר': r'ערוץ\s+מאיר',
        # קטגוריות הלכתיות
        'אבן העזר': r'אבן\s+העזר',
        'אורח חיים': r'אורח\s+חיים',
        'יורה דעה': r'יורה\s+דעה|יורה_דעה',
        'חושן משפט': r'חושן\s+משפט|חושן_משפט',
        'הלכה': r'הלכה',
        'שו"ת': r'שו"?ת',
        'מאמרים': r'מאמרים',
        # נושאים כלליים
        'אמונה': r'אמונה',
        'זוגיות': r'זוגיות|משפחה',
        'חינוך': r'חינוך',
        'מדינה': r'מדינה|ציונות|צבא|ארץ\s+ישראל',
        'מוסר': r'מוסר|מידות',
        'מועדים': r'מועדים|חגים|שבת|פסח|סוכות'
    }
    filename_clean = filename.replace('.html', '').strip()
    
    for category, pattern in category_patterns.items():
        if re.search(pattern, filename_clean, re.IGNORECASE):
            parts = re.split(r'\s*-\s*|\s*\(\s*|\s*\)\s*', filename_clean)
            subcategory = parts[-1].strip() if len(parts) > 1 else 'כללי'
            return category, subcategory
    
    return 'כללי', 'כללי'

if __name__ == "__main__":
    folder_path = "./pages"  # ← Updated to the new sub-folder
    db_file = create_aviner_database(folder_path, overwrite_db=True)
    print(f"\n✅ ניתן להריץ שאילתות על: {db_file}")