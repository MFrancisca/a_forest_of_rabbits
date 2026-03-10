# Content Migration Guide

Use this guide when performing the manual content migration from Google Sites into Wagtail.
Read it end-to-end once before starting. Each step is in order — do not skip ahead.

Track your progress in `docs/migration-checklist.md` as you go.

---

## Prerequisites (check before starting)

- [ ] Dev server is running: `docker compose up`
- [ ] Projects index page exists:
  ```
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/projects/
  ```
  Must return `200`. If it returns `404`, run:
  ```
  docker compose exec web python manage.py create_site_skeleton
  ```
- [ ] Live Google Sites open in a browser tab alongside the Wagtail admin at http://localhost:8000/cms/

---

## Step 1: Create the three Category snippets FIRST

**Do this before touching any articles.** You cannot assign a category to an article that does not exist yet.

1. Navigate to: **/cms/ > Snippets > Categories > "+ Add Category"**
2. Create the following three categories in this order:
   - **Calligraphy & Illumination**
   - **Clothing**
   - **Armor**
3. Confirm all three appear in the Categories snippet list before continuing.

---

## Step 2: For each article, repeat these sub-steps

Work through one article at a time, completing all sub-steps (2a–2f) before moving to the next.

---

### Step 2a — Download images from Google Sites

- For each image in the article: **right-click > Save image as** — save to a local folder (e.g. `~/Desktop/migration-images/`)
- Do this for **ALL images** in the article before starting the Wagtail entry
- Name files meaningfully (e.g. `oak-gall-ink-step1.jpg`) — the filename becomes searchable in Wagtail

> **Pitfall to avoid:** Do not try to upload images mid-entry. Download all images first, then do the Wagtail work.

---

### Step 2b — Upload images to Wagtail image library

- Navigate to: **/cms/ > Images > "Add an image"**
- Upload each saved image file
- Give each image a meaningful title (Wagtail uses this for search)
- You can upload all images for an article in one batch before creating the page

---

### Step 2c — Create the ProjectPage

- Navigate to: **/cms/ > Pages (sidebar) > Root > Projects > "+ Add child page" > "Project page"**
- Fill in these fields:
  - **Title** — copy exactly from the Google Sites article heading
  - **Date** — use the original publish date if visible; otherwise use today's date
  - **Category** — select from the dropdown (must exist from Step 1)
  - **Excerpt** — a short description: the first sentence or two from the article

> **Pitfall to avoid:** Leave the **Cover Image** field BLANK. All images go inline in the body (Step 2e). Using cover_image will result in a different page layout that does not match the migration plan.

---

### Step 2d — Add body text

- In the Body editor: paste the article text from Google Sites
- Apply headings (H2, H3), bold, italic, and lists using the toolbar as needed
- Minor formatting differences from Google Sites are acceptable — the goal is content fidelity, not pixel-perfect reproduction

> **Pitfall to avoid:** Do not publish before inserting images (Step 2e). Body text without images is an incomplete article.

---

### Step 2e — Insert images inline in the body (MOST IMPORTANT STEP)

Images must be inserted using Wagtail's image chooser — not pasted or dragged in. Pasted images will not persist or serve correctly.

For each image in the article:

1. **Position your cursor** in the body text where the image should appear
2. **Click the image toolbar button** (picture icon in the Body editor toolbar)
3. In the chooser modal: **search for the image** you uploaded in Step 2b by filename
4. **Select it** and choose "Full width" or the desired format
5. Click **Insert** — the image appears in the body at the cursor position
6. Repeat for each image

> **Pitfall to avoid:** Do not skip this step or paste image URLs directly. Images not inserted via the chooser will appear as broken links once the site is deployed and the Google Sites image URLs are no longer valid.

---

### Step 2f — Publish

- Click **"Publish"** — not "Save draft"
- **Draft articles do NOT appear on /projects/**
- Verify: visit **http://localhost:8000/projects/** and confirm the new article appears in the list
- Click through to the article; confirm:
  - All images display (not broken)
  - Body text reads correctly
  - Category chip appears

> **Pitfall to avoid:** If you only click "Save draft", the article will not be visible. Always click "Publish".

---

## Step 3: Update the checklist

After each article is published and verified:

1. Open `docs/migration-checklist.md`
2. Fill in the row for this article:
   - Tick the Done checkbox: `[x]`
   - Add the Article Title
   - Add the Category
   - Add the Wagtail URL (e.g. `/projects/making-oak-gall-ink/`)
3. Save the file

Keep the checklist up to date as you go — do not wait until all articles are done.

---

## Step 4: After ALL articles are complete

Once every article row in the checklist is ticked:

1. Open `docs/migration-checklist.md` and tick the three sign-off checkboxes at the bottom
2. Do a final side-by-side browser comparison: Google Sites vs. the local Wagtail site
3. Run the test suite to confirm nothing was broken:
   ```
   docker compose exec web pytest -q
   ```
4. Commit the completed checklist:
   ```
   git add docs/migration-checklist.md && git commit -m "docs(05): complete content migration checklist"
   ```

**The checklist must be 100% ticked before Phase 6 DNS cutover begins.**

---

## Known Pitfall Summary

| # | Pitfall | Prevention |
|---|---------|------------|
| 1 | Wrong category order | Create all three categories in Step 1 before any articles |
| 2 | Missing site skeleton | Run `create_site_skeleton` if /projects/ returns 404 |
| 3 | Two-step image process | Download first (Step 2a), then upload (Step 2b), then insert (Step 2e) |
| 4 | Draft vs. publish | Always click "Publish", not "Save draft" |
| 5 | Cover image confusion | Leave cover_image BLANK — all images go inline in the body |
| 6 | Uncommitted checklist | Commit checklist after migration is complete (Step 4) |
