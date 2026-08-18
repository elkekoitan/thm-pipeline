import re, glob, sys, os
from bs4 import BeautifulSoup

pat = re.compile(r'https://d8j0ntlcm91z4\.cloudfront\.net/[^"\'<>\s]+\.(?:png|jpg|jpeg)')
files = sorted(glob.glob('/home/ubuntu/upload/higgsfield*.html'))
f = sys.argv[1] if len(sys.argv) > 1 else files[-1]
html = open(f, encoding='utf-8', errors='ignore').read()
soup = BeautifulSoup(html, 'html.parser')

# find img tags referencing cloudfront
found = []
for img in soup.find_all('img'):
    for attr in ('src', 'data-src', 'srcset'):
        val = img.get(attr) or ''
        for m in pat.findall(val):
            found.append(m)
# also raw html search
for m in pat.findall(html):
    found.append(m)

seen = []
for u in found:
    if u not in seen:
        seen.append(u)
print("file:", f)
print("count:", len(seen))
for u in seen:
    print(u)
