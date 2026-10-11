"""Build the custovox.ai static site into dist/ (run by Netlify).

Only the website files are published (pages, blog, images and the translated
copies in fr/, de/, es/, pt-br/), never the MCP servers or other repo content.
Blog articles whose `article:published_time` is later than today (Paris time)
are left out, and every link to them is removed, so each article goes live on
its own date. Every page gets the language flags and hreflang links.

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
LANGS = ["en", "fr", "de", "es", "pt-br"]           # "en" lives at the root
HREFLANG = {"en": "en", "fr": "fr", "de": "de", "es": "es", "pt-br": "pt-BR"}
NAMES = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español", "pt-br": "Português (Brasil)"}
PUBLISHED = ["index.html", "robots.txt", "blog", "images", "fr", "de", "es", "pt-br"]

FLAGS = {
    "en": '<svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice"><clipPath id="uk-clip"><path d="M30,15h30v15zv15h-30zh-30v-15zv-15h30z"/></clipPath>'
          '<path d="M0,0v30h60v-30z" fill="#012169"/><path d="M0,0L60,30M60,0L0,30" stroke="#fff" stroke-width="6"/>'
          '<path d="M0,0L60,30M60,0L0,30" clip-path="url(#uk-clip)" stroke="#C8102E" stroke-width="4"/>'
          '<path d="M30,0v30M0,15h60" stroke="#fff" stroke-width="10"/><path d="M30,0v30M0,15h60" stroke="#C8102E" stroke-width="6"/></svg>',
    "fr": '<svg viewBox="0 0 3 2" preserveAspectRatio="none"><path fill="#0055A4" d="M0,0h1v2H0z"/><path fill="#fff" d="M1,0h1v2H1z"/><path fill="#EF4135" d="M2,0h1v2H2z"/></svg>',
    "de": '<svg viewBox="0 0 5 3" preserveAspectRatio="none"><path d="M0,0h5v1H0z"/><path fill="#DD0000" d="M0,1h5v1H0z"/><path fill="#FFCE00" d="M0,2h5v1H0z"/></svg>',
    "es": '<svg viewBox="0 0 3 2" preserveAspectRatio="none"><path fill="#AA151B" d="M0,0h3v2H0z"/><path fill="#F1BF00" d="M0,.5h3v1H0z"/></svg>',
    "pt-br": '<svg viewBox="0 0 720 504" preserveAspectRatio="none"><path fill="#009C3B" d="M0,0h720v504H0z"/><path fill="#FFDF00" d="M72,252L360,40L648,252L360,464z"/>'
             '<circle cx="360" cy="252" r="126" fill="#002776"/><path d="M240,226Q360,196 478,272" stroke="#fff" stroke-width="16" fill="none"/></svg>',
}
SWITCH_CSS = """<style>
.lang-switch{display:inline-flex;gap:7px;align-items:center;margin-left:1rem;}
.lang-switch a{display:inline-flex;border-radius:3px;overflow:hidden;opacity:.5;box-shadow:0 0 0 1px #E2E8F0;transition:opacity .15s;}
.lang-switch a:hover,.lang-switch a.active{opacity:1;}
.lang-switch svg{width:22px;height:15px;display:block;}
@media(max-width:600px){nav:has(.lang-switch){flex-wrap:wrap;row-gap:.6rem;}.lang-switch{margin-left:0;}}
</style>
"""


def today_paris() -> datetime.date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    except Exception:
        return datetime.datetime.utcnow().date()


def split_lang(rel: str):
    first = rel.split("/", 1)
    if len(first) == 2 and first[0] in LANGS:
        return first[0], first[1]
    return "en", rel


def url_of(rel: str) -> str:
    path = rel[:-len("index.html")] if rel.endswith("index.html") else rel[:-len(".html")]
    return "/" + path


def equivalent(rest: str, lang: str) -> str:
    """dist-relative path of `rest` in `lang`, falling back to the blog or home page."""
    prefix = "" if lang == "en" else lang + "/"
    for candidate in (rest, "blog/index.html" if rest.startswith("blog/") else "index.html"):
        if (DIST / (prefix + candidate)).exists():
            return prefix + candidate
    return prefix + "index.html"


def add_language_links(page: Path) -> None:
    rel = page.relative_to(DIST).as_posix()
    lang, rest = split_lang(rel)
    links = []
    alternates = []
    for other in LANGS:
        target = equivalent(rest, other)
        active = ' class="active" aria-current="true"' if other == lang else ""
        links.append(f'<a href="{url_of(target)}" hreflang="{HREFLANG[other]}" title="{NAMES[other]}"{active}>{FLAGS[other]}</a>')
        if target.endswith(rest):
            alternates.append(f'<link rel="alternate" hreflang="{HREFLANG[other]}" href="{SITE}{url_of(target)}">')
    if equivalent(rest, "en") == rest:
        alternates.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{url_of(rest)}">')

    html = page.read_text(encoding="utf-8")
    switch = '<div class="lang-switch" aria-label="Language">' + "".join(links) + "</div>"
    html = html.replace("</nav>", switch + "</nav>", 1)
    html = html.replace("</head>", "\n".join(alternates) + "\n" + SWITCH_CSS + "</head>", 1)
    page.write_text(html, encoding="utf-8")


def main() -> None:
    today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else today_paris()

    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    for name in PUBLISHED:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, DIST / name)
        elif src.exists():
            shutil.copy2(src, DIST / name)

    live, hidden = set(), set()
    for page in sorted(DIST.rglob("blog/*.html")):
        if page.name == "index.html":
            continue
        m = re.search(r'article:published_time" content="(\d{4}-\d{2}-\d{2})', page.read_text(encoding="utf-8"))
        date = datetime.date.fromisoformat(m.group(1)) if m else today
        if date > today:
            hidden.add(page.stem)
            page.unlink()
        else:
            live.add(page.stem)

    for slug in hidden:
        link = re.compile(
            r'<a\b[^>]*href="(?:%s)?/(?:(?:%s)/)?blog/%s(?:\.html)?"[^>]*>.*?</a>\s*'
            % (re.escape(SITE), "|".join(LANGS[1:]), re.escape(slug)), re.S)
        for html in DIST.rglob("*.html"):
            text = html.read_text(encoding="utf-8")
            new = link.sub("", text)
            if new != text:
                html.write_text(new, encoding="utf-8")

    pages = sorted(p for p in DIST.rglob("*.html"))
    for page in pages:
        add_language_links(page)

    urls = [SITE + url_of(p.relative_to(DIST).as_posix()) for p in pages]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{u}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    print(f"Build date {today}: {len(live)} article(s) live, {len(hidden)} scheduled, {len(pages)} pages")
    for slug in sorted(hidden):
        print(f"  scheduled  {slug}")


if __name__ == "__main__":
    main()
