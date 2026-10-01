#!/usr/bin/env python3
"""
Bi-weekly review audit for lovedbyaireviews.com.

Compares the live state of every review source against reviews.json (the ledger)
and reports what is NEW, what is LOST, and where the published score has drifted.

Covers automatically (plain HTTP):
    WordPress.org  - plugin API + reviews forum, per-review 404 checks
    Website        - lovedby.ai testimonials

Cannot cover automatically: G2, Trustpilot and Google all return 403 to scripted
requests or need JS. Those are captured with a real browser via the
/review-audit skill; this script prints exactly what to go and check.

    python3 scripts/audit_reviews.py            # report only
    python3 scripts/audit_reviews.py --write    # also stamp last_verified / status
    python3 scripts/audit_reviews.py --json     # machine-readable report
"""
import json, re, sys, html, urllib.request, urllib.error, datetime, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "reviews.json"
TODAY = datetime.date.today().isoformat()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BROWSER_ONLY = ("G2", "Trustpilot", "Google")


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def status_of(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def norm(s):
    """Fold typographic variants so a curly apostrophe is not reported as drift."""
    if not s:
        return ""
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2014", "-"), ("\u2013", "-"), ("\u2026", "..."), ("\u00a0", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()


def strip(s):
    s = re.sub(r"<li[^>]*>", "\n- ", s)
    s = re.sub(r"</p>", "\n\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


# ---------------------------------------------------------------- WordPress.org
def wordpress(slug):
    api = ("https://api.wordpress.org/plugins/info/1.2/?action=plugin_information"
           f"&request[slug]={slug}")
    d = json.loads(get(api))
    if "error" in d:
        raise RuntimeError(f"WordPress API: {d['error']}")
    out = {
        "score": round(d["rating"] / 20, 1),
        "ratings": d["num_ratings"],
        "distribution": {str(k): v for k, v in d["ratings"].items()},
        "version": d["version"],
        "active_installs": d["active_installs"],
        "reviews": [],
    }
    page = get(f"https://wordpress.org/support/plugin/{slug}/reviews/")
    for block in re.findall(r'<li class="[^"]*bbp-topic[^"]*"[^>]*>.*?</li>', page, re.S):
        m = re.search(r'href="https://wordpress\.org/support/topic/([^"/]+)/"[^>]*>([^<]+)<', block)
        if not m:
            continue
        rating = re.search(r"aria-label='([\d.]+) out of 5 stars'", block)
        out["reviews"].append({
            "slug": m.group(1),
            "title": html.unescape(m.group(2)).strip(),
            "rating": float(rating.group(1)) if rating else None,
            "url": f"https://wordpress.org/support/topic/{m.group(1)}/",
        })
    seen, uniq = set(), []
    for r in out["reviews"]:
        if r["slug"] not in seen:
            seen.add(r["slug"])
            uniq.append(r)
    out["reviews"] = uniq
    return out


def wordpress_review(url):
    """Full detail for one review topic, or None if it is gone."""
    try:
        h = get(url)
    except urllib.error.HTTPError:
        return None
    title = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    rating = re.search(r"aria-label='([\d.]+) out of 5 stars'", h)
    author = re.search(r'class="bbp-author-name">([^<]+)<', h)
    date = re.search(r'title="([^"]+)"\s+class="bbp-topic-permalink"', h)
    body = re.search(r'<div class="bbp-topic-content">(.*?)</div>', h, re.S)
    return {
        "title": strip(title.group(1)) if title else None,
        "rating": float(rating.group(1)) if rating else None,
        "author": html.unescape(author.group(1)).strip() if author else None,
        "date": date.group(1) if date else None,
        "body": strip(body.group(1)) if body else None,
        "url": url,
    }


# -------------------------------------------------------------------- Website
def website(url="https://www.lovedby.ai/"):
    h = get(url)
    sec = re.search(r'<section id="testimonials".*?(?=<section |</main>)', h, re.S)
    if not sec:
        # lovedby.ai intermittently serves a page without the testimonials
        # section. Treat that as a failed fetch, not as "every testimonial gone".
        raise RuntimeError("no #testimonials section in response (flaky fetch?) - re-run")
    out, seen = [], set()
    for fig in re.findall(r"<figure.*?</figure>", sec.group(0), re.S):
        name = re.search(r'text-nws-ink">([^<]+)</span>', fig)
        role = re.search(r'text-nws-ink/50">([^<]+)</span>', fig)
        quote = re.search(r"<blockquote.*?</blockquote>", fig, re.S)
        if not name or name.group(1) in seen:
            continue
        seen.add(name.group(1))
        out.append({
            "author": html.unescape(name.group(1)).strip(),
            "role": html.unescape(role.group(1)).strip() if role else None,
            "body": strip(quote.group(0)).strip("“” ") if quote else None,
        })
    return out


# --------------------------------------------------------------------- report
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="stamp last_verified / status into reviews.json")
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = ap.parse_args()

    led = json.loads(LEDGER.read_text())
    reviews = led["reviews"]
    by_id = {r["id"]: r for r in reviews}
    rep = {"date": TODAY, "new": [], "lost": [], "drift": [], "manual": [], "errors": [], "ok": []}

    # ---- WordPress.org -----------------------------------------------------
    try:
        wp = wordpress(led["product"]["wp_slug"])
        p = led["platforms"]["WordPress.org"]
        for field, live in (("score", wp["score"]), ("ratings", wp["ratings"]),
                            ("distribution", wp["distribution"])):
            if p.get(field) != live:
                rep["drift"].append({"platform": "WordPress.org", "field": field,
                                     "published": p.get(field), "live": live})
        for field, live in (("version", wp["version"]), ("active_installs", wp["active_installs"])):
            if led["product"].get(field) != live:
                rep["drift"].append({"platform": "product", "field": field,
                                     "published": led["product"].get(field), "live": live})

        live_slugs = {r["slug"] for r in wp["reviews"]}
        known = {r["source_url"].rstrip("/").rsplit("/", 1)[-1]: r
                 for r in reviews if r["platform"] == "WordPress.org" and r.get("source_url")}
        for r in wp["reviews"]:
            if r["slug"] not in known:
                detail = wordpress_review(r["url"]) or r
                rep["new"].append({"platform": "WordPress.org", "title": detail.get("title") or r["title"],
                                   "rating": detail.get("rating"), "author": detail.get("author"),
                                   "date": detail.get("date"), "url": r["url"],
                                   "body": detail.get("body")})
        for slug, r in known.items():
            if r["status"] != "live":
                continue
            if slug not in live_slugs or status_of(r["source_url"]) == 404:
                rep["lost"].append({"id": r["id"], "platform": "WordPress.org",
                                    "title": r["title"], "author": r["author"],
                                    "rating": r["rating"], "url": r["source_url"]})
            else:
                rep["ok"].append(r["id"])
    except Exception as e:
        rep["errors"].append(f"WordPress.org: {e}")

    # ---- Website -----------------------------------------------------------
    try:
        live = website()
        names = {t["author"] for t in live}
        known = {r["author"]: r for r in reviews if r["platform"] == "Website"}
        for t in live:
            if t["author"] not in known:
                rep["new"].append({"platform": "Website", "author": t["author"],
                                   "role": t["role"], "body": t["body"],
                                   "url": "https://www.lovedby.ai/"})
        for name, r in known.items():
            if r["status"] != "live":
                continue
            if name not in names:
                rep["lost"].append({"id": r["id"], "platform": "Website", "title": None,
                                    "author": name, "rating": None,
                                    "url": "https://www.lovedby.ai/"})
            else:
                rep["ok"].append(r["id"])
                cur = next(t for t in live if t["author"] == name)
                if cur["body"] and r.get("body") and norm(cur["body"]) != norm(r["body"]):
                    rep["drift"].append({"platform": "Website", "field": f"quote:{name}",
                                         "published": r["body"][:90], "live": cur["body"][:90]})
    except Exception as e:
        rep["errors"].append(f"Website: {e}")

    # ---- browser-only platforms -------------------------------------------
    for name in BROWSER_ONLY:
        p = led["platforms"][name]
        rep["manual"].append({
            "platform": name, "url": p["source_url"],
            "published_score": p["score"], "published_count": p["ratings"],
            "live_ids": [r["id"] for r in reviews if r["platform"] == name and r["status"] == "live"],
        })

    if args.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        w = lambda s="": print(s)
        w(f"Review audit — {TODAY}")
        w("=" * 68)
        if rep["errors"]:
            w("\nERRORS")
            for e in rep["errors"]:
                w(f"  ! {e}")
        w(f"\nSCORE / STAT DRIFT ({len(rep['drift'])})")
        for d in rep["drift"] or []:
            w(f"  ~ {d['platform']}.{d['field']}: published {d['published']!r} -> live {d['live']!r}")
        if not rep["drift"]:
            w("  none - published figures match the sources")
        w(f"\nNEW AT SOURCE ({len(rep['new'])})")
        for n in rep["new"] or []:
            w(f"  + [{n['platform']}] {n.get('title') or n.get('author')}"
              + (f"  {n['rating']}*" if n.get("rating") else ""))
            w(f"      {n['url']}")
        if not rep["new"]:
            w("  none")
        w(f"\nGONE FROM SOURCE ({len(rep['lost'])})  -> move to archive.html")
        for l in rep["lost"] or []:
            w(f"  - [{l['platform']}] {l.get('title') or l.get('author')}  (id {l['id']})")
        if not rep["lost"]:
            w("  none")
        w(f"\nNEEDS A BROWSER ({len(rep['manual'])})  -> /review-audit walks these")
        for m in rep["manual"]:
            w(f"  ? {m['platform']}: page says {m['published_score']} / {m['published_count']} reviews")
            w(f"      {m['url']}")
        w(f"\nverified unchanged: {len(rep['ok'])}")

    if args.write:
        for rid in rep["ok"]:
            by_id[rid]["last_verified"] = TODAY
        for l in rep["lost"]:
            r = by_id[l["id"]]
            r.update(status="archived", quoted=False, lost_on=TODAY,
                     note=(r.get("note") or "") + f" Gone from source, detected {TODAY}.")
        led["audit"]["last_run"] = TODAY
        led["audit"]["next_due"] = (datetime.date.fromisoformat(TODAY)
                                    + datetime.timedelta(days=14)).isoformat()
        LEDGER.write_text(json.dumps(led, indent=2, ensure_ascii=False) + "\n")
        print(f"\nreviews.json updated (next due {led['audit']['next_due']})")
        if rep["new"] or rep["lost"] or rep["drift"]:
            print("New/lost/drift still need to be applied to index.html and archive.html.")
    return 1 if rep["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
