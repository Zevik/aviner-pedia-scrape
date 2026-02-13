# Aviner Pedia Scrape

אתר וויקי לתכני הרב אבינר - סקרייפ ממקורות שונים באינטרנט.

## תיאור

פרויקט זה כולל:
- סקריפט Python שאוסף תכנים מאתרי הרב אבינר
- מסד נתונים SQLite עם כל התכנים
- אפליקציית Flask לצפייה ונווט בתכנים

## תכונות

- **בניה מקובץ XML** - חילוץ אוטומטי של כל המטאדאטה מקובץ backup.xml של MediaWiki
- **חיפוש מתקדם** - חיפוש full-text באמצעות FTS5 ואוטומטי השלמה
- **ארגון לפי קטגוריות** - סידור התכנים לפי סוגים ונושאים (וידאו, מאמרים, שו"ת, סדרות)
- **ניווט היררכי** - דף בית → קטגוריה → תת-קטגוריה → מאמרים
- **ממשק נוח** - ממשק משתמש עברי וידידותי עם breadcrumbs
- **תמיכה בסוגי תוכן שונים** - מאמרים, שאלות ותשובות, סדרות וידאו
- **7,864 מאמרים** בסך הכל:
  - שו"ת הלכה: 915 מאמרים עם 11 תתי-קטגוריות
  - וידאו: 1,267 מאמרים עם 11 תתי-קטגוריות
  - מאמרים: 2,346 מאמרים עם 13 תתי-קטגוריות
  - סדרות: 438 מאמרים עם 7 תתי-קטגוריות

## התקנה

1. שכפל את הריפו:
```bash
git clone https://github.com/Zevik/aviner-pedia-scrape.git
cd aviner-pedia-scrape
```

2. צור סביבה וירטואלית והתקן תלויות:
```bash
python -m venv .venv
source .venv/bin/activate  # בלינוקס/מק
# או
.venv\Scripts\activate  # בווינדוס

pip install -r requirements.txt
```

3. בנה את מסד הנתונים (אם עדיין לא קיים):
```bash
python build_from_xml.py
```

4. הרץ את האפליקציה:
```bash
python app.py
```

5. פתח דפדפן וגש ל: http://127.0.0.1:5000

## מבנה הפרויקט

```
.
├── app.py                  # אפליקציית Flask ראשית
├── build.py                # סקריפט ישן לבניית מסד נתונים מ-regex
├── build_from_xml.py       # סקריפט חדש - בונה DB מקובץ backup.xml ✨
├── sheut_mappings.py       # מיפוי ידני של שאלות ותשובות לתתי-קטגוריות
├── backup.xml              # גיבוי MediaWiki XML עם כל המטאדאטה
├── aviner_database.db      # מסד נתונים (נוצר אוטומטית)
├── pages/                  # קבצי HTML מקוריים (7,166 קבצים)
├── templates/              # תבניות Flask
│   ├── base.html           # תבנית בסיס עם חיפוש אוטומטי השלמה
│   ├── home.html           # דף הבית עם כרטיסי קטגוריות
│   ├── section.html        # דף קטגוריה עם תתי-קטגוריות
│   ├── category.html       # דף תת-קטגוריה עם רשימת מאמרים
│   └── article.html        # דף מאמר עם breadcrumbs
└── requirements.txt        # תלויות Python
```

## טכנולוגיות

- **Backend**: Python, Flask
- **Database**: SQLite with FTS5
- **Frontend**: HTML, CSS, JavaScript
- **Scraping**: BeautifulSoup4, Pandas

## רישיון

פרויקט זה נועד לשימוש חינוכי ומחקרי בלבד. כל הזכויות על התוכן המקורי שייכות לרב שלמה אבינר.
