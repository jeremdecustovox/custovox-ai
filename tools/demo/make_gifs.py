"""Make the 3 demo GIFs (EN + FR) in the style of the voc-skill demo GIF, with CustoVox colours.

  images/demo/custovox-calls-demo-{en,fr}.gif    custovox-calls in demo mode (fictional calls)
  images/demo/custovox-demo-reviews-{en,fr}.gif  the /demo page on the fictional example reviews
  images/demo/custovox-sample-report-{en,fr}.gif the fictional sample report

Every number and sentence shown comes from the real code: custovox-calls' demo data (needs the
package importable: run with the venv where callscope-ai and custovox-calls are installed) and
demo-engine.js (node). Fictional data only. Needs Pillow.

Usage: python tools/demo/make_gifs.py
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "mcp" / "callscope-ai" / "src"))
sys.path.insert(0, str(ROOT / "mcp" / "custovox-calls" / "src"))
from fixtures import REPORT_EN, REPORT_FR, REVIEWS_EN, REVIEWS_FR  # noqa: E402
from pages import REASON_LABELS, T  # noqa: E402

OUT = ROOT / "images" / "demo"
W, H = 960, 540
BG, BAR, WHITE, GRAY, DIM = (17, 21, 28), (28, 34, 46), (236, 239, 244), (148, 163, 184), (100, 116, 139)
NAVY, TEAL, TEAL_D, G200, G600, RED, AMBER = (13, 43, 107), (0, 196, 140), (0, 158, 114), (226, 232, 240), (71, 85, 105), (194, 65, 12), (180, 83, 9)


def font(name, size):
    return ImageFont.truetype(name, size)   # Segoe UI / Consolas, found by Pillow in the system fonts


SANS, BOLD, MONO = (lambda s: font("segoeui.ttf", s)), (lambda s: font("segoeuib.ttf", s)), (lambda s: font("consola.ttf", s))


def window(title, light=False):
    im = Image.new("RGB", (W, H), (255, 255, 255) if light else BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 35], fill=BAR)
    for i, c in enumerate([(239, 68, 68), (234, 179, 8), (34, 197, 94)]):
        d.ellipse([14 + i * 22, 11, 26 + i * 22, 23], fill=c)
    d.text((W // 2, 18), title, font=SANS(13), fill=GRAY, anchor="mm")
    return im, d


def footer(d, text, light=False):
    d.text((W // 2, H - 16), text, font=SANS(12), fill=DIM if not light else (148, 163, 184), anchor="mm")


def card(title, sub, lines, foot, wtitle):
    im, d = window(wtitle)
    d.text((W // 2, 205), title, font=BOLD(50), fill=WHITE, anchor="mm")
    d.text((W // 2, 262), sub, font=SANS(23), fill=TEAL, anchor="mm")
    y = 325
    for kind, text in lines:
        d.text((W // 2, y), text, font=MONO(22) if kind == "mono" else SANS(17), fill=WHITE if kind == "mono" else GRAY, anchor="mm")
        y += 52
    footer(d, foot)
    return im


def save(frames, name):
    OUT.mkdir(parents=True, exist_ok=True)
    ims = [f for f, _ in frames]
    durs = [ms for _, ms in frames]
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=64, dither=Image.NONE) for im in ims]
    path = OUT / name
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, optimize=True, disposal=1)
    print(f"{name}: {len(ims)} frames, {sum(durs) / 1000:.1f} s, {path.stat().st_size // 1024} KB")


def run_engine(texts):
    code = ("const e=require(process.argv[1]);let d='';process.stdin.on('data',c=>d+=c)"
            ".on('end',()=>process.stdout.write(JSON.stringify(e.report(JSON.parse(d)))));")
    out = subprocess.run(["node", "-e", code, str(ROOT / "demo-engine.js")], input=json.dumps(texts),
                         capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


# ------------------------------------------------------------------ 1. custovox-calls

CALLS = {
    "en": dict(sub="Local call analysis · simple FR/EN rules", fict="Fictional data · demo mode (CUSTOVOX_CALLS_DEMO=1)",
               ask="Which demo calls had a churn threat? What should we do?",
               calls="{n} calls · {m} min · mean customer sentiment {s:+.2f}",
               churn="Customers who mentioned leaving:", acts="Suggested actions for {cid} (nothing is sent):",
               types={"manager_alert": "Manager alert", "customer_callback": "Customer callback", "crm_ticket": "CRM ticket"},
               prio={"high": "HIGH", "medium": "MEDIUM"},
               end2="Open source · MIT · free", end4="Your calls stay on your machine"),
    "fr": dict(sub="Analyse locale de vos appels · règles simples FR/EN", fict="Données fictives · mode démo (CUSTOVOX_CALLS_DEMO=1)",
               ask="Quels appels de démo contiennent une menace de départ ? Que faire ?",
               calls="{n} appels · {m} min · sentiment client moyen {s:+.2f}",
               churn="Clients qui parlent de partir :", acts="Actions proposées pour {cid} (rien n'est envoyé) :",
               types={"manager_alert": "Alerte responsable", "customer_callback": "Rappel client", "crm_ticket": "Ticket CRM"},
               prio={"high": "HAUTE", "medium": "MOYENNE"},
               end2="Open source · MIT · gratuit", end4="Vos appels restent sur votre poste"),
}


def reason_text(lang, why):
    """custovox-calls writes its reasons in English; the FR GIF shows the same reason in French."""
    if lang == "en":
        return why
    import re
    fixed = {"The customer mentioned leaving.": "Le client a parlé de partir.",
             "The agent made a promise: check it is kept.": "Le conseiller a fait une promesse : vérifier qu'elle est tenue.",
             "The customer complained.": "Le client s'est plaint."}
    if why in fixed:
        return fixed[why]
    m = re.match(r"Negative customer sentiment \(([-+.\d]+)\)(?: about (.*))?\.$", why)
    if m:
        about = ", ".join(REASON_LABELS["fr"].get(k.strip(), k).lower() for k in m.group(2).split(",")) if m.group(2) else ""
        return f"Sentiment client négatif ({m.group(1)})" + (f" sur : {about}." if about else ".")
    return why


def gif_calls(lang):
    import callscope
    from custovox_calls import actions
    from custovox_calls.demo import DEMO_CALLS
    from custovox_calls.store import CallStore
    c = CALLS[lang]
    st = CallStore(":memory:")
    analyses = {}
    for cid, (started, segs) in DEMO_CALLS.items():
        analyses[cid] = callscope.analyze(segs)
        st.save(cid, started, analyses[cid])
    ins = st.insights(None, None)
    first = ins["churn_threats"][0]["call_id"]
    acts = actions.suggest(first, analyses[first])
    wt = "custovox-calls · " + ("call analysis" if lang == "en" else "analyse d'appels")

    frames = [(card("custovox-calls", c["sub"], [], c["fict"], wt), 1500)]

    def base():
        im, d = window(wt)
        footer(d, c["fict"])
        return im, d

    ask = c["ask"]
    step = 4
    for k in list(range(0, len(ask), step)) + [len(ask)]:
        im, d = base()
        d.text((40, 70), ">", font=MONO(20), fill=TEAL)
        d.text((66, 70), ask[:k], font=MONO(20), fill=WHITE)
        x = 66 + d.textlength(ask[:k], font=MONO(20))
        d.rectangle([x + 2, 72, x + 12, 94], fill=WHITE)
        frames.append((im, 60))
    frames[-1] = (frames[-1][0], 600)

    lines = [("tool", "custovox-calls · get_call_insights"),
             ("text", c["calls"].format(n=ins["calls"], m=ins["total_minutes"], s=ins["customer_sentiment_mean"])),
             ("head", c["churn"])]
    lines += [("quote", f'{t["call_id"]} — « {t["text"]} »') for t in ins["churn_threats"]]
    lines += [("tool", f"custovox-calls · suggest_actions {first}"), ("head", c["acts"].format(cid=first))]
    lines += [("act", (a["priority"], c["types"][a["type"]], reason_text(lang, a["reason"]))) for a in acts]

    shown = []
    for item in lines:
        shown.append(item)
        im, d = base()
        d.text((40, 60), ">", font=MONO(18), fill=TEAL)
        d.text((66, 60), ask, font=MONO(18), fill=WHITE)
        y = 104
        for kind, val in shown:
            if kind == "tool":
                y += 6
                d.ellipse([42, y + 7, 50, y + 15], fill=TEAL)
                d.text((66, y), val, font=MONO(17), fill=TEAL)
                y += 34
            elif kind == "head":
                d.text((66, y), val, font=BOLD(17), fill=WHITE)
                y += 30
            elif kind == "text":
                d.text((66, y), val, font=SANS(17), fill=GRAY)
                y += 32
            elif kind == "quote":
                for i, ln in enumerate(wrap(d, val, SANS(15), 840)[:2]):
                    d.text((86, y), ln, font=SANS(15), fill=GRAY)
                    y += 22
                y += 6
            else:
                prio, typ, why = val
                tag = c["prio"][prio]
                tw = d.textlength(tag, font=BOLD(13)) + 16
                d.rounded_rectangle([86, y + 2, 86 + tw, y + 22], radius=10, fill=(120, 45, 10) if prio == "high" else (110, 80, 10))
                d.text((94, y + 3), tag, font=BOLD(13), fill=WHITE)
                d.text((96 + tw, y), f"{typ} — {why}", font=SANS(16), fill=WHITE)
                y += 30
        frames.append((im, 500 if kind != "act" else 700))
    frames[-1] = (frames[-1][0], 2600)
    frames.append((card("custovox-calls", c["end2"], [("mono", "uvx custovox-calls"), ("sans", c["end4"])],
                        c["fict"], wt), 2600))
    save(frames, f"custovox-calls-demo-{lang}.gif")


# ------------------------------------------------------------------ 2. /demo page

def browser(lang, url):
    im, d = window(url, light=True)
    d.rectangle([0, 36, W, 76], fill=(255, 255, 255))
    d.text((24, 56), "custovox", font=BOLD(20), fill=TEAL, anchor="lm")
    d.text((24 + d.textlength("custovox", font=BOLD(20)), 56), ".ai", font=BOLD(20), fill=NAVY, anchor="lm")
    d.line([0, 76, W, 76], fill=G200)
    return im, d


def tagbox(d, x, y, text, prio):
    f = BOLD(12)
    w = d.textlength(text, font=f) + 14
    d.rounded_rectangle([x, y, x + w, y + 20], radius=10, fill=(255, 237, 213) if prio == "high" else (254, 243, 199))
    d.text((x + 7, y + 3), text, font=f, fill=RED if prio == "high" else AMBER)
    return w


def gif_demo(lang):
    t, labels = T[lang], REASON_LABELS[lang]
    texts = REVIEWS_FR if lang == "fr" else REVIEWS_EN
    r = run_engine(texts)
    url = "custovox.ai" + t["demo_path"]
    fict = t["example_note"]
    q = ("“", "”") if lang == "en" else ("« ", " »")
    frames = []

    def page(n_lines, pressed=False):
        im, d = browser(lang, url)
        d.text((40, 96), t["h1"], font=BOLD(28), fill=NAVY)
        d.rounded_rectangle([40, 146, 920, 400], radius=10, outline=G200, width=2)
        for i, ln in enumerate(texts[:n_lines]):
            d.text((56, 158 + i * 29), ln[:95], font=SANS(16), fill=NAVY)
        bx = 40
        d.rounded_rectangle([bx, 418, bx + 130, 458], radius=8, fill=TEAL_D if pressed else TEAL)
        d.text((bx + 65, 438), t["analyze"], font=BOLD(16), fill=NAVY, anchor="mm")
        d.text((190, 438), t["privacy_note"][:80], font=SANS(13), fill=G600, anchor="lm")
        footer(d, fict, light=True)
        return im, d

    frames.append((page(0)[0], 900))
    for n in (3, 6, 8):
        frames.append((page(n)[0], 350))
    frames[-1] = (frames[-1][0], 1200)
    frames.append((page(8, pressed=True)[0], 400))

    def report(stage):
        im, d = browser(lang, url)
        d.text((40, 92), t["r_title"], font=BOLD(24), fill=NAVY)
        d.text((40 + d.textlength(t["r_title"], font=BOLD(24)) + 12, 100), "· " + t["r_texts"].format(n=r["count"]),
               font=SANS(14), fill=(148, 163, 184))
        # tone card
        d.rounded_rectangle([40, 134, 470, 290], radius=12, outline=G200, width=2)
        d.text((58, 148), t["tone"], font=BOLD(15), fill=NAVY)
        overall = "positive" if r["mean"] > 0.15 else "negative" if r["mean"] < -0.15 else "neutral"
        d.text((58, 174), t["tone_overall"][overall], font=BOLD(20), fill=NAVY)
        x = 58
        for k, col in (("positive", TEAL), ("neutral", (148, 163, 184)), ("negative", RED)):
            w = 394 * r["labels"][k] / r["count"]
            d.rectangle([x, 214, x + w, 228], fill=col)
            x += w
        lx = 58
        for k, col, key in (("positive", TEAL, "tone_pos"), ("neutral", (148, 163, 184), "tone_neu"), ("negative", RED, "tone_neg")):
            s = f'{r["labels"][k]} {t[key]}'
            d.rectangle([lx, 248, lx + 10, 258], fill=col)
            d.text((lx + 16, 244), s, font=SANS(14), fill=G600)
            lx += 30 + d.textlength(s, font=SANS(14))
        # topics card
        d.rounded_rectangle([490, 134, 920, 290], radius=12, outline=G200, width=2)
        d.text((508, 148), t["topics"], font=BOLD(15), fill=NAVY)
        for i, x_ in enumerate(r["reasons"][:4]):
            y = 176 + i * 27
            d.text((508, y), labels[x_["reason"]], font=SANS(15), fill=NAVY)
            d.text((902, y), t["topic_texts"].format(n=x_["texts"]), font=SANS(14), fill=(148, 163, 184), anchor="ra")
        if stage >= 1:
            d.rounded_rectangle([40, 306, 920, 506], radius=12, outline=G200, width=2)
            d.text((58, 318), t["actions"], font=BOLD(15), fill=NAVY)
            for i, a in enumerate(r["actions"][:3]):
                y = 348 + i * 52
                title = t["act_churn"] if a["type"] == "manager_alert" and a["why"] == "churn_threat" else \
                    t["act_complaint"] if a["type"] == "manager_alert" else \
                    (t["act_ticket_about"].format(topics=", ".join(labels[k].lower() for k in a["reasons"])) if a["reasons"] else t["act_ticket"])
                w = tagbox(d, 58, y, t["prio"][a["priority"]], a["priority"])
                d.text((66 + w, y), title, font=BOLD(15), fill=NAVY)
                ev = t["line"].format(n=a["index"] + 1) + " — " + q[0] + a["evidence"] + q[1]
                d.text((70, y + 24), ev[:110] + ("…" if len(ev) > 110 else ""), font=SANS(13), fill=G600)
        footer(d, fict, light=True)
        return im

    frames.append((report(0), 1600))
    frames.append((report(1), 4200))
    end = card("custovox.ai" + t["demo_path"], t["h1"],
               [("sans", t["privacy_note"][:90])], fict, url)
    frames.append((end, 2600))
    save(frames, f"custovox-demo-reviews-{lang}.gif")


# ------------------------------------------------------------------ 3. sample report

def gif_report(lang):
    t, labels = T[lang], REASON_LABELS[lang]
    r = run_engine(REPORT_FR if lang == "fr" else REPORT_EN)
    q = ("“", "”") if lang == "en" else ("« ", " »")
    url = "custovox.ai" + t["report_path"]
    # Draw the whole report on a tall canvas, then scroll through it.
    tall = Image.new("RGB", (W, 1500), (255, 255, 255))
    d = ImageDraw.Draw(tall)
    y = 20
    for ln in wrap(d, t["rep_h1"], BOLD(30), 880):
        d.text((40, y), ln, font=BOLD(30), fill=NAVY)
        y += 40
    y += 8
    d.rounded_rectangle([40, y, 920, y + 48], radius=10, fill=(254, 243, 199))
    d.text((56, y + 13), t["rep_fictional"][:120], font=SANS(14), fill=(120, 53, 15))
    y += 72

    def h2(text):
        nonlocal y
        d.text((40, y), text, font=BOLD(22), fill=NAVY)
        y += 40

    h2(t["rep_summary"])
    top = [labels[x["reason"]].lower() for x in r["reasons"][:3]]
    summary = t["rep_summary_text"].format(n=r["count"], pos=r["labels"]["positive"], neu=r["labels"]["neutral"],
                                           neg=r["labels"]["negative"], topics=", ".join(top), churn=len(r["churn"]))
    for ln in wrap(d, summary, SANS(17), 880):
        d.text((40, y), ln, font=SANS(17), fill=NAVY)
        y += 26
    x = 40
    for k, col in (("positive", TEAL), ("neutral", (148, 163, 184)), ("negative", RED)):
        w = 880 * r["labels"][k] / r["count"]
        d.rectangle([x, y + 8, x + w, y + 24], fill=col)
        x += w
    y += 56
    h2(t["topics"])
    for x_ in r["reasons"][:6]:
        d.text((40, y), labels[x_["reason"]], font=SANS(17), fill=NAVY)
        d.text((920, y), t["topic_texts"].format(n=x_["texts"]), font=SANS(15), fill=(148, 163, 184), anchor="ra")
        d.line([40, y + 30, 920, y + 30], fill=G200)
        y += 38
    y += 16
    h2(t["rep_quotes"])
    for x_ in r["reasons"][:2]:
        hits = sorted((p for p in r["per"] if any(z["reason"] == x_["reason"] for z in p["reasons"])), key=lambda p: p["score"])[:2]
        d.text((40, y), labels[x_["reason"]], font=BOLD(16), fill=NAVY)
        y += 28
        for p in hits:
            d.rectangle([40, y, 43, y + 22], fill=TEAL)
            d.text((54, y), q[0] + p["text"] + q[1], font=SANS(15), fill=G600)
            y += 32
    y += 12
    h2(t["rep_plan"])
    for a in r["actions"]:
        title = t["act_churn"] if a["type"] == "manager_alert" and a["why"] == "churn_threat" else \
            t["act_complaint"] if a["type"] == "manager_alert" else \
            (t["act_ticket_about"].format(topics=", ".join(labels[k].lower() for k in a["reasons"])) if a["reasons"] else t["act_ticket"])
        w = tagbox(d, 40, y + 2, t["prio"][a["priority"]], a["priority"])
        d.text((50 + w, y), title, font=BOLD(16), fill=NAVY)
        d.text((54, y + 28), q[0] + a["evidence"] + q[1], font=SANS(14), fill=G600)
        y += 64
    page_h = y + 20
    view = H - 36 - 30
    frames = []
    max_off = max(0, page_h - view)
    steps = 22
    for i in range(steps + 1):
        off = int(max_off * i / steps)
        im, dd = window(url, light=True)
        im.paste(tall.crop((0, off, W, off + view)), (0, 36))
        dd.rectangle([0, H - 30, W, H], fill=(255, 255, 255))
        footer(dd, t["rep_fictional"].split(":")[0] if lang == "en" else "Données fictives", light=True)
        frames.append((im, 1800 if i == 0 else 2600 if i == steps else 260))
    end = card(t["rep_h1"].split(":")[0], "custovox.ai" + t["report_path"],
               [("sans", t["cta_title"])], "Maison Verveine · " + ("fictional data" if lang == "en" else "données fictives"), url)
    frames.append((end, 2600))
    save(frames, f"custovox-sample-report-{lang}.gif")


if __name__ == "__main__":
    for lang in ("en", "fr"):
        gif_calls(lang)
        gif_demo(lang)
        gif_report(lang)
