---
name: review-audit
description: Run the recurring review audit for lovedbyaireviews.com — find new and lost reviews across WordPress.org, G2, Trustpilot, the lovedby.ai website and Google, correct any published score that has drifted, move vanished reviews to the archive page, and stage the result on a branch. Use when asked to audit reviews, check for new or lost reviews, refresh the review scores, or when the bi-weekly review check is due.
---

# Review audit

The site publishes other people's words and other platforms' numbers. Both change
without warning. This audit keeps every figure on the page traceable to a source
that says the same thing today.

**Cadence:** every 14 days. `reviews.json` → `audit.next_due` holds the date.

## Ground rules

1. **Never write a number you did not just read from the source.** No estimating,
   no carrying a stale figure forward, no averaging your way to a nicer score.
2. **A review is live only if you loaded its source and saw it.** Not "probably
   still there".
3. **Never push, never deploy.** Stage on a branch, write the report, stop.
4. `archive.html` carries **no** `Review`, `AggregateRating` or `ratingValue`
   structured data. Its reviews no longer exist at their source; marking them up
   as ratings would be fabricated review markup. Human-readable only.
5. Trustpilot's **TrustScore is not the mean of its stars** — it weights recency
   and volume. Publish the TrustScore Trustpilot displays (4.1 as of 2026-10-01),
   never a computed average of the individual reviews (which would read 5.0) as
   Trustpilot's score.
6. Website testimonials have no verifiable star rating. They get a **count, not a
   score**, and stay out of every structured-data rating and the overall score.
7. **The overall score** (hero, `.overall-rating` explainer, `aggregateRating`) is
   a straight mean of every live third-party review — WordPress.org, G2,
   Trustpilot, Google — each counted once at the rating its own author gave it.
   Dean chose this on 2026-09-14 and confirmed it on 2026-10-01. Recompute it
   from the per-review ratings you just read, and keep `reviews.json` →
   `aggregate` (points, n, breakdown, `computed`) in step. Every live review
   counts, including unquoted ones (the 2★ and the "spam" 5★ on WordPress.org)
   and Google's text-less ratings. Never use platform scores or the TrustScore
   as inputs.
8. The top scorecard row is WordPress.org, G2, Trustpilot, Google. Website
   testimonials are not in it. The Google section still renders last.

## Step 1 — the automated half

```bash
python3 scripts/audit_reviews.py
```

Covers WordPress.org (plugin API + forum + per-review 404 checks) and the
lovedby.ai testimonials. Reports drift, new, lost, and what still needs a browser.

WordPress.org is the one fully machine-verifiable source: the API returns
`rating` out of 100, `num_ratings`, the star distribution, `version` and
`active_installs`. Trust it over anything on the page.

## Step 2 — the browser half

G2, Trustpilot and Google **all return 403 to scripted requests**. curl and
`urllib` cannot see them. Use the browser tools.

If the Browser pane is hidden, clicks and scrolls time out — read with
`get_page_text` / `find`, and drive the DOM with `javascript_tool` instead.

### Trustpilot — `https://www.trustpilot.com/review/lovedby.ai`
Cloudflare shows "Verifying your connection" first; wait ~5s and read again.
`get_page_text` returns the TrustScore, the review count, the star distribution
and every review with author, country, date and body.

### G2 — `https://www.g2.com/products/lovedbyai-geo-for-wordpress/reviews`
Wait ~6s after navigating. `get_page_text` gives the aggregate, the count and
each review's title, per-review score, reviewer name, role, segment and the
three G2 answer fields. Record the **"What do you like best"** answer as the
quotable body — it is the one verbatim field a pull-quote can come from.
Note any review G2 labels **Incentivized** or **Source: G2 invite**; that
belongs in the ledger `note`.

### Google — `https://www.google.com/maps/search/LovedByAI+Yigal+Alon+114+Tel+Aviv?hl=en`
`share.google` short links are refused by the browser tool; go to Maps directly.
Wait ~8s. The aggregate and count come from `get_page_text`. For the individual
reviews, extract from the DOM — the visible list lazy-loads and duplicates nodes:

```js
[...document.querySelectorAll('button')]
  .filter(b => /More reviews/i.test(b.textContent || ''))
  .forEach(b => b.click());
await new Promise(r => setTimeout(r, 4000));
const seen = new Set();
[...document.querySelectorAll('[data-review-id]')]
  .map(n => ({
    id: n.getAttribute('data-review-id'),
    stars: n.querySelector('[aria-label*="star"]')?.getAttribute('aria-label'),
    name: n.querySelector('button[aria-label^="Photo of"]')?.getAttribute('aria-label')?.replace(/^Photo of /, ''),
    when: [...n.querySelectorAll('span')].map(s => s.textContent).find(t => /ago$/.test((t || '').trim())),
    text: n.querySelector('[class*="wiI7pd"]')?.textContent
  }))
  .filter(r => r.text && !seen.has(r.id) && seen.add(r.id));
```

Google counts **ratings without text** in its total, so the review count is
normally higher than the number of quotable reviews. Say so in the ledger note
rather than making the numbers agree.

## Step 3 — classify

For every review, compare live state against `reviews.json`:

| Situation | Do this |
|---|---|
| At source, in ledger | `last_verified` = today |
| At source, not in ledger | **new** — add with `first_seen`, decide whether to quote |
| In ledger as `live`, not at source | **lost** — `status: archived`, `quoted: false`, `lost_on` = today |
| Published figure ≠ live figure | **drift** — correct the page |

A review is only quoted on the main page if it is `status: live` **and** reads as
a genuine product review. Two live WordPress.org entries fail that second test —
a 2★ review and a 5★ entry whose text is an email complaint. Both still **count
in the WordPress.org score**; neither is quoted. Keep it that way: dropping them
from the score would be dishonest, quoting them would be absurd.

## Step 4 — apply

```bash
python3 scripts/audit_reviews.py --write   # stamps ledger status + next_due
```

Then, by hand, in `index.html`:

- **Scorecard** (`.platforms-grid`) — WordPress.org, G2, Trustpilot, Google.
  Each card's score, star row and count must match its platform in `reviews.json`.
  Perfect scores render as `5`, not `5.0`.
- **Review sections** — quote exactly the `quoted: true` reviews for that platform.
- **Google section** — last content section before the platform links.
- **Testimonials** — the `Website` platform entries.
- **Overall score** — hero score and count, the `.overall-rating` explainer
  (per-platform detail, points ÷ n), and `aggregateRating` in the `@graph`
  (`ratingValue` = rounded mean, `ratingCount`/`reviewCount` = n). See rule 7.
- **`Review` nodes** — one per `quoted: true` review, with its real per-review
  rating (G2's 4.5s are 4.5, not 5).
- **`softwareVersion`** — from the API.

And in `archive.html`: move each newly-lost review across, with its `lost_on`
date and why it went. Keep the body text — once a source 404s, this page is the
only surviving record, so never delete an archived body.

## Step 5 — report and stop

```bash
git checkout -b review-audit-$(date +%Y-%m-%d)
git add -A && git commit -m "Review audit <date>: <n> new, <n> lost, <n> corrected"
```

Then tell Dean, in plain terms: what is new, what vanished, which published
numbers were wrong and what they are now. Flag anything that looks like source
moderation rather than normal churn — a platform deleting several reviews at once
is a signal about the account, not a content problem.

Do not push. Do not deploy. He merges.
