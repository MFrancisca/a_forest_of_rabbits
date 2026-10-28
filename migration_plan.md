# Una Nueva Esperanza — Website Migration & Build Plan
**www.unanuovasperanza.art** | Google Sites → Django + Wagtail + HTMX
**Prepared:** February 2026
**Stack:** Django 5 + Wagtail 6 + HTMX + Alpine.js + Tailwind CSS + PostgreSQL
**Hosting:** Railway (Hobby $5/mo) + Cloudflare (DNS + CDN)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Full Tech Stack](#2-full-tech-stack)
3. [Data Models](#3-data-models)
4. [Project Structure](#4-project-structure)
5. [HTMX Filtering Pattern](#5-htmx-filtering-pattern)
6. [Content Migration from Google Sites](#6-content-migration-from-google-sites)
7. [Docker Setup](#7-docker-setup)
8. [Railway Deployment](#8-railway-deployment)
9. [Build Sequence](#9-build-sequence-session-by-session-plan)
10. [Requirements Files](#10-requirements-files)
11. [Action Items Before Session 1](#11-action-items-before-session-1)

---

## 1. Project Overview

### 1.1 Goals
- Preserve and improve presentation of existing content (craft projects, tutorials, art research articles).
- Add a new, fully filterable **Pigment Database** — a structured reference of pigments used in medieval manuscripts, sliceable by color family, pigment family, manuscript, country, and time period.
- Provide a modern, performant web experience without a full JavaScript frontend framework.

### 1.2 Content Areas

| Area | Type | Notes |
|---|---|---|
| Craft Projects & Tutorials | Editorial (CMS) | Steps, images, tags — managed in Wagtail |
| Historic Art Research | Editorial (CMS) | Long-form articles, references |
| Pigment Database | Structured Data | Django models, faceted HTMX filtering |

### 1.3 Architecture Decision

> **Key Design Choice:**
> Editorial content (tutorials, articles) lives in **Wagtail as Pages** — rich admin UI and CMS features.
> The Pigment Database is a separate **Django app with plain models** — full query control for filtering.
> Both share a single base template and navigation. They feel like one site but are architecturally independent.

---

## 2. Full Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| CMS / Backend | Django 5 + Wagtail 6 | Familiar, production-ready CMS |
| Dynamic UI | HTMX + Alpine.js | Server-side filtering, no JS build step |
| CSS | Tailwind CSS (CDN dev, CLI prod) | Utility-first, minimal integration overhead |
| Database | PostgreSQL 16 | Full-text search, proper indexing |
| Search / Filter | django-filter + Wagtail Search | Sufficient at <1000 records; zero extra infra |
| Media Storage | Cloudflare R2 (S3-compatible) | Cheap, fast CDN for images |
| Containerization | Docker + Docker Compose | Dev/prod parity, easy Railway deploy |
| Hosting | Railway Hobby ($5/mo) | 1-click Postgres, Docker deploy, low devops |
| DNS + CDN | Cloudflare (free) | SSL, caching, DDoS protection |

### Tailwind Strategy
- **Development:** Use the Tailwind CDN play script — just a `<script>` tag, no build step.
- **Production:** Switch to the Tailwind CLI to purge unused classes (bundle: ~3MB → ~10KB).

---

## 3. Data Models

### 3.1 Pigment App (`pigments/models.py`)

All taxonomy tables are registered as **Wagtail Snippets** for admin management.

#### Taxonomy / Lookup Tables

```
ColorFamily    — name                              e.g. Reds, Browns, Blues
PigmentFamily  — name                              e.g. Ochres, Mercury-based, Carbon
Brand          — name, website                     e.g. Winsor & Newton
Paint          — brand FK, name, hex_color         e.g. Yellow Ochre #D4A843
Country        — name                              e.g. France, Flanders
Manuscript     — name, country FK, date_start,     e.g. Book of Kells, 800 AD
                 date_end, notes
```

#### Core: Pigment

```python
class Pigment(ClusterableModel):
    name            = CharField
    color_family    = FK → ColorFamily
    pigment_family  = FK → PigmentFamily
    description     = TextField
    manuscripts     = M2M through PigmentManuscript
    # inline panels: formulas, manuscript_links, images
```

#### Formula System

A Pigment can have **multiple Formulas** (one per brand or alternative mix). Each Formula has multiple FormulaParts.

```python
class Formula(ClusterableModel):
    pigment  = ParentalKey → Pigment   (related_name: formulas)
    brand    = FK → Brand
    notes    = TextField               e.g. "works best on rough paper"

class FormulaPart:
    formula  = FK → Formula            (related_name: parts)
    paint    = FK → Paint
    parts    = DecimalField            e.g. 3.0 = "3 parts"
```

**Example:**
```
Pigment: Vermillion  |  Brand: Winsor & Newton
  3.0 parts  Cadmium Red Medium   #E34234
  0.5 parts  Yellow Ochre         #D4A843
  0.2 parts  Titanium White       #FFFFFF

Same pigment, alternative formula  |  Brand: Schmincke
  2.5 parts  Cadmium Red Hue      #D63C2E
  1.0 parts  Burnt Sienna         #8B4513
```

#### M2M Bridge: PigmentManuscript

```python
class PigmentManuscript:
    pigment    = ParentalKey → Pigment  (related_name: manuscript_links)
    manuscript = FK → Manuscript
    notes      = TextField              # context for this specific usage
```

#### Images

```python
class PigmentImage:
    pigment  = ParentalKey → Pigment   (related_name: images)
    image    = FK → wagtailimages.Image
    caption  = CharField
```

### 3.2 Editorial App Models (Wagtail `blog/`)

```python
HomePage(Page)           # root landing page
BlogIndexPage(Page)      # lists all articles
BlogPage(Page)
    title, intro, body (RichTextField), cover_image, tags
    category = choices: CRAFT | RESEARCH
```

---

## 4. Project Structure

```
unanuovasperanza/
├── config/                  # Django settings package
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── core/                    # Shared: base templates, static, utils
│   ├── templates/
│   │   ├── base.html        # Tailwind + HTMX + Alpine loaded here
│   │   └── includes/        # nav.html, footer.html, pagination.html
│   └── static/
├── blog/                    # Wagtail pages: tutorials + art research
│   ├── models.py
│   ├── templates/blog/
│   └── wagtail_hooks.py
├── pigments/                # Django app: pigment database
│   ├── models.py
│   ├── views.py
│   ├── filters.py           # django-filter FilterSet
│   ├── urls.py
│   └── templates/pigments/
│       ├── list.html        # full page with filter sidebar
│       ├── _results.html    # HTMX partial (just the grid)
│       └── detail.html
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── production.txt
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── .env.example
```

---

## 5. HTMX Filtering Pattern

### How It Works

Two-panel layout: filter sidebar (left) + results grid (right).
When any filter changes → HTMX sends GET → Django filters queryset → returns `_results.html` partial → HTMX swaps it in.
No page reload. No JavaScript logic. All filtering happens in Python.

### `list.html` — Full Page

```html
<div id="filter-sidebar">
  <form hx-get="/pigments/"
        hx-target="#results-grid"
        hx-trigger="change"
        hx-push-url="true">
    {{ filter.form }}
  </form>
</div>
<div id="results-grid">
  {% include "pigments/_results.html" %}
</div>
```

### `_results.html` — HTMX Partial

```html
{% for pigment in pigments %}
  <div class="pigment-card">
    <span class="color-swatch" style="background: {{ pigment.color_family.hex }}"></span>
    <h3>{{ pigment.name }}</h3>
    <p>{{ pigment.pigment_family }}</p>
  </div>
{% empty %}
  <p>No pigments match these filters.</p>
{% endfor %}
```

### `views.py`

```python
def pigment_list(request):
    qs = Pigment.objects.select_related('color_family', 'pigment_family')
    f = PigmentFilter(request.GET, queryset=qs)

    if request.htmx:  # django-htmx adds this
        return render(request, 'pigments/_results.html', {'pigments': f.qs})

    return render(request, 'pigments/list.html', {'filter': f, 'pigments': f.qs})
```

### `filters.py`

```python
import django_filters
from .models import Pigment, ColorFamily, PigmentFamily, Manuscript

class PigmentFilter(django_filters.FilterSet):
    color_family   = django_filters.ModelChoiceFilter(queryset=ColorFamily.objects.all())
    pigment_family = django_filters.ModelChoiceFilter(queryset=PigmentFamily.objects.all())
    manuscript     = django_filters.ModelChoiceFilter(queryset=Manuscript.objects.all(),
                         field_name='manuscripts')
    country        = django_filters.CharFilter(field_name='manuscripts__country__name',
                         lookup_expr='icontains')
    date_from      = django_filters.NumberFilter(field_name='manuscripts__date_start',
                         lookup_expr='gte')
    date_to        = django_filters.NumberFilter(field_name='manuscripts__date_end',
                         lookup_expr='lte')
    name           = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Pigment
        fields = ['color_family', 'pigment_family', 'manuscript',
                  'country', 'date_from', 'date_to', 'name']
```

> **Note:** `hx-push-url="true"` makes filters bookmark-able and shareable. Filter state lives in the URL — free with one HTMX attribute.

---

## 6. Content Migration from Google Sites

### 6.1 What Google Sites Gives You

Google Sites has no export API. Options:
- **Google Takeout** — exports ZIP with raw HTML files, one per page ✅ use this
- Download as PDF — not useful
- Manual copy-paste — fallback for edge cases

### 6.2 Migration Strategy by Content Type

| Content | Strategy | How |
|---|---|---|
| Craft tutorials | Semi-automated | Parse HTML → markdown → paste into Wagtail |
| Art research | Semi-automated | Same as above |
| Images | Download + re-upload | wget or browser save → Wagtail media library |
| Pigment data | Manual entry (first time) | Fill CSV template → run import script |
| Navigation | Rebuild manually | Wagtail page tree reflects new IA |

### 6.3 Google Takeout Migration Script

**Step 1 — Export**
1. Go to takeout.google.com
2. Deselect all → select only "Sites"
3. Export and download ZIP
4. Unzip — get a folder of `.html` files, one per page

**Step 2 — Convert HTML to Markdown**

```python
# migrate_sites.py
# pip install beautifulsoup4 markdownify
import os, re
from pathlib import Path
from bs4 import BeautifulSoup
import markdownify

INPUT_DIR  = Path('./takeout/Sites')
OUTPUT_DIR = Path('./migrated_content')
OUTPUT_DIR.mkdir(exist_ok=True)

for html_file in INPUT_DIR.glob('**/*.html'):
    soup = BeautifulSoup(html_file.read_text(), 'html.parser')

    # Google Sites wraps content in div.sites-layout-tile
    content_div = soup.find('div', class_='sites-layout-tile')
    if not content_div:
        content_div = soup.find('article') or soup.find('main') or soup.body

    # Remove nav/header/footer boilerplate
    for tag in content_div.find_all(['nav', 'header', 'footer']):
        tag.decompose()

    md = markdownify.markdownify(str(content_div), heading_style='ATX')
    md = re.sub(r'\n{3,}', '\n\n', md).strip()

    out_path = OUTPUT_DIR / html_file.with_suffix('.md').name
    out_path.write_text(md)
    print(f'Converted: {html_file.name} → {out_path.name}')
```

**Step 3 — Review Markdown Files**

Common things to fix manually:
- Image references — point to Google's CDN, download them separately
- Embedded Google Drawings/Slides — screenshot or replace
- Tables — markdownify handles them but verify
- Tag each file as `CRAFT` or `RESEARCH` category

**Step 4 — Bulk Import into Wagtail**

```python
# blog/management/commands/import_articles.py
from django.core.management.base import BaseCommand
from pathlib import Path
from blog.models import BlogIndexPage, BlogPage
import markdown

class Command(BaseCommand):
    def handle(self, *args, **options):
        index = BlogIndexPage.objects.first()
        for md_file in Path('./migrated_content').glob('*.md'):
            lines = md_file.read_text().splitlines()
            title = lines[0].lstrip('# ').strip()
            body_html = markdown.markdown('\n'.join(lines[1:]))

            page = BlogPage(
                title=title,
                body=body_html,
                slug=md_file.stem.lower().replace(' ', '-'),
            )
            index.add_child(instance=page)
            self.stdout.write(f'Imported: {title}')
```

### 6.4 Pigment Data — CSV Import

Since pigment data is new (not on Google Sites), the workflow is:
1. Fill CSV template (provided Session 2)
2. Run management command to load CSV into database
3. Add images and formulas via Wagtail admin

**CSV columns:** `name, color_family, pigment_family, description, manuscript_names, date_start, date_end, country`

### 6.5 Images

1. Bulk-download images from Google Sites (browser extension or wget) while still live
2. Organize by page/article
3. Upload to Wagtail media library
4. Re-link in articles after import

**Naming convention:** `pigment-vermillion-ref1.jpg`, `craft-embroidery-step3.jpg`
Wagtail's media library has no folders — naming is your organization system. Use Wagtail image tagging for pigment reference images.

---

## 7. Docker Setup

### `docker-compose.yml` (Development)

```yaml
version: '3.9'
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - '8000:8000'
    env_file: .env
    depends_on:
      - db
  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: unanuovasperanza
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
volumes:
  postgres_data:
```

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc
COPY requirements/base.txt requirements/production.txt ./requirements/
RUN pip install -r requirements/production.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 8. Railway Deployment

### Initial Setup
1. Create account at railway.app
2. Install CLI: `npm install -g @railway/cli`
3. Connect GitHub repo: `railway link`
4. Add PostgreSQL service from Railway dashboard
5. Set environment variables (DATABASE_URL is auto-injected)
6. Deploy: `git push` — Railway detects Dockerfile and builds

### Environment Variables

| Variable | Value / Notes |
|---|---|
| `DATABASE_URL` | Auto-injected by Railway Postgres plugin |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `yourdomain.com,yourapp.railway.app` |
| `CLOUDFLARE_R2_BUCKET` | Your R2 bucket name |
| `AWS_S3_ENDPOINT_URL` | `https://<account>.r2.cloudflarestorage.com` |
| `AWS_ACCESS_KEY_ID` | R2 API token |
| `AWS_SECRET_ACCESS_KEY` | R2 API secret |

### Custom Domain
1. Railway: Settings → Domains → Add Custom Domain
2. Cloudflare: add CNAME pointing to Railway hostname
3. Enable Cloudflare proxy (orange cloud) — free CDN + SSL

---

## 9. Build Sequence (Session-by-Session Plan)

### Session 1 — Scaffold & Models
**Goal:** A running local project with all models migrated
- Create Django project with Wagtail, configure settings package (dev/prod)
- Set up `docker-compose.yml` — `docker compose up` gives a running site
- Write all `pigments/models.py`
- Run migrations, register models as Wagtail Snippets
- Verify Wagtail admin shows all models with correct inline panels

### Session 2 — Pigment Filtering (Core Feature)
**Goal:** Working HTMX-filtered pigment list page
- Write `pigments/filters.py` with `PigmentFilter`
- Write `pigments/views.py` with HTMX partial detection
- Create `list.html` + `_results.html` templates
- Wire up `urls.py`
- Add Tailwind via CDN, style the filter sidebar and results grid
- Add sample data via fixtures, test all filters

### Session 3 — Pigment Detail Page + CSV Import
**Goal:** Full pigment detail page; import real data
- Write `detail.html` — description, formula(s) with color swatches, manuscript list
- Create CSV import management command
- Fill CSV template with real pigment data
- Run import, upload reference images
- Polish detail page with real data

### Session 4 — Blog / Editorial Content
**Goal:** Tutorials and research articles live in Wagtail
- Create `blog/` Wagtail page types (`BlogIndexPage`, `BlogPage`)
- Run Google Takeout migration script
- Review and clean up converted markdown files
- Import articles via management command
- Add category filtering (Craft / Research)

### Session 5 — Polish, Deploy, Domain
**Goal:** Live on your domain
- Write `production.py` settings (media on R2, static on whitenoise)
- Finalize Dockerfile, test cold build
- Deploy to Railway, run migrations
- Point Cloudflare DNS to Railway
- Smoke test: filters, images, admin, content creation

---

## 10. Requirements Files

### `requirements/base.txt`

```
Django==5.1
wagtail==6.3
psycopg2-binary==2.9.9
django-filter==24.3
django-htmx==1.21.0          # adds request.htmx detection
Pillow==10.4.0               # Wagtail image processing
whitenoise==6.7.0            # serve static files without nginx
gunicorn==23.0.0
boto3==1.35.0                # Cloudflare R2 / S3 media storage
django-storages==1.14.4      # S3-compatible media backend
python-decouple==3.8         # .env file management
```

### `requirements/dev.txt`

```
-r base.txt
django-debug-toolbar==4.4.6
ipython==8.28.0
```

---

## 11. Action Items Before Session 1

- [ ] **Project slug:** Decide on the Python package name (e.g. `esperanza`) — used in `config/`, import paths everywhere
- [ ] **GitHub repo:** Create one, or we create it together in Session 1
- [ ] **Google Takeout:** Export your Google Sites content now so it's ready for Session 4
- [ ] **Pigment spreadsheet:** Start even a rough spreadsheet with 5–10 pigment rows (name, color family, pigment family, description) to test the CSV import in Session 3
- [ ] **Accounts:** Sign up for Railway (railway.app) and Cloudflare (cloudflare.com) if not already done
