"""Shared helpers: list the translatable text segments of an English page."""
import json
import re

SKIP_BLOCKS = re.compile(r"(?s)<(style|script)\b[^>]*>.*?</\1>")
TEXT = re.compile(r">([^<>]*[A-Za-z][^<>]*)<")
ATTR = re.compile(r'\b(content|alt|aria-label|title|placeholder)="([^"]*[A-Za-z][^"]*)"')
META_NAMES = re.compile(r'<meta\s+(?:name|property)="(description|og:title|og:description|twitter:title|twitter:description|keywords)"\s+content="([^"]*)"')
JSONLD = re.compile(r'(?s)<script type="application/ld\+json">(.*?)</script>')
JSON_KEYS = ("headline", "description", "name", "articleSection")


def segments(html: str) -> list:
    out = []
    def add(s):
        s = s.strip()
        if s and s not in out and re.search(r"[A-Za-z]", s):
            out.append(s)
    for _, val in META_NAMES.findall(html):
        add(val)
    for block in JSONLD.findall(html):
        for key in JSON_KEYS:
            for val in re.findall(r'"%s":\s*"([^"]*)"' % key, block):
                add(val)
    body = SKIP_BLOCKS.sub("", html)
    body = re.sub(r"(?s)<meta[^>]*>", "", body)
    for txt in TEXT.findall(body):
        add(txt)
    for name, val in ATTR.findall(body):
        if name != "content":
            add(val)
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    segs = segments(open(sys.argv[1], encoding="utf-8").read())
    print(json.dumps({s: "" for s in segs}, ensure_ascii=False, indent=1))
