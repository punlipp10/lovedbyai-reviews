#!/usr/bin/env python3
"""
Generate archive.html from reviews.json.

Every review with status == "archived" is rendered here: reviews that were once
published on the main page and are no longer at their source. This page carries
NO Review or AggregateRating structured data - the sources are gone, so marking
them up as ratings would be fabricated review markup.

    python3 scripts/build_archive.py
"""
import json, html, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
led = json.loads((ROOT / "reviews.json").read_text())

PLATFORM = {
    "WordPress.org": ("wp", "review-logos/wordpress-logo.png"),
    "G2":            ("g2", "review-logos/g2-logo.png"),
    "Trustpilot":    ("tp", "review-logos/trustpilot-logo.png"),
    "Google":        ("gm", "review-logos/google-logo.png"),
    "Website":       ("web", None),
}
ORDER = ["WordPress.org", "G2", "Trustpilot", "Website", "Google"]

WHY = {
    "WordPress.org": "Removed by WordPress.org. Each source URL below returns 404. "
                     "WordPress.org moderates plugin reviews and does not notify "
                     "plugin authors when it removes one.",
    "G2":            "No longer listed among the reviews G2 shows for the product.",
    "Trustpilot":    "No longer listed among the reviews Trustpilot shows for lovedby.ai.",
    "Website":       "No longer published on lovedby.ai.",
    "Google":        "No longer shown on the Google Business Profile.",
}


def esc(s):
    return html.escape(s or "", quote=False)


def stars(rating):
    if not rating:
        return ""
    full = int(rating)
    half = rating - full >= 0.5
    out = '<span class="stars">' + "★" * full + "</span>"
    if half:
        out += '<span class="star-half">★</span>'
    out += '<span class="stars stars-empty">' + "★" * (5 - full - (1 if half else 0)) + "</span>"
    return out


def body_html(text):
    paras = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    return "\n            ".join(f"<p>{esc(p)}</p>" for p in paras)


def card(r):
    cls, logo = PLATFORM[r["platform"]]
    icon = (f'<img class="tag-icon" src="{logo}" alt="{esc(r["platform"])}">' if logo else "")
    title = f'<div class="a-title">&ldquo;{esc(r["title"])}&rdquo;</div>' if r.get("title") else ""
    rating = f'<div class="a-stars">{stars(r["rating"])}</div>' if r.get("rating") else ""
    lost = esc(r.get("lost_on") or "")
    src = r.get("source_url")
    dead = r["platform"] == "WordPress.org"
    link = (f'<span class="a-src a-src-dead">source removed (404)</span>' if dead
            else f'<a href="{esc(src)}" target="_blank" rel="noopener" class="a-src">{esc(r["platform"])} &#8599;</a>')
    return f"""        <article class="a-card {cls}">
          <div class="a-tag {cls}">{icon}{esc(r['platform'])}</div>
          {rating}
          {title}
          <div class="a-body">
            {body_html(r.get('body'))}
          </div>
          <footer class="a-foot">
            <div>
              <div class="a-author">{esc(r.get('author'))}</div>
              <div class="a-role">{esc(r.get('role') or '')}</div>
            </div>
            {link}
          </footer>
          <div class="a-meta">Delisted {lost}</div>
        </article>"""


arch = [r for r in led["reviews"] if r["status"] == "archived"]
groups = {p: [r for r in arch if r["platform"] == p] for p in ORDER}
groups = {p: v for p, v in groups.items() if v}
total = len(arch)
built = datetime.date.today().isoformat()

