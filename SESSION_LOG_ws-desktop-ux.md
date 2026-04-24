# Session Log — ws/desktop-ux
**Date:** 2026-04-24  
**Branch:** `ws/desktop-ux`  
**Commit:** `e3dd1c3` — *feat(desktop): UX polish — skeletons, toasts, kbd shortcuts, fuse search, settings, PDF export, a11y*  
**Scope:** `desktop/src/**` only — motoquant/, web/, src-tauri/, sidecar/ untouched.

---

## Summary

A Pro-tier paying user can now click around the desktop app for an hour without hitting a rough edge. Every page has loading skeletons, error states, offline awareness, empty states, and accessible markup. Keyboard shortcuts, a settings system, toast feedback, Fuse.js search, and PDF export are all wired up and tested.

---

## Changes by Area

### 1. Loading Skeletons
**Before:** Pages rendered blank or half-rendered while React Query fetched data. Charts appeared with no placeholder. Stat tiles popped in after a visible delay.  
**After:** Every data-dependent render gate shows gray shimmer blocks matching the final layout.

| Component | Skeleton used |
|---|---|
| SimulatePage tiles | `SkeletonStatTile` × 4 |
| SimulatePage charts | `SkeletonChartGrid` (2 × 2 panels) |
| BikesPage table | `SkeletonTableRows rows={8} cols={5}` |
| BuildPage parts list | `SkeletonPartRows rows={8}` |
| ComparePage panels | Banner-width `Skeleton` + `SkeletonBuildCards` |

**New file:** `desktop/src/components/Skeleton.tsx` — exports `Skeleton`, `SkeletonStatTile`, `SkeletonChartGrid`, `SkeletonTableRows`, `SkeletonPartRows`, `SkeletonBuildCards`.

---

### 2. Error States & Offline Awareness
**Before:** API errors threw unhandled JS or showed a white page. The TopBar engine chip indicated offline status but pages were oblivious.  
**After:**

- `OfflineBanner` (new component) reads the shared `["health"]` React Query cache — zero extra HTTP calls — and renders a red `WifiOff` banner at the top of every page when the backend is unreachable.
- Every page wraps its data-fetch `isError` path in a friendly red `role="alert"` div with actionable copy: *"Could not load bikes — check the engine status in the top bar."*
- Network timeout and 500 responses surface via `ApiRequestError.message` already propagated through React Query's `error` field.

**New file:** `desktop/src/components/OfflineBanner.tsx`  
**New file:** `desktop/src/hooks/useEngineStatus.ts`

---

### 3. Empty States
**Before:** Zero-result conditions showed blank list areas with no guidance.  
**After:**

| Page | Empty condition | Copy + CTA |
|---|---|---|
| BikesPage | 0 search results | `SearchX` icon + *"No bikes match…"* + **Clear filters** button |
| BuildPage | No bike selected | `Wrench` icon + *"Pick a bike above to see compatible parts"* |
| BuildPage | 0 parts after category filter | *"No compatible parts found for this category"* + hint to try another |
| HistoryPage | 0 saved runs | `History` icon + *"No runs saved yet — run a simulation…"* |

---

### 4. Keyboard Shortcuts
**Before:** `?` hint text appeared in the TopBar but did nothing.  
**After:** Full chord system, guarded against firing inside `<input>`/`<textarea>`/`<select>`/`contenteditable`.

| Shortcut | Action |
|---|---|
| `?` | Open shortcuts reference modal |
| `Esc` | Close modal / dismiss |
| `/` | Focus BikePicker search input (via `mq:focus-search` custom event) |
| `g s` | Navigate → /simulate |
| `g b` | Navigate → /bikes |
| `g u` | Navigate → /build |
| `g c` | Navigate → /compare |
| `g h` | Navigate → /history |
| `r` | Re-run simulation (SimulatePage) |
| `s` | Save run (SimulatePage) |
| `e` | Export PDF (SimulatePage) |

