"""Build the custovox.ai static site into dist/ (run by Netlify).

Only the website files are published (pages, blog, images and the translated
copies in fr/, de/, es/, pt-br/), never the MCP servers or other repo content.
Blog articles whose `article:published_time` is later than today (Paris time)
are left out, and every link to them is removed, so each article goes live on
its own date. Every page gets the language switcher (EN · FR) and
hreflang links; translated articles have localized URLs (i18n/slugs.json).
/llms.txt is regenerated at every build from llms-header.md + the pages published that day.

Usage: python3 build.py [YYYY-MM-DD]   (optional date, for testing)
"""
import datetime
import json
import re
import shutil
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SITE = "https://custovox.ai"
LANGS = ["en", "fr"]                                # published languages; "en" lives at the root
HIDDEN_LANGS = ["de", "es", "pt-br"]               # kept in the repo, not published: redirected to English
HREFLANG = {"en": "en", "fr": "fr", "de": "de", "es": "es", "pt-br": "pt-BR"}
NAMES = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español", "pt-br": "Português (Brasil)"}
PUBLISHED = ["index.html", "faq.html", "pricing.html", "how-it-works.html", "features", "integrations.html", "about.html", "security-gdpr.html", "solutions", "merci.html", "thank-you.html", "privacy.html", "consent.js", "favicon.ico",
             "robots.txt", "blog", "images", "fr"]

CODES = {"en": "EN", "fr": "FR", "de": "DE", "es": "ES", "pt-br": "PT"}
SWITCH_CSS = """<style>
.lang-switch{display:inline-flex;gap:10px;align-items:center;margin-left:1.25rem;}
.lang-switch a{font-size:12px;font-weight:600;letter-spacing:.04em;color:#94A3B8;text-decoration:none;padding:2px 0;border-bottom:2px solid transparent;transition:color .15s;}
.lang-switch a:hover{color:#0D2B6B;}
.lang-switch a.active{color:#0D2B6B;border-bottom-color:#00C48C;}
@media(max-width:600px){nav:has(.lang-switch){flex-wrap:wrap;row-gap:.6rem;}.nav-links{flex-wrap:wrap;row-gap:.5rem;}.lang-switch{margin-left:0;}}
</style>
"""


SLUGS_FILE = ROOT / "i18n" / "slugs.json"
SLUGS = json.loads(SLUGS_FILE.read_text(encoding="utf-8")) if SLUGS_FILE.exists() else {}


def slug_in(lang: str, en_slug: str) -> str:
    return en_slug if lang == "en" else SLUGS.get(en_slug, {}).get(lang, en_slug)


def to_english_rest(lang: str, rest: str) -> str:
    """blog/<localized-slug>.html -> blog/<english-slug>.html"""
    if lang != "en" and rest.startswith("blog/") and rest != "blog/index.html":
        stem = rest[len("blog/"):-len(".html")]
        for en, per_lang in SLUGS.items():
            if per_lang.get(lang) == stem:
                return f"blog/{en}.html"
    return rest


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


def equivalent(en_rest: str, lang: str) -> str:
    """dist-relative path of a page in `lang`, falling back to the blog or home page."""
    prefix = "" if lang == "en" else lang + "/"
    rest = en_rest
    if en_rest.startswith("blog/") and en_rest != "blog/index.html":
        rest = "blog/" + slug_in(lang, en_rest[len("blog/"):-len(".html")]) + ".html"
    for candidate in (rest, "blog/index.html" if rest.startswith("blog/") else "index.html"):
        if (DIST / (prefix + candidate)).exists():
            return prefix + candidate
    return prefix + "index.html"


def add_language_links(page: Path) -> None:
    rel = page.relative_to(DIST).as_posix()
    lang, rest = split_lang(rel)
    en_rest = to_english_rest(lang, rest)
    links = []
    alternates = []
    for other in LANGS:
        target = equivalent(en_rest, other)
        active = ' class="active" aria-current="true"' if other == lang else ""
        links.append(f'<a href="{url_of(target)}" hreflang="{HREFLANG[other]}" title="{NAMES[other]}"{active}>{CODES[other]}</a>')
        if not target.endswith("index.html") or en_rest.endswith("index.html"):
            alternates.append(f'<link rel="alternate" hreflang="{HREFLANG[other]}" href="{SITE}{url_of(target)}">')
    if equivalent(en_rest, "en") == en_rest:
        alternates.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{url_of(en_rest)}">')

    html = page.read_text(encoding="utf-8")
    if 'class="lang"' in html or "cvx-lang" in html:   # page with its own language switcher (site nav)
        links = []
    switch = '<div class="lang-switch" aria-label="Language">' + "".join(links) + "</div>"
    if links:
        html = html.replace("</nav>", switch + "</nav>", 1)
    if 'rel="alternate"' in html:   # page already declares its language versions
        alternates = []
    html = html.replace("</head>", "\n".join(alternates) + "\n" + SWITCH_CSS + "</head>", 1)
    page.write_text(html, encoding="utf-8")


