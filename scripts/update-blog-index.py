#!/usr/bin/env python3
"""Synchronize the blog index with canonical articles."""

import glob
import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "trading", "blog", "index.html")
ARTICLE_GLOB = os.path.join(BASE_DIR, "trading", "blog", "*", "index.html")

MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}


def parse_date(value):
    parts = value.lower().strip().split()
    return datetime(int(parts[2]), MONTHS[parts[1]], int(parts[0]))


def extract_article(path):
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()

    if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', source, re.I):
        return None

    slug = os.path.basename(os.path.dirname(path))
    date = re.search(r'<rect width="18".*?</svg>\s*([^<]+?)\s*</span>', source, re.DOTALL)
    reading_time = re.search(r'<circle cx="12".*?</svg>\s*([^<]+?)\s*</span>', source, re.DOTALL)
    title = re.search(r'<h1>(.*?)</h1>', source, re.DOTALL)
    description = re.search(r'<meta name="description" content="(.*?)"', source)

    return {
        "url": f"/trading/blog/{slug}/",
        "date": date.group(1).strip() if date else "1 gennaio 2026",
        "time": reading_time.group(1).strip() if reading_time else "5 min di lettura",
        "title": title.group(1).strip() if title else slug,
        "desc": description.group(1).strip() if description else "",
    }


def build_card(article, featured=False):
    cls = "post-card post-card-featured reveal" if featured else "post-card reveal"
    svg_date = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/>'
        '<path d="M3 10h18"/></svg>'
    )
    svg_time = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
    )
    return (
        f'        <article class="{cls}">\n'
        f'          <div class="post-card-meta">\n'
        f'            <span>\n              {svg_date}\n              {article["date"]}\n            </span>\n'
        f'            <span>\n              {svg_time}\n              {article["time"]}\n            </span>\n'
        f'          </div>\n'
        f'          <h2><a href="{article["url"]}">{article["title"]}</a></h2>\n'
        f'          <p>{article["desc"]}</p>\n'
        f'          <a class="btn btn-outline" href="{article["url"]}">Leggi l\'articolo →</a>\n'
        f'        </article>'
    )


def main():
    articles = []
    for path in sorted(glob.glob(ARTICLE_GLOB)):
        article = extract_article(path)
        if article:
            articles.append(article)

    for article in articles:
        try:
            article["_sort"] = parse_date(article["date"])
        except (ValueError, KeyError, IndexError):
            article["_sort"] = datetime(2000, 1, 1)
    articles.sort(key=lambda item: item["_sort"], reverse=True)

    grid = ['      <div class="blog-grid">']
    grid.extend(build_card(article, featured=index == 0) for index, article in enumerate(articles))
    grid.append("      </div>")

    with open(INDEX_PATH, "r", encoding="utf-8") as handle:
        index_html = handle.read()
    old_block = re.search(
        r'^\s*<div class="blog-grid">.*?</div>\s*</div>\s*</main>',
        index_html,
        re.DOTALL | re.MULTILINE,
    )
    if not old_block:
        raise RuntimeError("Blocco blog-grid non trovato in trading/blog/index.html")

    new_block = "\n".join(grid) + "\n\n    </div>\n  </main>"
    index_html = index_html.replace(old_block.group(0), new_block)
    with open(INDEX_PATH, "w", encoding="utf-8") as handle:
        handle.write(index_html)

    gtm_missing = []
    for path in [INDEX_PATH, *sorted(glob.glob(ARTICLE_GLOB))]:
        with open(path, "r", encoding="utf-8") as handle:
            if "GTM-MCBW9JTG" not in handle.read():
                gtm_missing.append(os.path.relpath(path, BASE_DIR))

    print(f"Blog index aggiornato: {len(articles)} articoli canonici")
    if gtm_missing:
        print("WARNING: GTM mancante:")
        for path in gtm_missing:
            print(f"  - {path}")
    else:
        print("GTM presente su blog index e articoli canonici")


if __name__ == "__main__":
    main()
