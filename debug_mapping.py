#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET

# בדיקה של הקובץ הראשון
pages_dir = Path('pages')
first_file = list(pages_dir.glob('*.html'))[0]
with open('debug_output.txt', 'w', encoding='utf-8') as f:
    f.write(f'First file: {first_file.name}\n')
    f.write(f'Decoded: {unquote(first_file.name)}\n\n')

    # בדיקה מה הכותרת בXML
    tree = ET.parse('backup.xml')
    root = tree.getroot()
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    pages = root.findall('.//mw:page', ns)

    for i, page in enumerate(pages[:5]):
        title_elem = page.find('mw:title', ns)
        if title_elem is not None:
            title = title_elem.text
            filename = title + '.html'
            f.write(f'\nPage {i+1}:\n')
            f.write(f'  XML title: {title}\n')
            f.write(f'  Expected filename: {filename}\n')

    # בדיקת מיפוי
    f.write('\n\nFile mapping test:\n')
    html_files_map = {}
    for file_path in pages_dir.glob('*.html'):
        try:
            decoded_name = unquote(file_path.name)
            html_files_map[decoded_name] = file_path
        except:
            pass
        html_files_map[file_path.name] = file_path

    f.write(f'Total files mapped: {len(html_files_map)}\n')
    f.write(f'Sample mappings:\n')
    for i, (key, value) in enumerate(list(html_files_map.items())[:10]):
        f.write(f'  {key[:80]} -> {value.name[:80]}\n')

print('Output written to debug_output.txt')
