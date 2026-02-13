from flask import Flask, render_template, request, abort
import sqlite3
import re

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('aviner_database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # Fetch sections with article count
    sections = conn.execute("""
        SELECT section, COUNT(*) as article_count 
        FROM articles 
        GROUP BY section 
        ORDER BY article_count DESC
    """).fetchall()
    # Fetch top categories by article count
    categories = conn.execute("""
        SELECT name, article_count 
        FROM categories 
        ORDER BY article_count DESC 
        LIMIT 15
    """).fetchall()
    conn.close()
    return render_template('index.html', sections=sections, categories=categories)

@app.route('/section/<section_name>')
def section(section_name):
    conn = get_db_connection()
    articles = conn.execute("""
        SELECT title, url_slug, section 
        FROM articles 
        WHERE section = ? 
        LIMIT 100
    """, (section_name,)).fetchall()
    conn.close()
    return render_template('category.html', articles=articles, cat_name=section_name)

@app.route('/category/<cat_name>')
def category(cat_name):
    conn = get_db_connection()
    articles = conn.execute("""
        SELECT a.title, a.url_slug FROM articles a
        JOIN categories c ON a.category_id = c.id
        WHERE c.name = ?
    """, (cat_name,)).fetchall()
    conn.close()
    return render_template('category.html', articles=articles, cat_name=cat_name)

@app.route('/article/<slug>')
def article(slug):
    conn = get_db_connection()
    page = conn.execute("SELECT title, content, video_id FROM articles WHERE url_slug = ?", (slug,)).fetchone()
    conn.close()
    if page is None:
        abort(404)
    return render_template('article.html', title=page['title'], content=page['content'], video_id=page['video_id'])

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=[], query='')
    
    conn = get_db_connection()
    # Advanced search using FTS5
    results = conn.execute("""
        SELECT title, url_slug FROM articles 
        JOIN articles_fts ON articles.id = articles_fts.rowid
        WHERE articles_fts MATCH ? 
        ORDER BY rank
        LIMIT 50
    """, (query,)).fetchall()
    
    # Fallback to LIKE if FTS5 query is invalid (e.g. empty or special chars)
    if not results:
        results = conn.execute("""
            SELECT title, url_slug FROM articles 
            WHERE title LIKE ? OR content LIKE ? 
            LIMIT 50
        """, (f"%{query}%", f"%{query}%")).fetchall()
        
    conn.close()
    return render_template('search.html', results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
