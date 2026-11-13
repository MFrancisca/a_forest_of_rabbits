# Blog ("journal" app) — design

Date: 2026-11-12
Status: draft, awaiting review

## Purpose

A blog for work-in-progress updates and interesting finds that aren't project
documentation. Posts can point at the projects they're about, and posts tagged
"Pigments" surface beside the pigment database, so visitors browsing it can see
the research is ongoing.

Success looks like: writing a post in the Wagtail admin feels like writing a
project; a post linked to a project shows up on that project's page; a post
tagged Pigments shows up in the pigment pages' sidebar; nothing about the
existing project or pigment pages changes for visitors when there are no posts.

### Decisions made

| Question | Decision |
|---|---|
| App | New Django app `journal`. The existing `blog` app (projects) is not renamed. |
| Public URL / menu | `/blog/`, nav item "Blog". |
| Relation to projects | A post can link to any number of project pages (optional). |
| Tags | A curated list edited in the admin (Snippets → Tags), picked as checkboxes on a post. Not free-typed tags. Seeded with "Pigments". |
| Pigment database | "Latest pigment notes" sidebar on the pigment list and detail pages. |
| Phones / narrow screens | Sidebar content moves to the bottom of the page. |
| Hiding | Detail pages only: a Hide button collapses the sidebar; the choice is remembered per browser. |
| RSS | Not now. |

## Data model (`journal/models.py`)

### `Tag` (snippet)
- `name` — CharField(100), unique. Ordered by name.
- `slug` — SlugField, unique, filled from the name on save if blank. Used in the
  filter URL (`/blog/?tag=pigments`).