def page_info(page: Path):
    """(title, description) of a published page, without the " — CustoVox.ai" suffix."""
    html = page.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    title = re.sub(r"(?i)\s*[—|-]\s*custovox\.ai\s*$", "", title.group(1).strip()) if title else page.stem
    return unescape(title), (unescape(desc.group(1).strip()) if desc else "")


def write_llms_txt(pages) -> None:
    """dist/llms.txt = llms-header.md (fixed text) + the pages actually published today."""
    src = ROOT / "llms-header.md"
    if not src.exists():
        return
    text = re.sub(r"(?s)<!--(?! OPTIONAL).*?-->\n?", "", src.read_text(encoding="utf-8"))
    head, _, optional = text.partition("<!-- OPTIONAL -->\n")
    by_rel = {p.relative_to(DIST).as_posix(): p for p in pages}

    def line(rel):
        title, desc = page_info(by_rel[rel])
        return f"- [{title}]({SITE}{url_of(rel)})" + (f": {desc}" if desc else "")

    sections = {
        "Main pages": ["index.html", "fr/index.html", "faq.html", "fr/faq.html", "pricing.html", "fr/tarifs.html",
                       "how-it-works.html", "fr/comment-ca-marche.html", "integrations.html", "fr/integrations.html",
                       "about.html", "fr/a-propos.html", "security-gdpr.html", "fr/securite-rgpd.html"],
        "Solutions": ["solutions/retail.html", "fr/solutions/retail.html",
                      "solutions/hospitality.html", "fr/solutions/hospitality.html",
                      "solutions/call-centers.html", "fr/solutions/call-centers.html",
                      "solutions/agencies.html", "fr/solutions/agencies.html"],
        "Features": ["features/index.html", "fr/fonctionnalites/index.html"]
                    + [f"{p}/{m}/index.html" for m in ("textiq", "voiceiq", "visualiq", "predictiq")
                       for p in ("features", "fr/fonctionnalites")],
        "Blog (English)": ["blog/index.html"] + sorted(r for r in by_rel if r.startswith("blog/") and r != "blog/index.html"),
        "Blog (français)": ["fr/blog/index.html"] + sorted(r for r in by_rel if r.startswith("fr/blog/") and r != "fr/blog/index.html"),
        "Legal": ["privacy.html", "fr/confidentialite.html"],
    }
    out = [head.rstrip(), ""]
    for name, rels in sections.items():
        rels = [r for r in rels if r in by_rel]
        if rels:
            out += [f"## {name}"] + [line(r) for r in rels] + [""]
    out.append(optional.strip())
    (DIST / "llms.txt").write_text("\n".join(out) + "\n", encoding="utf-8")


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

    # noindex pages (e.g. /merci.html) get no language links and stay out of the sitemap.
    # Cookie consent banner + footer legal links on every page (consent.js).
    for page in DIST.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        if "/consent.js" not in html:
            page.write_text(html.replace("</body>", '<script src="/consent.js" defer></script>\n</body>', 1), encoding="utf-8")

    pages = sorted(p for p in DIST.rglob("*.html") if 'name="robots" content="noindex"' not in p.read_text(encoding="utf-8"))
    for page in pages:
        add_language_links(page)

    redirects = [f"/{lang}/blog/{en} /{lang}/blog/{loc} 301"
                 for en, per_lang in SLUGS.items() for lang, loc in per_lang.items()
                 if loc != en and lang in LANGS]
    # Hidden languages and /en: old URLs go to the English version (no dead links).
    redirects += ["/en / 301", "/en/ / 301", "/en/* /:splat 301", "/pt / 301", "/pt/* / 301"]
    for lang in HIDDEN_LANGS:
        for en, per_lang in SLUGS.items():
            for slug in {en, per_lang.get(lang, en)}:
                redirects.append(f"/{lang}/blog/{slug} /blog/{en} 301")
        redirects += [f"/{lang}/blog /blog/ 301", f"/{lang}/blog/ /blog/ 301", f"/{lang}/blog/* /blog/ 301",
                      f"/{lang} / 301", f"/{lang}/ / 301", f"/{lang}/* / 301"]
    (DIST / "_redirects").write_text("\n".join(redirects) + "\n", encoding="utf-8")

    urls = [SITE + url_of(p.relative_to(DIST).as_posix()) for p in pages]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{u}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")
    write_llms_txt(pages)

    print(f"Build date {today}: {len(live)} article(s) live, {len(hidden)} scheduled, {len(pages)} pages")
    for slug in sorted(hidden):
        print(f"  scheduled  {slug}")


if __name__ == "__main__":
    main()