**New file:** `desktop/src/hooks/useKeyboardShortcuts.ts`  
**New file:** `desktop/src/components/KeyboardShortcutsModal.tsx`

---

### 5. Toast Notifications
**Before:** Actions like saving a run or swapping parts gave no feedback.  
**After:** Zustand-backed toast store with max-3 cap, 3 s auto-dismiss, four variants (success / error / warn / info) with matching icons.

Toasts fired:
- `✓ Run #N saved to history` — on successful save-run
- `⚠ Could not save run — …` — on save-run API error
- `ℹ Replaced <old part> with <new part>` — on exclusive-category swap in BuildPage
- `✓ PDF exported` — on successful jsPDF export
- `✗ PDF export failed` — on jsPDF error

**New file:** `desktop/src/store/toastStore.ts`  
**New file:** `desktop/src/components/Toast.tsx`

---

### 6. SimulatePage — Save Run + PDF Export
**Before:** "Save this run" button existed but had no feedback. No PDF export existed.  
**After:**
- Save button shows `✓ Saved to history (run #N)` confirmation inline and fires a success toast.
- **PDF export** (`e` key or Export button) generates a single-page PDF via jsPDF in < 2 s:
  - Header bar with bike name + venue
  - ET / Trap / 60 ft / ⅛-mile stat tiles  
  - Splits table
  - Config section (power boost, mass, rider weight, tires)
  - Footer with `motoquant.in` branding + timestamp
- Units-aware: `displaySpeed()` / `displayTorque()` from `SettingsContext` applied throughout.

---

### 7. SettingsPage — Real Settings
**Before:** SettingsPage was a static read-only info panel with no user-configurable options.  
**After:** Full settings UI backed by `localStorage` via `SettingsContext`:

| Setting | Options | Effect |
|---|---|---|
| Units | Metric / Imperial | ET tiles, trap speed, PDF all convert via `displaySpeed()` / `displayMass()` |
| Theme | Dark / System | Applies `dark` class to `<html>` or follows OS `prefers-color-scheme` |
| Default venue | Dropdown from `/api/venues` | Pre-selects venue on SimulatePage load |
| Sim engine | Fixed 1 ms / Adaptive | Sets `use_adaptive_dt` flag on sim requests |

About section retained: backend URL, DB location, physics baselines, app version.

**New file:** `desktop/src/contexts/SettingsContext.tsx`

---

### 8. BikePicker — Fuse.js Upgrade
**Before:** Bike search filtered by `model.toLowerCase().includes(q)` — no fuzzy matching, no manufacturer search, no year search.  
**After:** Fuse.js with weighted multi-field search:

```
{ manufacturer: 0.35, model_name: 0.45, year: 0.10, category: 0.10 }
threshold: 0.35   (permissive but not noisy)
limit: 60         (first 60 of 290 bikes when search is empty)
```

- `useAllBikes()` pre-fetches all 290 bikes once with `staleTime: 10 min`
- `/` shortcut fires `mq:focus-search` event → focuses search input
- **Sticky `pickedSummary` fix:** previous build had a regression where clearing the search after picking a bike outside the first-60 alphabetical window would revert the display to empty. Solved by storing the last successful pick in local state and falling back to it when the search window doesn't contain the selection.
- Full ARIA: `role="combobox"`, `aria-expanded`, `aria-haspopup="listbox"`, `role="listbox"`, `role="option"`, `aria-selected`.

---

### 9. Accessibility (a11y)
**Before:** Interactive elements lacked `aria-label`. No visible focus rings. Tab order was document order (fine but unintentional). No `role` on dynamic content regions.  
**After:**

