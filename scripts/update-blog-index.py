#!/usr/bin/env python3
"""
Aggiorna trading/blog/index.html raccogliendo tutti gli articoli presenti in:
  - blog/*.html
  - trading/blog/*/index.html (esclude index.html, style.css, template-post.html)

Uso:
  python3 scripts/update-blog-index.py
"""
import re
import os
import glob
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "trading", "blog", "index.html")

MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12
}


def parse_date(s):
    parts = s.lower().strip().split()
    day = int(parts[0])
    month = MONTHS[parts[1]]
    year = int(parts[2])
    return datetime(year, month, day)


def extract_from_blog_file(path):
    """Estrae metadati da un file HTML in blog/*.html"""
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    date = re.search(r'<rect width="18".*?</svg>\s*([^<]+?)\s*</span>', s, re.DOTALL)
    time = re.search(r'<circle cx="12".*?</svg>\s*([^<]+?)\s*</span>', s, re.DOTALL)
    title = re.search(r'<h1>(.*?)</h1>', s, re.DOTALL)
    desc = re.search(r'<meta name="description" content="(.*?)"', s)
    return {
        "url": "/blog/" + os.path.basename(path),
        "date": date.group(1).strip() if date else "1 gennaio 2026",
        "time": time.group(1).strip() if time else "5 min di lettura",
        "title": title.group(1).strip() if title else os.path.basename(path),
        "desc": desc.group(1).strip() if desc else "",
    }


def extract_from_index(path):
    """Estrae le card già presenti in trading/blog/index.html"""
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    cards = re.findall(r'<article class="post-card[^"]*">(.*?)</article>', s, re.DOTALL)
    results = []
    for c in cards:
        url = re.search(r'href="([^"]+)"', c)
        date = re.search(r'<rect width="18".*?</svg>\s*([^<]+?)\s*</span>', c, re.DOTALL)
        time = re.search(r'<circle cx="12".*?</svg>\s*([^<]+?)\s*</span>', c, re.DOTALL)
        title = re.search(r'<h2><a href="[^"]+">(.*?)</a></h2>', c, re.DOTALL)
        desc = re.search(r'<p>(.*?)</p>\s*<a class="btn', c, re.DOTALL)
        if url:
            results.append({
                "url": url.group(1),
                "date": date.group(1).strip() if date else "1 gennaio 2026",
                "time": time.group(1).strip() if time else "5 min di lettura",
                "title": title.group(1).strip() if title else "",
                "desc": desc.group(1).strip() if desc else "",
            })
    return results


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
        f'            <span>\n'
        f'              {svg_date}\n'
        f'              {article["date"]}\n'
        f'            </span>\n'
        f'            <span>\n'
        f'              {svg_time}\n'
        f'              {article["time"]}\n'
        f'            </span>\n'
        f'          </div>\n'
        f'          <h2><a href="{article["url"]}">{article["title"]}</a></h2>\n'
        f'          <p>{article["desc"]}</p>\n'
        f'          <a class="btn btn-outline" href="{article["url"]}">Leggi l\'articolo →</a>\n'
        f'        </article>'
    )


def main():
    # 1. Leggi card esistenti (trading/blog/)
    existing = extract_from_index(INDEX_PATH)
    existing_basenames = {os.path.basename(a["url"].rstrip("/")) for a in existing}

    # 2. Scansiona blog/*.html
    new_articles = []
    for p in sorted(glob.glob(os.path.join(BASE_DIR, "blog", "*.html"))):
        bn = os.path.basename(p)
        if bn not in existing_basenames:
            new_articles.append(extract_from_blog_file(p))

    # 3. Unisci e ordina per data decrescente
    all_articles = new_articles + existing
    for a in all_articles:
        try:
            a["_sort"] = parse_date(a["date"])
        except Exception:
            a["_sort"] = datetime(2000, 1, 1)
    all_articles.sort(key=lambda x: x["_sort"], reverse=True)

    # 4. Costruisci la grid
    grid_lines = ['      <div class="blog-grid">']
    for i, a in enumerate(all_articles):
        grid_lines.append(build_card(a, featured=(i == 0)))
    grid_lines.append("      </div>")
    grid_html = "\n".join(grid_lines)

    # 5. Sostituisci nel file index
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index_html = f.read()

    old_block = re.search(
        r'<div class="blog-grid">.*?</div>\s*</div>\s*</main>',
        index_html,
        re.DOTALL,
    )
    if not old_block:
        print("ERRORE: blocco blog-grid non trovato in index.html")
        return

    new_block = grid_html + "\n\n    </div>\n  </main>"
    index_html = index_html.replace(old_block.group(0), new_block)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"✅ Blog index aggiornato: {INDEX_PATH}")
    print(f"   Articoli trovati: {len(all_articles)}")

    # 6. Verifica GTM su tutte le pagine HTML
    gtm_missing = []
    for html_path in glob.glob(os.path.join(BASE_DIR, "**", "*.html"), recursive=True):
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "GTM-MCBW9JTG" not in content:
            rel = os.path.relpath(html_path, BASE_DIR)
            gtm_missing.append(rel)

    if gtm_missing:
        print("\n⚠️  WARNING: GTM mancante nelle seguenti pagine:")
        for p in gtm_missing:
            print(f"   - {p}")
        print("   → Ricorda di inserire gli snippet GTM in <head> e subito dopo <body>.\n")
    else:
        print("   ✅ GTM presente su tutte le pagine.")


if __name__ == "__main__":
    main()
