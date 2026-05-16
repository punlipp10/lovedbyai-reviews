# LovedByAI Reviews — Design System

## Theme Decision
Dark. Scene: a WordPress site owner at 10pm on their laptop, researching AI SEO tools before making a purchase decision. They've seen LovedByAI mentioned somewhere and are doing due diligence. The dark theme communicates authority and reduces eye strain for late-night research.

## Color Strategy
Committed — one saturated violet/indigo (LovedByAI's brand color) carries 30–40% of the surface.

## Color Palette (OKLCH)
```
--bg:              oklch(11% 0.01 268)    /* near-black, slight violet tint */
--surface:         oklch(16% 0.013 270)   /* card backgrounds */
--surface-raised:  oklch(21% 0.016 272)   /* featured/elevated cards */
--border:          oklch(30% 0.02 270)    /* visible borders */
--border-subtle:   oklch(24% 0.015 270)   /* subtle dividers */

--brand:           oklch(68% 0.22 282)    /* LovedByAI violet */
--brand-dim:       oklch(52% 0.16 282)
--brand-subtle:    oklch(24% 0.06 282)    /* tinted backgrounds */

--text:            oklch(93% 0.006 270)   /* primary text */
--text-muted:      oklch(58% 0.012 270)   /* secondary text */
--text-faint:      oklch(40% 0.01 270)    /* labels, captions */

--star:            oklch(82% 0.18 82)     /* warm amber stars */
--green-stat:      oklch(72% 0.2 150)     /* positive metrics */
```

## Typography
- Headings: Georgia / Palatino serif — editorial authority
- Body: System sans-serif stack — legibility and speed
- Body size: 17px / 1.65 line-height
- Heading scale: Display (clamp 42–80px) > H2 (clamp 28–44px) > H3 (26–38px) > Review title (18px)
- Cap body line length: 72ch max

## Spacing Rhythm
- Section padding: 96px top/bottom (64px for smaller sections)
- Container max-width: 1160px
- Card padding: 28px
- Grid gap: 20px (reviews), 16px (platforms), 80px (case studies)

## Layout Patterns
- Reviews: CSS columns masonry (3 col → 2 → 1)
- Case studies: 2-column editorial grid, alternating direction
- Testimonials: mixed-size grid (large featured + smaller singles)
- Platforms: 4-column scorecard grid
- FAQ: 1fr / 2fr split layout

## Do Not Use
- Gradient text
- Glassmorphism / backdrop-blur as decoration
- Side-stripe border accents
- Identical card grids (vary card sizes)
- Nested cards
- Hero-metric template
- Bounce/elastic animations
- Em dashes (use commas, colons, parentheses)

## Animation
- Fade-up on scroll via IntersectionObserver
- Timing: 0.5s ease-out
- No CSS layout property animation
- Staggered delays: 0.08s between platform cards