sections = []
for p, rows in groups.items():
    cls, _ = PLATFORM[p]
    sections.append(f"""      <section class="a-group">
        <div class="a-group-head">
          <h2 class="a-group-title">{esc(p)}</h2>
          <div class="a-group-count">{len(rows)} delisted</div>
        </div>
        <p class="a-group-why">{esc(WHY[p])}</p>
        <div class="a-grid">
{chr(10).join(card(r) for r in rows)}
        </div>
      </section>""")

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review Archive | LovedByAI Reviews</title>
<meta name="description" content="Reviews that were once published on lovedbyaireviews.com and have since been removed by their source platform, kept here for transparency.">
<meta name="robots" content="noindex, follow">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<!-- No Review or AggregateRating structured data on this page by design: these
     reviews are no longer retrievable at their source, so rating markup for them
     would not be verifiable. See .claude/skills/review-audit/SKILL.md. -->
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: oklch(11% 0.01 268);
    --surface: oklch(16% 0.013 270);
    --border: oklch(30% 0.02 270);
    --border-subtle: oklch(24% 0.015 270);
    --brand: oklch(68% 0.22 282);
    --brand-subtle: oklch(24% 0.06 282);
    --text: oklch(93% 0.006 270);
    --text-muted: oklch(74% 0.012 270);
    --text-faint: oklch(62% 0.01 270);
    --star: oklch(82% 0.18 82);
    --star-bg: oklch(48% 0.06 82);
    --wp-blue: oklch(61% 0.17 243);
    --g2-orange: oklch(67% 0.2 42);
    --tp-green: oklch(62% 0.2 153);
    --google-blue: oklch(62% 0.20 252);
    --radius: 12px;
    --radius-lg: 20px;
    --font-serif: Georgia, "Palatino Linotype", Palatino, "Book Antiqua", serif;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  body {{
    background: var(--bg); color: var(--text); font-family: var(--font-sans);
    font-size: 17px; line-height: 1.65; -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 1160px; margin: 0 auto; padding: 0 24px; }}
  .stars {{ display: inline-flex; gap: 2px; color: var(--star); letter-spacing: -0.5px; }}
  .stars-empty {{ color: var(--star-bg); }}
  .star-half {{
    color: var(--star); position: relative; display: inline-block;
    background: linear-gradient(90deg, var(--star) 50%, var(--star-bg) 50%);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  }}

  nav {{ border-bottom: 1px solid var(--border-subtle); padding: 20px 0; }}
  .nav-inner {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; }}
  .nav-logo {{ font-family: var(--font-serif); font-size: 19px; letter-spacing: -0.01em; }}
  .nav-logo span {{ color: var(--text-faint); }}
  .nav-back {{
    color: var(--text-muted); text-decoration: none; font-size: 14px;
    border: 1px solid var(--border); border-radius: 999px; padding: 7px 16px;
    transition: color .2s ease, border-color .2s ease;
  }}
  .nav-back:hover {{ color: var(--text); border-color: var(--brand); }}

  header.a-hero {{ padding: 72px 0 48px; border-bottom: 1px solid var(--border-subtle); }}
  .a-label {{
    font-size: 12px; text-transform: uppercase; letter-spacing: 0.09em;
    color: var(--text-faint); margin-bottom: 18px;
  }}
  h1 {{
    font-family: var(--font-serif); font-weight: 400; letter-spacing: -0.02em;
    font-size: clamp(38px, 6vw, 62px); line-height: 1.08; margin-bottom: 22px;
  }}
  .a-lede {{ color: var(--text-muted); max-width: 68ch; font-size: 18px; }}
  .a-lede + .a-lede {{ margin-top: 14px; }}
  .a-lede strong {{ color: var(--text); font-weight: 600; }}
  .a-stat-row {{ display: flex; flex-wrap: wrap; gap: 14px; margin-top: 30px; }}
  .a-stat {{
    background: var(--surface); border: 1px solid var(--border-subtle);
    border-radius: var(--radius); padding: 14px 20px;
  }}
  .a-stat-n {{ font-family: var(--font-serif); font-size: 26px; line-height: 1; }}
  .a-stat-l {{ font-size: 12px; color: var(--text-faint); text-transform: uppercase;
               letter-spacing: 0.07em; margin-top: 7px; }}

  main {{ padding: 56px 0 16px; }}
  .a-group {{ margin-bottom: 68px; }}
  .a-group-head {{ display: flex; align-items: baseline; gap: 14px; margin-bottom: 10px; }}
  .a-group-title {{ font-family: var(--font-serif); font-weight: 400; font-size: 30px;
                    letter-spacing: -0.01em; }}
  .a-group-count {{
    font-size: 12px; color: var(--text-faint); text-transform: uppercase;
    letter-spacing: 0.07em; border: 1px solid var(--border); border-radius: 999px;
    padding: 3px 11px;
  }}
  .a-group-why {{ color: var(--text-muted); font-size: 15px; max-width: 72ch; margin-bottom: 26px; }}
  .a-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 20px; }}

  .a-card {{
    background: var(--surface); border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg); padding: 26px; display: flex; flex-direction: column;
  }}
  .a-tag {{
    display: inline-flex; align-items: center; gap: 7px; align-self: flex-start;
    font-size: 12px; text-transform: uppercase; letter-spacing: 0.07em;
    color: var(--text-faint); margin-bottom: 14px;
  }}
  .a-tag .tag-icon {{ width: 15px; height: 15px; object-fit: contain; opacity: .75; }}
  .a-card.wp {{ border-top: 1px solid color-mix(in oklch, var(--wp-blue) 35%, var(--border-subtle)); }}
  .a-card.g2 {{ border-top: 1px solid color-mix(in oklch, var(--g2-orange) 35%, var(--border-subtle)); }}
  .a-card.tp {{ border-top: 1px solid color-mix(in oklch, var(--tp-green) 35%, var(--border-subtle)); }}
  .a-card.web {{ border-top: 1px solid color-mix(in oklch, var(--brand) 35%, var(--border-subtle)); }}
  .a-stars {{ font-size: 15px; margin-bottom: 12px; }}
  .a-title {{ font-family: var(--font-serif); font-size: 19px; line-height: 1.3; margin-bottom: 12px; }}
  .a-body {{ color: var(--text-muted); font-size: 15.5px; }}
  .a-body p + p {{ margin-top: 12px; }}
  .a-foot {{
    display: flex; align-items: center; gap: 12px; margin-top: 22px; padding-top: 18px;
    border-top: 1px solid var(--border-subtle);
  }}
  .a-author {{ font-size: 14px; font-weight: 600; }}
  .a-role {{ font-size: 12.5px; color: var(--text-muted); }}
  .a-src {{
    margin-left: auto; font-size: 12px; color: var(--text-muted); text-decoration: none;
    white-space: nowrap;
  }}
  .a-src:hover {{ color: var(--brand); }}
  .a-src-dead {{ color: var(--text-faint); text-decoration: line-through; }}
  .a-meta {{
    font-size: 11.5px; color: var(--text-muted); text-transform: uppercase;
    letter-spacing: 0.07em; margin-top: 12px;
  }}

  footer {{ border-top: 1px solid var(--border-subtle); padding: 40px 0 64px; margin-top: 40px; }}
  .a-foot-note {{ color: var(--text-muted); font-size: 14px; max-width: 76ch; line-height: 1.6; }}
  .a-foot-note a {{ color: var(--text); text-decoration: underline; text-underline-offset: 2px; }}
  .a-foot-note a:hover {{ color: var(--brand); }}

  @media (max-width: 600px) {{
    header.a-hero {{ padding: 48px 0 36px; }}
    .a-grid {{ grid-template-columns: 1fr; }}
    .a-card {{ padding: 22px; }}
  }}
