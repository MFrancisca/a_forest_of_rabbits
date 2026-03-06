# Una Nueva Esperanza

## What This Is

A personal art and research website at `www.unanuovasperanza.art` for sharing craft projects, tutorials, and original research on historical pigments used in medieval manuscripts. It serves as a learning resource for the broader art community — people who want to look up specific pigments or browse and discover the history of color-making. It replaces an existing Google Sites presence with a proper, maintainable platform.

## Core Value

Visitors can easily explore and access historical pigment knowledge and craft tutorials; the owner can add new content in minutes without friction.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Filterable pigment database — searchable by color family, pigment family, manuscript, country, and time period
- [ ] Editorial content (craft tutorials + art research articles) managed via CMS
- [ ] Content migrated from Google Sites (<10 articles, hot swap — new site replaces Google Sites)
- [ ] Clean, navigable site design accessible to a general art audience
- [ ] Wagtail admin for all content management (no code required for routine updates)
- [ ] Deployed and live on custom domain (Railway + Cloudflare)

### Out of Scope

- Real-time chat or community features — not relevant to current goals
- Mobile app — web-first
- OAuth / social login — no user accounts needed (read-only public site)
- Comments or user-generated content — v1 is a publishing platform, not a community

## Context

- Existing site: Google Sites at `www.unanuovasperanza.art` (live, active — this is a hot swap replacement)
- Content volume: <10 articles to migrate from Google Sites
- Pigment database is new — no existing structured data, will be built fresh and populated via CSV import + Wagtail admin
- Stack already decided (from prior planning): Django 5 + Wagtail 6 + HTMX + Alpine.js + Tailwind CSS + PostgreSQL
- Hosting already decided: Railway (Hobby $5/mo) + Cloudflare (DNS + CDN + SSL)
- Media storage: Cloudflare R2 (S3-compatible)
- Owner maintains the site — prefers Wagtail admin for content, comfortable with occasional code changes for new features
- Python package name: `esperanza` (used in config/, import paths)

## Constraints

- **Tech Stack**: Django 5 + Wagtail 6 + HTMX + Alpine.js + Tailwind CSS + PostgreSQL — decided, not up for revision
- **Hosting**: Railway Hobby plan ($5/mo) — affects resource limits and deployment approach
- **Maintenance time**: Updates must be achievable in short sessions; code must be clean enough for the owner to understand and modify
- **No JS build step in dev**: Tailwind via CDN for development, CLI for production (from migration plan)
- **Zero downtime goal**: New site must be fully functional before DNS cutover from Google Sites

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Wagtail for editorial content, plain Django app for pigment DB | Editorial needs CMS UI; pigment filtering needs full query control | — Pending |
| HTMX for filtering (no JS framework) | Server-side filtering with no frontend build complexity | — Pending |
| Cloudflare R2 for media storage | Cost-effective, CDN-backed, S3-compatible | — Pending |
| Railway for hosting | Simple Docker deploy, 1-click Postgres, low devops overhead | — Pending |
| Tailwind CDN in dev / CLI in prod | No build step in development; optimized bundle in production | — Pending |

---
*Last updated: 2026-03-06 after initialization*
