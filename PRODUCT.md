# LovedByAI Reviews — Product Context

## Product Purpose
An independent review aggregation site for LovedByAI (lovedby.ai) — a WordPress plugin for AI search visibility (GEO/AEO). The site collects and presents real customer reviews from WordPress.org, G2, Trustpilot, and Google in one authoritative place.

## Register
brand — this is a marketing/landing page where design IS the product. The page needs to establish trust and authority.

## Target Users
- WordPress site owners googling "lovedbyai reviews" before purchase
- Digital marketers comparing GEO tools
- Bloggers and content creators evaluating AI SEO plugins
- Agencies researching tools for clients

## Core Goal
Rank #1 for "lovedbyai reviews" and related queries. Serve as the definitive, trustworthy source of social proof for LovedByAI.

## Brand Tone
Authoritative, honest, editorial. Not a sales page — a reference. Should feel like it was curated by a trusted reviewer, not written by marketing.

## Anti-References
- Do NOT look like a generic SaaS landing page
- Do NOT use hero-metric template (big number + gradient accent)
- Do NOT use glassmorphism
- Do NOT use gradient text
- Avoid the "dark blue SaaS tool" reflex — this is a review publication, not a product dashboard

## Key Content
- 6 five-star reviews from WordPress.org (verbatim)
- 2 case studies: The Working Artist (Crista Cloutier), Andre Guelmann
- 5 testimonials from lovedby.ai homepage
- Platform links: WordPress.org, G2, Trustpilot, Google Maps
- SEO-optimized FAQ section
- Full Schema.org structured data (SoftwareApplication, AggregateRating, Review, FAQPage)

## Key Stats

`reviews.json` is the source of truth for every score and count on the site. Do not
copy figures out of it into here or into `index.html` by hand: run
`python3 scripts/audit_reviews.py` (or the `/review-audit` skill) and let the audit
tell you what the sources say today. The numbers below are a snapshot from the
2026-09-07 audit, kept only for orientation.

- WordPress.org: 4.4/5 from 5 ratings (4 five-star, 1 two-star)
- G2: 4.7/5 from 3 reviews
- Trustpilot: 4/5 TrustScore from 4 reviews (weighted, not a plain average)
- lovedby.ai: 5 published testimonials, unrated
- Google Business Profile: 5/5 from 4 ratings, reported last and excluded from the scorecard row
- 1,000 active WordPress installations, plugin v1.7.28
- Featured in Forbes, WP Weekly, WordPress.org

## Review integrity

Reviews get deleted by the platforms that host them. The 2026-09-07 audit found all six
WordPress.org reviews the site had been quoting returned 404, and single reviews
had vanished from G2, Trustpilot and lovedby.ai. That is normal churn plus
platform moderation, not a bug, and it is why the site runs on a ledger:

- A review that disappears from its source moves to `archive.html` with the date
  it went. It is never deleted, because after a source 404s this site holds the
  only surviving copy of the text.
- Scores shown on the main page only ever count reviews that are live at source.
- `archive.html` carries no rating structured data, since none of it can be
  verified any more.
- Reviews that are live but not quotable (a two-star review, a five-star entry
  whose text is an unrelated complaint) still count toward the published score.
  Removing them from the score would be dishonest; quoting them would be silly.