- Registered with `@register_snippet`, menu label "Tags".
- A data migration creates `Pigments` (slug `pigments`).
- `PIGMENTS_TAG_SLUG = 'pigments'` is the constant the sidebar looks up. Renaming
  the tag in the admin keeps its slug, so the sidebar keeps working; deleting it
  turns the sidebar off (it simply doesn't render).

### `BlogIndexPage` (Page)
- `intro` — RichTextField, blank.
- `parent_page_types = ['blog.HomePage']`, `subpage_types = ['journal.BlogPostPage']`,
  `max_count = 1`.
- `blog.HomePage.subpage_types` gains `'journal.BlogIndexPage'`.

### `BlogPostPage` (Page)
- `date` — DateField, default today. Orders posts (newest first, then by `-first_published_at`).
- `summary` — TextField(max 300), optional.
- `display_summary` (property) — what the list, sidebar and "Updates on this
  project" show: `summary` if set, otherwise the beginning of the body's first
  rich-text block that has text, with HTML stripped and truncated at a word
  boundary to about 300 characters, ending in "…". If the body has no text
  either, it's empty and listings show just the title and date. Computed from
  the page being rendered, nothing stored.
- `cover_image` — FK `wagtailimages.Image`, SET_NULL, optional.
- `tags` — `ParentalManyToManyField('journal.Tag', blank=True)`, checkbox widget.
- `related_projects` — `ParentalManyToManyField('blog.ProjectPage', blank=True,
  related_name='journal_posts')`, edited with a page chooser / multi-select.
- `body` — StreamField with `rich_text`, `image`, `carousel`, using
  `RichTextWithTitleBlock`, `ImageWithCaptionBlock`, `CarouselBlock` imported
  from `blog.models` (not copied).
- `parent_page_types = ['journal.BlogIndexPage']`, `subpage_types = []`.
- Parental M2Ms (not plain M2Ms) so tag/project edits are stored in revisions,
  same reason as `ProjectPage.categories`.

## Pages and templates

### Blog index (`/blog/`)
- Intro, then tag filter links ("All", then each tag that has at least one live
  post), the current one marked with `aria-current`.
- Live posts under the index, newest first, 10 per page (Django `Paginator`),
  `?tag=<slug>&page=<n>`. Unknown tag slug → empty list with "No posts tagged …",
  not a 404. Out-of-range page → last page.
- Each item: date, title (link), summary, tags, cover thumbnail if set.

### Post page
- Title, date, tags (linking to the filtered index), "Related project(s):" links
  (live projects only), cover image, body rendered with the existing block
  templates. Missing image files are skipped via `lightbox_renditions`, as on
  project pages.

### Project page addition
- "Updates on this project": live posts whose `related_projects` include the
  page, newest first, date + title + summary. Section omitted when there are none.

### Pigment sidebar
- Inclusion tag `{% pigment_notes_sidebar collapsible=False %}` in `journal`,
  rendering `journal/includes/pigment_notes_sidebar.html`. It queries the 3
  newest live posts tagged `PIGMENTS_TAG_SLUG` and renders nothing if there are
  none (or the tag doesn't exist).
- Content: heading "Latest pigment notes", each post's title (link), date and
  summary (truncated), then "See all →" to `/blog/?tag=pigments`.
- Layout: the pigment list and detail templates gain a two-column wrapper at
  `lg` and wider. The main content keeps its current max width (5xl list, 4xl
  detail) and the page container widens by the sidebar's ~16rem. Below `lg` the
  sidebar renders after the main content, full width.
- Detail page only (`collapsible=True`): a "Hide" button in the sidebar header
  collapses it to a slim vertical "Notes" tab; the tab restores it. State is
  stored in `localStorage` (key `pigmentNotesHidden`), read and written inside
  try/catch; if storage is unavailable the sidebar shows. Button uses
  `aria-expanded` / `aria-controls`. Uses the Alpine already loaded on the
  pigment pages. When hidden, the main content may use the freed width.
- The HTMX list partial is not affected: the sidebar sits outside the swapped region.

### Navigation
- `core/navigation.py` `NAV_LINKS` gains `('/blog/', 'Blog')`, and
  `SECTION_ITEMS` gains `'/blog/': 'post'` (for the 404 "Go to Blog" link).

## Image collections

All post images go into one top-level "Blog" collection (no per-post
collections, so the Images collection filter stays short).

- `BLOG_COLLECTION_NAME = 'Blog'`, created on demand with `core.collections.top_level_collection`.
- On save, images used on the post that are still in the root collection
  (unfiled) move into "Blog". Images already in another collection, such as a
  project's, stay where they are. Images later removed from a post stay in
  "Blog". Images are only ever moved, never deleted. This is the same rule as
  manuscript illuminations.
- Which images a post uses: `blog.image_collections.project_image_ids` is
  generalised to `page_image_ids(page)` (cover, image blocks, carousel slides,
  rich-text embeds; `technical_info` only when the page has it), and both apps
  call it.
- Triggered by a `post_save` signal on `BlogPostPage`, with the same
  `latest_revision` guard as `blog/signals.py`.
- No link model and no backfill command are needed: there are no existing posts.

## Operations

- `create_site_skeleton` creates the Blog index under Home (slug `blog`) if
  missing, idempotent, so staging and production get it on deploy.
- `sync_staging_to_production`:
  - add `journal.tag`, `journal.blogindexpage`, `journal.blogpostpage` and the
    M2M through tables to the copied model list, after the `blog` models they
    reference;
  - "Blog" joins Projects and Manuscripts in `_derived_collection_names()`, so it
    is recreated rather than required to exist.
  - Update `docs/promote-staging-to-production.md` and `docs/sync-local-to-staging.md`.
- Migrations: `journal/0001_initial` plus the Pigments seed (one or two files),
  and a `blog` migration for the `HomePage.subpage_types` change if Django
  generates one. Check consolidation afterwards per CLAUDE.md.
- `core/static/css/output.css` rebuilt for new Tailwind classes.

## Testing

- Models: `display_summary` uses the summary when set, else the start of the
  first rich-text block with text (HTML stripped, truncated at a word, "…" only
  when cut), else empty; tag slug auto-fill and uniqueness; tags and related projects survive
  publishing a revision; `Pigments` seeded by the migration.
- Blog index: newest-first order, tag filter, unknown tag, pagination,
  drafts excluded, filter links only for tags in use.
- Post page: renders body, tags, related projects (live only); missing image file skipped.
- Project page: "Updates on this project" lists live linked posts only; absent with none.
- Sidebar: on list and detail pages; only Pigments posts, max 3, newest first;
  absent with no posts or no tag; Hide control only on detail; present on full
  page but not in the HTMX partial response.
- Collections: a post's unfiled images move into "Blog"; images in another
  collection stay; removed images stay in "Blog"; nothing deleted;
  `page_image_ids` still passes the existing project tests.
- Sync command: new models copied; "Blog" collection recreated.
- Skeleton: creates `/blog/` once, idempotent.
- a11y (axe): blog index, post page, pigment detail with sidebar shown and hidden.
- Manual: Playwright screenshots at 1280px and 390px.

## Out of scope

RSS feed; free-typed tags; linking posts to individual pigments or manuscripts;
comments; search.

## Decided after first review

- Single "Blog" collection for all post images, not one collection per post.
