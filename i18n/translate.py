"""Generate the translated site (fr/, de/, es/, pt-br/) from the English pages.

The English pages are the source of truth. Each language has one dictionary,
i18n/<lang>.json, mapping English text segments to their translation (see
segments.py). Run after changing an English page or a dictionary:

    python i18n/translate.py

Segments missing from a dictionary stay in English and are listed.
Article URLs are localized with i18n/slugs.json (English slug -> slug per language);
an article without an entry keeps its English slug.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = {"fr": "fr", "de": "de", "es": "es", "pt-br": "pt-BR"}
JSON_KEYS = ("headline", "description", "name", "articleSection")
META_NAMES = "description|og:title|og:description|twitter:title|twitter:description|keywords"
NOT_PAGES = r"(?!images/|blog/images/)"


def load_slugs() -> dict:
    path = ROOT / "i18n" / "slugs.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def localize_links(html: str, lang: str, slugs: dict) -> str:
    """/fr/blog/<english-slug> -> /fr/blog/<french-slug> (relative and absolute links)."""
    for en, per_lang in slugs.items():
        loc = per_lang.get(lang)
        if loc and loc != en:
            html = re.sub(r"(/%s/blog/)%s(?=[\"#?])" % (re.escape(lang), re.escape(en)), r"\g<1>" + loc, html)
    return html


def pages():
    yield ROOT / "index.html"
    yield from sorted((ROOT / "blog").glob("*.html"))


def translate(html: str, lang: str, words: dict, missing: set) -> str:
    def tr(text):
        key = text.strip()
        if not key or not re.search(r"[A-Za-z]", key):
            return text
        if key not in words:
            missing.add(key)
            return text
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        return lead + words[key] + trail

    # Text nodes, outside <style>/<script>.
    parts = re.split(r"(?s)(<(?:style|script)\b[^>]*>.*?</(?:style|script)>)", html)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r">([^<>]+)<", lambda m: ">" + tr(m.group(1)) + "<", parts[i])
        parts[i] = re.sub(r'\b(alt|aria-label|title)="([^"]+)"',
                          lambda m: '%s="%s"' % (m.group(1), tr(m.group(2))), parts[i])
    html = "".join(parts)

    # Meta tags and JSON-LD.
    html = re.sub(r'(<meta\s+(?:name|property)="(?:%s)"\s+content=")([^"]*)(")' % META_NAMES,
                  lambda m: m.group(1) + tr(m.group(2)) + m.group(3), html)
    html = re.sub(r'(?s)(<script type="application/ld\+json">)(.*?)(</script>)',
                  lambda m: m.group(1) + re.sub(
                      r'("(?:%s)":\s*")([^"]*)(")' % "|".join(JSON_KEYS),
                      lambda k: k.group(1) + tr(k.group(2)) + k.group(3), m.group(2)) + m.group(3), html)

    # Language and links to this language's pages (images stay shared).
    html = re.sub(r'<html lang="[^"]*"', '<html lang="%s"' % LANGS[lang], html, count=1)
    html = re.sub(r'href="/%s' % NOT_PAGES, 'href="/%s/' % lang, html)
    html = re.sub(r"https://custovox\.ai/%s" % NOT_PAGES, "https://custovox.ai/%s/" % lang, html)
    html = re.sub(r'("inLanguage":\s*")[^"]*(")', r"\g<1>%s\2" % LANGS[lang], html)
    return html


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    slugs = load_slugs()
    for lang in LANGS:
        words = json.loads((ROOT / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
        for old in (ROOT / lang).rglob("*.html") if (ROOT / lang).exists() else []:
            old.unlink()   # regenerate from scratch (slugs may have changed)
        for page in pages():
            missing = set()
            rel = page.relative_to(ROOT)
            if rel.parent.name == "blog" and page.stem in slugs and lang in slugs[page.stem]:
                rel = rel.with_name(slugs[page.stem][lang] + ".html")
            out = ROOT / lang / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            html = translate(page.read_text(encoding="utf-8"), lang, words, missing)
            out.write_text(localize_links(html, lang, slugs), encoding="utf-8")
            if missing:
                print(f"[{lang}] {page.relative_to(ROOT)}: {len(missing)} untranslated")
                for m in sorted(missing):
                    print("    ", m[:90])
    print("done")


if __name__ == "__main__":
    main()
