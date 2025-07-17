import os
import re

templates_dir = 'templates/pages'

def clean_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove everything outside <body> if exists
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
    if body_match:
        content = body_match.group(1)
    else:
        # Otherwise remove html/head manually
        content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)

    # Optional: remove extra blank lines
    content = '\n'.join([line.strip() for line in content.strip().splitlines() if line.strip()])

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

# Loop through all .html files in templates/pages
for filename in os.listdir(templates_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(templates_dir, filename)
        print(f"Cleaning {filename}...")
        clean_html(filepath)

print("✅ All templates cleaned!")