</style>
</head>
<body>

<nav>
  <div class="container nav-inner">
    <div class="nav-logo">LovedByAI <span>Reviews</span></div>
    <a href="index.html" class="nav-back">&larr; Back to reviews</a>
  </div>
</nav>

<header class="a-hero">
  <div class="container">
    <div class="a-label">Review Archive</div>
    <h1>Reviews that are no longer at their source.</h1>
    <p class="a-lede">This page holds every review this site once published that has since
      been removed by the platform it was posted on. Nothing here is counted in any score
      shown on the main page, and none of it carries rating markup, because none of it can
      be checked at source any more.</p>
    <p class="a-lede">It is kept because deleting it would be the dishonest option. A review
      aggregator that quietly drops reviews when they vanish is telling you only the half of
      the story that flatters it.</p>
    <div class="a-stat-row">
      <div class="a-stat"><div class="a-stat-n">{total}</div><div class="a-stat-l">Reviews archived</div></div>
      <div class="a-stat"><div class="a-stat-n">{len(groups)}</div><div class="a-stat-l">Platforms affected</div></div>
      <div class="a-stat"><div class="a-stat-n">{built}</div><div class="a-stat-l">Last audited</div></div>
    </div>
  </div>
</header>

<main>
  <div class="container">
{chr(10).join(sections)}
  </div>
</main>

<footer>
  <div class="container">
    <p class="a-foot-note">Review text is reproduced as it was published on this site, which
      for the WordPress.org entries is now the only surviving record of it. Scores and counts
      on the <a href="index.html">main reviews page</a> reflect only reviews that are live at
      their source today. Audited every two weeks. Visit
      <a href="https://www.lovedby.ai" target="_blank" rel="noopener">www.lovedby.ai</a> to learn more.</p>
  </div>
</footer>

</body>
</html>
"""

(ROOT / "archive.html").write_text(doc)
print(f"archive.html — {total} archived reviews across {len(groups)} platforms")
for p, rows in groups.items():
    print(f"  {p:<15} {len(rows)}")