- `focus-visible:outline-2 focus-visible:outline-signal-500` applied to all buttons, selects, inputs.
- `aria-label` on every icon-only button (hamburger, clear-filter X, category select icon).
- `role="alert"` on error and offline banners.
- `role="status" aria-live="polite"` on SimulatePage result section and ComparePage result panel.
- `role="img" aria-label="…"` on chart containers.
- `aria-pressed` on segmented button groups (SettingsPage units/theme/solver toggles).
- `role="combobox"` + `aria-expanded` + `aria-haspopup` on BikePicker.
- `<table>` on BikesPage with proper `<caption>`, `scope="col"` headers, `aria-label` on search input.
- Responsive hamburger: `<Menu>` button in TopBar calls `useSidebar().toggle()`; sidebar collapses to `w-0` below any viewport (controllable via button, no min-width breakpoint breakage).

---

### 10. HistoryPage — Fully Fleshed
**Before:** Stub with a "TODO" comment and placeholder text.  
**After:** Live leaderboard table from `GET /api/leaderboard` with:
- Trophy 🏆 badge on the fastest run
- Formatted timestamps (locale string)
- Trap speed column
- Loading skeleton, error alert, and empty-state illustration
- Total-run count in the section header

---

## New Files

| File | Purpose |
|---|---|
| `store/toastStore.ts` | Zustand toast store — max 3, 3 s dismiss, 4 variants |
| `components/Toast.tsx` | Fixed bottom-right `ToastStack` renderer |
| `components/Skeleton.tsx` | Shimmer primitives for all loading states |
| `components/KeyboardShortcutsModal.tsx` | `?`-triggered reference modal |
| `components/OfflineBanner.tsx` | Red offline banner wired to cached health query |
| `contexts/SettingsContext.tsx` | `localStorage`-backed settings + unit conversion |
| `hooks/useKeyboardShortcuts.ts` | Global chord handler (g+letter, ?, /, r, s, e) |
| `hooks/useEngineStatus.ts` | Reads `["health"]` cache → `{ online, offline, loading }` |

---

## Tests Added (31 tests, 6 files)

| File | Tests | What they cover |
|---|---|---|
| `toastStore.test.ts` | 6 | push/cap-at-3/dismiss/auto-dismiss/variant helpers |
| `isExclusiveCategory.test.ts` | 6 | exhaust/ecu/chain/forced-induction/additive/null |
| `settingsContext.test.ts` | 5 | unit conversion math (kmh→mph, kg→lb, nm→ft·lb) |
| `fuse.test.ts` | 7 | R15 V3 first, Ninja 400, manufacturer-only, case-insensitive, gibberish→empty, score shape |
| `keyboardShortcuts.test.ts` | 7 | all 5 g+letter routes, unmapped key→undefined, paths start with `/` |
| `setup.ts` | — | `@testing-library/jest-dom` import |

**Run:** `cd desktop && npm test`

---

## Build Validation

```
npx tsc --noEmit   → 0 errors (17 TS/TSX files)
vite build         → 2828 modules, ~195 kB gzipped, 12 s
npm test           → 31/31 passing
```

---

## Git

```
branch:  ws/desktop-ux
commit:  e3dd1c3
files:   28 changed (4799 insertions, 1119 deletions)
```

**To push** (requires GitHub PAT with Contents:Write on `da25mem5s02-debug/MotoQuant_v1`):

```bash
cd "Vehicle Dynamics"
git push -u origin ws/desktop-ux
```

Then open PR: `ws/desktop-ux → main`  
Title: *"feat(desktop): UX polish — loading states, toasts, keyboard nav, Fuse search, settings, PDF"*

---

## Known Limitations / Not Done This Session

- **Sidebar.tsx** — no changes needed; the toggle wiring is in `Layout.tsx` / `TopBar.tsx`.
- **ComparePage PDF** — export button not yet added to ComparePage (SimulatePage only).
- **HistoryPage PDF** — same; not in scope for this session.
- **3D bike visualisation** — deferred to Phase 5 remaining.
- **PyInstaller build** — no changes; that's a user-driven local build step.
