# Content Migration Checklist

**This checklist must be 100% complete before Phase 6 DNS cutover begins.**

Follow `docs/migration-guide.md` for step-by-step instructions on how to migrate each article.

Fill in all columns as you complete each article. Article titles are not pre-populated — you will discover the exact article list when sitting down with the live Google Sites. Add more rows if needed.

---

## Articles

| Done | Article Title                           | Category                   | Wagtail URL                                       |
|------|-----------------------------------------|----------------------------|---------------------------------------------------|
| [x]  | About                                   | About                      | /about                                            |
| [x]  | Weaving Archive                         | Archive                    | /projects/weaving/                                |
| [x]  | Scribal Archive                         | Archive                    | /projects/scribal/                                |
| [x]  | Classes                                 | Classes                    | /projects/classes/                                |
| [x]  | Rotella                                 | Armor                      | /projects/rotella                                 |
| [x]  | Leather Fencing Doublet                 | Armor                      | /projects/letather-fencing-doublet                |
| [x]  | Handsewn Italian Camicia                | Clothing                   | /projects/handsewn-camicia                        |
| [x]  | Bjornsborg Chapions - Spring 2025       | Calligraphy & Illumination | /projects/bjornsborg-champions-spring-2025        |
| [x]  | Queen's Champion for HRM Gilyan III     | Calligraphy & Illumination | /projects/queens-champion-for-hrm-gilyan-iii      |
| [x]  | Rainbow Triskele - Sable Swap 2024      | Calligraphy & Illumination | /projects/rainbow-triskele-sable-swap-2024        |
| [x]  | Court Baronies for Elfea's founding B&B | Calligraphy & Illumination | /projects/court-baronies-for-elfseas-founding-bb  |
| [x]  | Queen's CHampion for HRM Sonja III      | Calligraphy & Illumination | /projects/queens-champion-for-sonja-iii/          |
---

**Example of a completed row:**

| [x] | Making Oak Gall Ink | Calligraphy & Illumination | /projects/making-oak-gall-ink/ |

---

## Completed

- [x] All rows above are ticked
- [x] Side-by-side browser comparison with live Google Sites done — no missing content
- [x] Existing test suite green: `docker compose exec web pytest -q`

When all three boxes are ticked, Phase 6 DNS cutover is unblocked.
