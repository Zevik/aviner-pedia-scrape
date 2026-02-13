from bs4 import BeautifulSoup
import os

file_path = r'c:\Users\Zevik\Downloads\נסיון חילוץ אבינר פדיה פרפלקסיטי\pages - Copy\pages\10 עובדות על רפורמים (מאמר).html'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Current logic in build.py
    content_div = soup.find('div', id='mw-content-text') or soup.find('body')
    content = content_div.get_text(separator='\n', strip=True) if content_div else "NONE FOUND"
    
    print(f"--- CURRENT LOGIC ---\n{content[:200]}...\n")
    
    # Better logic
    better_div = soup.find('div', id='mw-content-text') or \
                 soup.find('div', class_='mw-parser-output') or \
                 soup.find('div', class_='mw-content-ltr') or \
                 soup.find('div', class_='mw-content-rtl') or \
                 soup.find('body') or \
                 soup
    
    better_content = better_div.get_text(separator='\n', strip=True)
    print(f"--- BETTER LOGIC ---\n{better_content[:200]}...\n")
else:
    print("File not found")
