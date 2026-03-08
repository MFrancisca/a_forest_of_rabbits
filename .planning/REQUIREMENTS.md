# Requirements: Una Nueva Esperanza

**Defined:** 2026-03-06
**Core Value:** Visitors can easily explore and access historical pigment knowledge and craft tutorials; the owner can add new content in minutes without friction.

## v1 Requirements

### Pigment Database

- [ ] **PIGM-01**: User can browse pigments in a filterable list, sliceable by color family, pigment family, manuscript, country, and time period
- [ ] **PIGM-02**: User can view a pigment detail page with description, reference images, and manuscript provenance links
- [ ] **PIGM-03**: User can see brand-specific modern paint formulas with color swatches and part proportions for each pigment
- [ ] **PIGM-04**: Owner can manage all pigment data (taxonomy entries, formulas, images, manuscript links) through Wagtail admin without touching code

### Editorial

- [ ] **EDIT-01**: User can browse and read craft tutorials and art research articles
- [ ] **EDIT-02**: User can read an About page describing the site and its author

### Infrastructure

- [x] **INFRA-01**: Site runs locally via Docker Compose for development (Docker up = working site with database)
- [ ] **INFRA-02**: All uploaded images are stored on Cloudflare R2 and persist across Railway deployments
- [ ] **INFRA-03**: Existing Google Sites articles are migrated into Wagtail and accessible on the new site
- [ ] **INFRA-04**: Site is deployed and live at www.unanuovasperanza.art on Railway with Cloudflare DNS and SSL

### Testing

- [x] **TEST-01**: All models, views, filters, and URL routing have backend tests written using pytest + pytest-django
- [x] **TEST-02**: All test data is created via factory_boy factories — no Django fixtures anywhere in the test suite
- [ ] **TEST-03**: Tests cover edge cases for the pigment filter (empty results, M2M joins, combined filters)
- [ ] **TEST-04**: Tests cover the HTMX partial/full-page response logic in the pigment list view

## v2 Requirements

### Pigment Database

- **PIGM-v2-01**: Full-text search across pigment names and descriptions (add when database exceeds ~200 entries)
- **PIGM-v2-02**: CSV bulk import management command for loading large batches of pigment data

### Editorial

- **EDIT-v2-01**: Art research articles as a distinct content category with separate filtering
- **EDIT-v2-02**: Tag-based related articles (meaningful once more content exists)
- **EDIT-v2-03**: RSS feed

### Infrastructure

- **INFRA-v2-01**: StreamField step-by-step blocks for tutorial articles (richer than RichTextField)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / login | Read-only public site; no user-generated content planned |
| Comments or community features | Adds auth surface and GDPR complexity; not core to site goals |
| Dark / light mode toggle | Color research site needs consistent display conditions for accurate pigment representation |
| Social sharing buttons | Bookmarkable filter URLs are sufficient |
| E-commerce | Use external platform if ever needed |
| Mobile app | Web-first |
| OAuth / social login | No user accounts in v1 |
| Pagination on pigment list | Unnecessary below ~500 pigments given filtered list UX |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIGM-01 | Phase 2 | Pending |
| PIGM-02 | Phase 3 | Pending |
| PIGM-03 | Phase 3 | Pending |
| PIGM-04 | Phase 1 | Pending |
| EDIT-01 | Phase 4 | Pending |
| EDIT-02 | Phase 4 | Pending |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 6 | Pending |
| INFRA-03 | Phase 5 | Pending |
| INFRA-04 | Phase 6 | Pending |
| TEST-01 | Phase 1–4 | Complete |
| TEST-02 | Phase 1–4 | Complete |
| TEST-03 | Phase 2 | Pending |
| TEST-04 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-06*
*Last updated: 2026-03-06 after roadmap creation*
