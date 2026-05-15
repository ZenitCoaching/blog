#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

BASE_URL = "https://zenitcoach.com"
ROOT = pathlib.Path(__file__).resolve().parents[1]

EXCLUDED_PREFIXES = (
    ".git/",
    ".github/",
    "assets/",
    "scripts/",
    "blog/",
    "internooooooo/",
    "pagina-nuova-modificata/",
    "tg-redirect/",
)

EXCLUDED_FILES = {
    "AGENTS.md",
    "CNAME",
    "trading/blog/style.css",
    "trading/blog/template-post.html",
    "trading/blog/come-diventare-trader-professionista/index-pietra.html",
}

PRIORITY = {
    "/": "1.0",
    "/corsi-di-trading/": "0.9",
    "/zeta-club/": "0.9",
    "/affiliazioni-zenit/": "0.8",
    "/chi-siamo/": "0.7",
    "/trading/blog/": "0.8",
}

CHANGEFREQ = {
    "/": "weekly",
    "/trading/blog/": "weekly",
}


def posix(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_excluded(rel: str) -> bool:
    return rel in EXCLUDED_FILES or any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def page_url(rel: str) -> str | None:
    if not rel.endswith("index.html"):
        return None
    directory = rel[: -len("index.html")]
    if directory == "":
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{directory}"


def has_noindex(text: str) -> bool:
    match = re.search(r'<meta[^>]+name=["\\']robots["\\'][^>]+content=["\\']([^"\\']+)["\\']', text, re.I)
    return bool(match and "noindex" in match.group(1).lower())


def canonical(text: str) -> str | None:
    match = re.search(r'<link[^>]+rel=["\\']canonical["\\'][^>]+href=["\\']([^"\\']+)["\\']', text, re.I)
    return html.unescape(match.group(1)) if match else None


def lastmod(rel: str) -> str:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "--", rel],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return out[:10]
    except Exception:
        pass
    return dt.date.today().isoformat()


def collect_urls() -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for file_path in sorted(ROOT.rglob("*.html")):
        rel = posix(file_path)
        if is_excluded(rel):
            continue
        url = page_url(rel)
        if not url:
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if has_noindex(text):
            continue
        declared = canonical(text)
        if declared and declared.rstrip("/") != url.rstrip("/"):
            continue
        urls.append((url, rel))
    return urls


def write_sitemap(urls: list[tuple[str, str]]) -> None:
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url, rel in urls:
        path = "/" + url.removeprefix(BASE_URL).lstrip("/")
        node = ET.SubElement(root, "url")
        ET.SubElement(node, "loc").text = url
        ET.SubElement(node, "lastmod").text = lastmod(rel)
        ET.SubElement(node, "changefreq").text = CHANGEFREQ.get(path, "monthly")
        ET.SubElement(node, "priority").text = PRIORITY.get(path, "0.6" if path.startswith("/trading/blog/") else "0.5")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )


def main() -> None:
    urls = collect_urls()
    write_sitemap(urls)
    write_robots()
    print(f"Generated sitemap.xml with {len(urls)} URLs")


if __name__ == "__main__":
    main()
