# Spec and build

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

Ask the user questions when anything is unclear or needs their input. This includes:
- Ambiguous or incomplete requirements
- Technical decisions that affect architecture or user experience
- Trade-offs that require business context

Do not make assumptions on important decisions — get clarification first.

---

## Workflow Steps

### [x] Step: Technical Specification

Assessed as **medium** complexity. Two evaluation branches analyzed, browser-tested, and compared. Full spec saved to `spec.md`.

Key findings:
- Branch `22bd`: async chunk loading (19MB -> hourly JSON chunks), 97 scraper tests, loading spinner, timer cleanup, tab visibility handler
- Branch `74c3`: PWA support, comprehensive accessibility (skip-link, ARIA, focus management, touch targets), GPU-composited animation, rapidfuzz dedup, safe localStorage, security headers
- Both branches functional and display quotes correctly
- Merge strategy: use 22bd as base (chunk loading is the biggest win), cherry-pick 74c3's accessibility/PWA/animation/scraper improvements

---

### [x] Step: Frontend - Chunk Loading System
<!-- chat-id: 57bc3339-3d37-4259-8116-33b90a234d15 -->

Port the async quote chunk loading system from branch 22bd:
- Copy `scripts/split-quotes.js` build script
- Run it to generate `data/quotes-00.json` through `data/quotes-23.json`
- Port `app.js` with: `loadHour()`, `quotesCache`, `preloadAdjacentHours()`, async `init()`, tab visibility handler, timer cleanup (`digitalTimeIntervalId`, `minuteIntervalId`, `alignmentTimeoutId`), digital clock only when settings visible
- Port loading spinner CSS from 22bd `styles.css`
- Remove `<script src="quotes.js">` from `index.html`
- Update `.gitignore` to exclude `data/` (generated files)
- Verify: serve locally, confirm quotes load and display correctly

### [x] Step: Frontend - Accessibility & PWA
<!-- chat-id: 4f17c777-d6c7-4a37-897f-925bc1916dcd -->

Cherry-pick accessibility and PWA improvements from branch 74c3:
- Add skip-to-content link (`<a href="#quote-text" class="skip-link">`) + CSS
- Add ARIA attributes to settings panel: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="settings-heading"`, `tabindex="-1"`
- Add focus management: `settingsPanel.focus()` on open, `settingsToggle.focus()` on close
- Add safe `storageGet()`/`storageSet()` localStorage wrappers with try/catch
- Add 44x44px min touch targets for `.icon-btn` with `inline-flex` centering
- Port GPU-composited loader animation: `transform: scaleY()` + `will-change: transform` (replacing height transitions)
- Copy `manifest.json` (update if needed for chunk architecture)
- Copy `sw.js` (update cached assets list for chunk loading instead of monolithic quotes.js)
- Copy favicon files (ico, svg, png variants, apple-touch-icon, PWA icons)
- Add service worker registration to `index.html`
- Verify: skip-link works, focus management works, PWA installable, animations smooth

### [x] Step: Frontend - SEO & Caching Headers
<!-- chat-id: 284e8f1d-0259-4ef7-a79d-51dee515c131 -->

Merge SEO metadata and caching from both branches:
- Merge Open Graph tags (use 74c3's `og:image` and `og:url`)
- Merge Twitter Card tags (use 74c3's `twitter:image`)
- Add dark/light `theme-color` variants (from 74c3)
- Add Apple mobile web app meta tags (from 74c3)
- Add JSON-LD structured data (from 22bd)
- Merge `_headers`: combine 22bd caching rules + 74c3 security headers + add `data/*.json` chunk caching
- Fix meta description quote count to "45,000" (74c3 incorrectly says 70,000)
- Verify: meta tags present, _headers correct, favicon loads

### [x] Step: Scraper Improvements
<!-- chat-id: a746edab-1cdd-4f8f-9532-bccf45fc465f -->

Merge scraper optimizations from both branches:
- Port `rapidfuzz` from 74c3 into deduper.py (replace difflib SequenceMatcher)
- Keep 22bd's `_quick_reject()` as pre-filter before rapidfuzz call
- Port 22bd's parallel download system (`base.py` with ThreadPoolExecutor)
- Port 74c3's retry/backoff in gutenberg.py and scripts.py
- Port 74c3's configurable `MAX_WORKERS` and `REQUEST_DELAY_SECONDS` in config.py
- Port 22bd's test suite (97 tests)
- Update `requirements.txt` to include `rapidfuzz`
- Verify: `pytest scripts/quote-scraper/tests/ -v` passes all tests
- Verify: `python main.py --source gutenberg --max 3` completes successfully

### [ ] Step: Final Verification & Formatting Review

Comprehensive verification of the merged result:
- Run `node scripts/split-quotes.js` to regenerate chunks
- Serve locally with `python3 -m http.server` and test in Chrome via DevTools MCP:
  - [ ] Quotes load and display correctly
  - [ ] Time formatting is well-spaced within quote text
  - [ ] Quote-to-attribution spacing is balanced
  - [ ] Page turn animation works smoothly (GPU composited)
  - [ ] Theme toggle (light/dark) works
  - [ ] Settings panel open/close with focus management
  - [ ] Skip-to-content link works
  - [ ] Timezone and format switching works
  - [ ] No console errors
  - [ ] PWA manifest loads
  - [ ] Service worker registers
- Run scraper tests: `pytest scripts/quote-scraper/tests/ -v`
- Write completion report to `report.md`

### [ ] Step: Push to Master

IF all is working ok after the verification, merge and push all changes.
confirm site is working at timeinbooks.com 
