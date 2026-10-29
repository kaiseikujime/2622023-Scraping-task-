import csv
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

START_URL = "https://www.musashino-u.ac.jp/"
DOMAIN = urlparse(START_URL).netloc
SLEEP_SEC = 1
MAX_PAGES = 1000  # 暴走防止の上限。必要に応じて変更
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# robots.txt の指示を確認する(授業資料の注意事項)
rp = RobotFileParser(urljoin(START_URL, "/robots.txt"))
time.sleep(SLEEP_SEC)
rp.read()

sitemap = {}  # key: URL, value: <title></title>で挟まれた文字列
visited = set()
queue = deque([START_URL])

while queue and len(sitemap) < MAX_PAGES:
    url = queue.popleft()
    if url in visited or not rp.can_fetch("*", url):
        continue
    visited.add(url)

    time.sleep(SLEEP_SEC)  # アクセスの前に必ず待つ
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        print("ERROR", url, e)
        continue

    # HTML以外(PDF・画像など)は対象外
    if "text/html" not in res.headers.get("Content-Type", ""):
        continue

    html_soup = BeautifulSoup(res.content, "html.parser")
    title = html_soup.title.string.strip() if html_soup.title and html_soup.title.string else ""
    sitemap[url] = title
    print(len(sitemap), url, title)

    for a in html_soup.find_all("a", href=True):
        link, _ = urldefrag(urljoin(url, a["href"]))  # 相対→絶対、#以降は除去
        p = urlparse(link)
        if p.scheme in ("http", "https") and p.netloc == DOMAIN and link not in visited:
            queue.append(link)

with open("sitemap.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["url", "title"])
    writer.writerows(sitemap.items())
