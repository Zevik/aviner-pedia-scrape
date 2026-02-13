# Aviner Pedia Scrape

אתר וויקי לתכני הרב אבינר - סקרייפ ממקורות שונים באינטרנט.

## תיאור

פרויקט זה כולל:
- סקריפט Python שאוסף תכנים מאתרי הרב אבינר
- מסד נתונים SQLite עם כל התכנים
- אפליקציית Flask לצפייה ונווט בתכנים

## תכונות

- **חיפוש מתקדם** - חיפוש full-text באמצעות FTS5
- **ארגון לפי קטגוריות** - סידור התכנים לפי סוגים ונושאים
- **ממשק נוח** - ממשק משתמש עברי וידידותי
- **תמיכה בסוגי תוכן שונים** - מאמרים, שאלות ותשובות, סדרות וידאו

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

3. הרץ את האפליקציה:
```bash
python app.py
```

4. פתח דפדפן וגש ל: http://127.0.0.1:5000

## מבנה הפרויקט

```
.
├── app.py              # אפליקציית Flask ראשית
├── build.py            # סקריפט לבניית מסד הנתונים
├── aviner_database.db  # מסד נתונים (לא נמצא ב-git)
├── pages/              # קבצי HTML מקוריים
├── templates/          # תבניות Flask
├── static/             # קבצי CSS/JS/תמונות
└── requirements.txt    # תלויות Python
```

## טכנולוגיות

- **Backend**: Python, Flask
- **Database**: SQLite with FTS5
- **Frontend**: HTML, CSS, JavaScript
- **Scraping**: BeautifulSoup4, Pandas

## רישיון

פרויקט זה נועד לשימוש חינוכי ומחקרי בלבד. כל הזכויות על התוכן המקורי שייכות לרב שלמה אבינר.
