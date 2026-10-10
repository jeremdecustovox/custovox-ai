"""Build the custovox.ai static site into dist/ (run by Netlify).

Only the website files are published (index.html, robots.txt, blog/), never
the MCP servers or other repo content. Blog articles whose
`article:published_time` is later than today (Paris time) are left out, and
every link to them is removed, so each article goes live on its own date.

Usage: python3 build.py [YYYY-MM-DD]   (optional date, for testing)
"""
import datetime
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SITE = "https://custovox.ai"
PUBLISHED = ["index.html", "robots.txt", "blog"]


def today_paris() -> datetime.date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    except Exception:
        return datetime.datetime.utcnow().date()


def main() -> None:
    today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_paris()

    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    for name in PUBLISHED:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, DIST / name)
        else:
            shutil.copy2(src, DIST / name)

    live, hidden = [], []
    for page in sorted((DIST / "blog").glob("*.html")):
        if page.name == "index.html":
            continue
        m = re.search(r'article:published_time" content="(\d{4}-\d{2}-\d{2})', page.read_text(encoding="utf-8"))
        date = datetime.date.fromisoformat(m.group(1)) if m else today
        (hidden if date > today else live).append((page.stem, date))

    for slug, _ in hidden:
        (DIST / "blog" / f"{slug}.html").unlink()
        link = re.compile(
            r'<a\b[^>]*href="(?:%s)?/blog/%s(?:\.html)?"[^>]*>.*?</a>\s*' % (re.escape(SITE), re.escape(slug)),
            re.S,
        )
        for html in DIST.rglob("*.html"):
            text = html.read_text(encoding="utf-8")
            new = link.sub("", text)
            if new != text:
                html.write_text(new, encoding="utf-8")

    urls = [f"{SITE}/", f"{SITE}/blog/"] + [f"{SITE}/blog/{slug}" for slug, _ in live]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{u}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    print(f"Build date {today}: {len(live)} article(s) live, {len(hidden)} scheduled")
    for slug, date in hidden:
        print(f"  scheduled {date}  {slug}")


if __name__ == "__main__":
    main()
