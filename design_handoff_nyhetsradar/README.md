# Handoff: Nyhetsradar (Selvaag Eiendom news monitor)

## Overview

Nyhetsradar is an internal news-monitoring frontend for Selvaag Eiendom. A nightly pipeline collects property-sector news from ~34 Norwegian sources, deduplicates near-identical coverage into single stories, scores each story against per-role and per-person "watchlists" built from flagged examples, and publishes a weekly brief. An LLM is used only for two things: a summary and a "why this matters to us" paragraph, generated for stories above the relevance threshold.

The frontend covers four views: the weekly brief (the product's centre of gravity), an article detail page that explains *why* a story scored the way it did, an admin view for source and pipeline health, and mobile layouts of the first two.

Interface language is **Norwegian**. All copy in the design is final Norwegian copy — do not translate or rewrite it.

## About the Design Files

The files in this bundle are **design references created in HTML** — prototypes showing intended look and behaviour, not production code to copy directly.

The task is to **recreate these designs in the target codebase's existing environment** (React, Vue, .NET/Razor, SwiftUI, whatever Selvaag's stack is) using its established patterns, component library, and data layer. If no frontend environment exists yet, choose the most appropriate framework for the project and implement the designs there.

`Nyhetsradar.dc.html` is a single-file prototype: all four screens live in one component with a `screen` state variable and a left-hand nav that switches between them. In production these are almost certainly **four routes**, not one component — the single-file structure is a prototyping convenience, not an architectural recommendation.

All content in the prototype is **hard-coded sample data** (see `Nyhetsradar.dc.html`, constants `LISTS`, `ITEMS`, `HEALTH`, `SOURCES`, `MODELS`, `LOG`). It is realistic but invented: story titles, figures, source counts and log lines are all placeholder. Replace with real API data.

## Fidelity

**High-fidelity.** Colours, typography, spacing, borders and interaction states are final and specified exactly below. Recreate pixel-faithfully using the codebase's existing primitives where they exist.

One substitution to be aware of: the design system fonts (**Selvaag Sans** for display/UI, **Tiempos** for body) are not web-licensable in the prototype environment. The prototype uses **Archivo** as the Selvaag Sans stand-in and **Source Serif 4** as the Tiempos stand-in. In a real Selvaag deployment, swap both back to the licensed brand fonts — the sizes, weights, letter-spacing and uppercase treatment specified below are authored for the brand fonts and should carry over unchanged.

Visual language: flat, architectural, zero border-radius everywhere, 2px rules for structural divisions and 1px rules for list separators, flush-left alignment, generous whitespace. No shadows, no gradients, no rounded cards. This is deliberate — it comes from the Selvaag profile manual and the attached Modernist design system.

---

## Design Tokens

### Colours

| Token | Hex | Use |
|---|---|---|
| Petroleum (primary) | `#00313B` | All body text, sidebar background, 2px structural rules, primary buttons |
| Rust (accent) | `#B7592E` | Eyebrow labels, relevance scores ≥85, "why this matters" left border, primary CTA, active-state dots, links |
| Fromage (highlight) | `#FAF2CF` | "Why this matters" callout background, row hover tint (at 40% alpha), secondary button hover |
| Paper (canvas) | `#FFFEF9` | Page background, text on dark |
| Stone | `#F4F4F2` | Sidebar-panel background (article detail right rail) |
| Sand | `#E3DBCC` | 1px separators inside panels, progress-bar track, button hover fill |
| Sand light | `#EFEAE0` | Reserved — lighter separator variant |
| Mint | `#85B590` | Sidebar sub-label, "Nyhetsradar" wordmark, cluster-count chip border, training-basis panel border |
| Mint tint | `#F2FCFA` | Cluster-count chip background, training-basis panel background |

Text alpha ladder on petroleum: `1.0` headings and primary text · `0.85` article body · `0.78` summaries · `0.75` intro paragraphs · `0.7` / `0.68` "why this matters" italic · `0.65` / `0.62` panel notes · `0.55` / `0.5` uppercase meta labels · `0.45` de-emphasised numerals · `0.38` input placeholder.

Text alpha ladder on petroleum background (sidebar): `#FFFEF9` at `1.0` nav and active list · `0.62` stats · `0.6` inactive lists · `0.5` counts · `0.45` section labels · `0.22` / `0.16` rules.

### Typography

Two families. Display/UI is uppercase-heavy with wide tracking; body is a serif at comfortable measure.

**Display / UI — Archivo (→ Selvaag Sans)**

| Role | Size | Weight | Tracking | Case |
|---|---|---|---|---|
| Wordmark | 15px | 600 | 0.17em | upper |
| Page title (h1) | 40px | 500 | 0.015em | upper, line-height 1.05 |
| Mobile page title | 26px | 500 | 0.015em | upper, line-height 1.1 |
| Eyebrow (above h1) | 11px | 400 | 0.17em | upper |
| Section heading (h2) | 15px | 500 | 0.13em | upper |
| Nav item | 12px | 400 | 0.1em | upper |
| Button label | 11px | 400 | 0.1em | upper |
| Meta label / column header | 10px | 400 | 0.13–0.15em | upper |
| Micro label ("Relevans") | 9px | 400 | 0.13em | upper |
| Stat numeral (KPI strip) | 28px | 500 | — | — |
| Score numeral (feed row) | 22px | 500 | — | line-height 1 |
| Score numeral (detail rail) | 46px | 500 | — | line-height 1 |
| Numeric cell (tables, similarity) | 12–14px | 400 | — | — |

**Body — Source Serif 4 (→ Tiempos)**

| Role | Size | Weight | Line-height | Notes |
|---|---|---|---|---|
| Article detail h1 | 40px | 600 | 1.16, tracking −0.01em | max 30ch |
| Feed row title | 25px | 600 | 1.25 | max 46ch |
| Mobile article title | 26px | 600 | 1.22 | |
| Mobile feed title | 20px | 600 | 1.28 | |
| Detail summary | 20px | 400 | 1.6 | |
| "Why this matters" (detail) | 19px | 400 | 1.6 | |
| Intro paragraph | 18px | 400 | 1.6 | max 54–56ch |
| Feed summary | 17px | 400 | 1.62 | max 62ch |
| Article body | 17px | 400 | 1.7 | max 66ch |
| "Why this matters" (feed) | 16px | 400 italic | 1.55 | max 58ch |
| Panel body / list item | 14–15px | 400 | 1.45–1.55 | |
| Caveat / footnote | 13–14px | 400 italic | 1.5 | |

`text-wrap: pretty` on every multi-line prose block. Max-width via `ch` units, not px — measure is what matters.

### Spacing

Page padding `46px 52px 72px`. Sidebar padding `34px 24px 24px`. Right rail padding `46px 34px 72px`. Mobile frame inner padding `20–22px`.

Vertical rhythm inside content: section gap `34–38px`, block gap `26–30px`, element gap `10–18px`, tight gap `3–9px`. Feed row vertical padding `30px 0 32px`. KPI cell padding `22px`. Table row bottom padding `13px`.

### Borders & radius

**Border radius is `0` everywhere.** No exceptions.

- `2px solid #00313B` — structural: under page header, under KPI strip, above the feed footer, right-rail left edge, mobile frame outline, table header underline.
- `2px solid #B7592E` — the "why this matters" left border (feed rows and mobile), and primary-button border.
- `2px solid #85B590` — training-basis panel.
- `1px solid #E3DBCC` — separators between list items, KPI cell dividers, table row rules.
- `1px solid rgba(255,254,249,0.16)` — sidebar nav item dividers.

No `box-shadow` anywhere.

### Other

Progress bars: 4px tall in feed rows, 6px in the detail rail. Track `#E3DBCC`, fill accent, width = `score%`. Active-nav dot and status dot: 6×6px square (not a circle), accent-coloured, toggled via `opacity: 0 | 1`.

Focus ring: `2px solid #B7592E`, `outline-offset: 2px`, on `:focus-visible` for buttons and inputs.

Selection: `::selection { background: #FAF2CF }`.

---

## Screens / Views

### Persistent: left sidebar (264px, all desktop screens)

**Purpose** — identity, screen switching, watchlist selection, pipeline reassurance.

**Layout** — fixed `264px` (`flex: 0 0 264px`), full height, background `#00313B`, text `#FFFEF9`, padding `34px 24px 24px`, `flex-direction: column`, `gap: 36px`. Last block uses `margin-top: auto` to pin to the bottom.

**Components, top to bottom**

1. **Wordmark block** — "SELVAAG / EIENDOM" on two lines (15px/600/0.17em upper, line-height 1.35), then a `2px` rust rule (`margin: 14px 0 12px`), then "NYHETSRADAR" in mint `#85B590` (11px/0.15em upper).
2. **Nav** — four items, each a full-width button, `padding: 12px 0`, `border-bottom: 1px solid rgba(255,254,249,0.16)`, `display: flex; gap: 10px; align-items: center`. Each begins with a 6×6px rust square whose `opacity` is `1` when that screen is active, `0` otherwise (the square always occupies space, so labels never shift). Labels: **Ukens brief**, **Sak**, **Kilder og drift**, **Mobil**. Hover: label colour → `#85B590`.
3. **Watchlist block** — label "WATCHLISTER" (10px/0.15em upper, `rgba(255,254,249,0.45)`), then a `gap: 10px` column of buttons. Each row: name (15px serif, `flex: 1`) + count (11px Archivo, `rgba(255,254,249,0.5)`), baseline-aligned. Active list is `#FFFEF9`, others `rgba(255,254,249,0.6)`; hover `#FAF2CF`. Below, an italic 13px note at `0.5` alpha stating the current scope.
   Lists in the sample data: `Forretningsutvikling` (6, role), `Kommunikasjon` (4, role), `Ledelse` (3, role), `Min liste · Anne` (5, personal). Note text: "Rollelister og personlige lister."
4. **Footer block** — `2px` rule at `rgba(255,254,249,0.22)`, then two 13px lines at `0.62` alpha ("412 artikler siste 7 døgn", "34 kilder · sist kjørt 06:12"), then the brand line "KUNSTEN Å UTVIKLE EIENDOM" (10px/0.13em upper, mint at `0.8`).

Clicking a watchlist sets the active list **and** navigates to the brief.

---

### 1. Ukens brief

**Purpose** — the Monday read. A stakeholder opens this, scans 5 stories, and knows what happened in the market that affects Selvaag.

**Layout** — single column, `max-width: 1080px`, page padding `46px 52px 72px`.

**Components**

1. **Header** — `display: flex`, `align-items: flex-end`, `justify-content: space-between`, `gap: 32px`, `padding-bottom: 24px`, `border-bottom: 2px solid #00313B`.
   - Left: eyebrow "UKE 36 · 31. AUGUST – 6. SEPTEMBER 2026" (rust), h1 "UKENS BRIEF" (40px/500 upper).
   - Right: two buttons, `gap: 10px`. Secondary "DEL I TEAMS" — `2px solid #00313B`, transparent, `padding: 11px 16px`; hover fill `#FAF2CF`. Primary "SEND DIGEST" — rust fill and border, paper text; hover both go petroleum.
2. **KPI strip** — 4-column grid, `border-bottom: 2px solid #00313B`, cells divided by `1px solid #E3DBCC` (first cell has no left padding, last no right padding). Each cell: numeral 28px/500 over a 10px uppercase label at `0.55`. Values: **412** Samlet inn · **118** Unike saker · **14** Over terskel (numeral in rust) · **7** Til vurdering.
3. **Active-list line** — `padding: 26px 0 8px`, baseline flex, `gap: 20px`: "VISER" at `0.55` then the active list name in full-strength petroleum, both 11px uppercase.
4. **List blurb** — 18px serif at `0.75`, `max-width: 56ch`, `margin-bottom: 34px`. Explains how that watchlist was built. Example: "Bygget rundt omtale av Selvaag-selskaper og av prosjektene våre. 89 merkede eksempler ligger bak."
5. **Feed rows** — a column of `<article>` elements. Each row: `border-top: 1px solid #E3DBCC`, `padding: 30px 0 32px`, `display: grid; grid-template-columns: 76px 1fr; gap: 28px`, `cursor: pointer`. Hover: `background: rgba(250,242,207,0.4)` (fromage at 40%).
   - **Score gutter (76px)** — score numeral 22px/500 (rust if score ≥85, else petroleum), a 4px progress bar (track `#E3DBCC`, fill = same colour, width = `score%`), and the micro label "RELEVANS" (9px/0.13em upper at `0.45`).
   - **Body** — meta row (10px uppercase, `gap: 10px`, wraps): watchlist name in **rust**, source, date, then a cluster chip ("5 kilder") with `background: #F2FCFA`, `border: 1px solid #85B590`, `padding: 3px 8px`. Then the title (25px/600 serif, max 46ch), the summary (17px/1.62 at `0.78`, max 62ch), then the **"why this matters" block**: `padding-left: 16px`, `border-left: 2px solid #B7592E`, italic 16px at `0.68`, max 58ch.
6. **Feed footer** — `border-top: 2px solid #00313B`, `padding-top: 22px`, baseline flex `gap: 16px`: a secondary button "VIS 9 SAKER UNDER TERSKEL" plus an italic 15px note at `0.55`: "Klassifikatoren er usikker på disse. Vurderingen din trener modellen."

Density is deliberately **editorial** — five stories, each with room to be read, rather than a dense table. Do not compress.

---

### 2. Sak (article detail)

**Purpose** — read one story and understand why the system surfaced it. The score is not a black box: the page shows the nearest training examples that produced it.

**Layout** — two columns, `min-height: 100vh`. Main column `flex: 1`, `max-width: 780px`, padding `46px 52px 72px`. Right rail `flex: 0 0 396px`, `border-left: 2px solid #00313B`, `background: #F4F4F2`, padding `46px 34px 72px`, `flex-direction: column`, `gap: 34px`.

**Main column, top to bottom**

1. Back link "← TILBAKE TIL BRIEF" — 11px/0.13em upper, rust, hover petroleum.
2. Meta row — `padding: 30px 0 16px`, 10px uppercase at `0.55`, watchlist name in rust, then source, then date.
3. **h1** — 40px/600 serif, line-height 1.16, tracking −0.01em, max 30ch.
4. `2px solid #00313B` rule, `margin-top: 30px`.
5. **Sammendrag** — label (10px/0.15em upper at `0.5`), then 20px/1.6 serif. Block padding `26px 0 30px`, `border-bottom: 1px solid #E3DBCC`.
6. **"Derfor er dette relevant for oss"** — the signature element. `background: #FAF2CF`, `padding: 30px 28px`, `margin: 30px 0`. Rust uppercase label, then 19px/1.6 serif, then an italic 14px caveat at `0.55`: "Generert av språkmodell. Kun for saker over terskel." The caveat is load-bearing — it tells the reader this paragraph is machine-written.
7. **Utdrag** — label, then 2–3 paragraphs at 17px/1.7, `0.85` alpha, max 66ch. Then a link "LES HOS {SOURCE} →" (11px/0.12em upper, rust).

**Right rail, top to bottom**

1. **Relevansscore** — label, then the score at 46px/500 rust with "/ 100" at 13px/`0.5` on the baseline, a 6px progress bar, then a 15px note at `0.7` explaining the score ("Høyt over terskel. Modellen kjenner igjen mønsteret transaksjon + Fornebu + regulert volum fra 11 tidligere flagg.").
2. **Nærmeste treningseksempler** — 3 rows, each `border-bottom: 1px solid #E3DBCC`, `padding-bottom: 12px`: similarity in rust 12px Archivo (fixed 38px column, Norwegian decimal comma: `0,91`) + title at 14px/1.45.
3. **Samme sak i N kilder** — one row per source in the dedup cluster: article title (14px) over source name (10px uppercase at `0.45`), separated by `1px` rules.
4. **Fra arkivet** — 2 related archive hits: title over a meta line "Estate · april 2026 · 0,78".
5. **Action block** — pinned with `margin-top: auto`, `border-top: 2px solid #00313B`, `padding-top: 20px`, `gap: 10px`. Primary "FLAGG SOM VIKTIG" (rust fill, `padding: 13px 16px`; hover petroleum) which toggles to "FLAGGET SOM VIKTIG ✓" with a petroleum fill. Secondary "IKKE RELEVANT" (`2px solid rgba(0,49,59,0.4)`, label at `0.75`; hover border petroleum, fill `#E3DBCC`). Then a 13px italic note at `0.55`: "Begge valg går inn som treningsdata for din watchliste."

The flag/reject pair is the training loop's only UI. Both actions must persist as labelled examples against the user's watchlist.

---

### 3. Kilder og drift (admin)

**Purpose** — answer "is this thing working, and what is it made of?" for IT and for whoever owns the pipeline.

**Layout** — single column, `max-width: 1180px`, same page padding. Below the header, a `1.55fr / 1fr` two-column grid with `gap: 44px`.

**Components**

1. **Header** — same pattern as the brief. Eyebrow "DRIFT · 3. SEPTEMBER 06:12", h1 "KILDER OG DRIFT", right-side secondary button "KJØR INNSAMLING NÅ".
2. **Health strip** — 3-column grid, `border-bottom: 2px solid #00313B`, cells split by `1px solid #E3DBCC`, cell padding `26px 24px 26px 0`. Each: 10px uppercase label at `0.5`, value at 24px/500 (rust when it warrants attention), then a 14px note at `0.65`.
   - Innsamling — "Grønn" — "34 av 34 kilder svarte. Siste feil for 6 døgn siden."
   - Duplikatklynging — "294 slått sammen" — "Terskel 0,85 cosinus over et rullerende vindu på 72 timer."
   - Språkmodell — "16 kall" (rust) — "Sammendrag og begrunnelse for saker over terskel, pluss 4 usikre."
3. **Kilder table** (left column) — h2 "KILDER". Grid `1.5fr 0.7fr 0.7fr 0.9fr`. Header row: Kilde / Type / 7 døgn / Status, 10px uppercase at `0.5`, `border-bottom: 2px solid #00313B`. Rows: name 15px serif, type 11px uppercase at `0.55`, count 14px Archivo, status = a 6×6px square in the status colour + 11px uppercase label. Petroleum for "Aktiv"; rust for "Delvis" and "Betalingsmur". Each row `border-bottom: 1px solid #E3DBCC`, `padding-bottom: 13px`. Ten sample sources, sorted by 7-day volume descending.
4. **Right column**, three stacked blocks with `gap: 34px`:
   - **Modeller** — 3 entries (Embedding / Klassifikator / Språkmodell), each: role label, model name 16px, note 14px at `0.62`, `border-bottom: 1px solid #E3DBCC`. Names in the sample: `NbAiLab/nb-sbert-base`, `SetFit på nb-sbert-base`, "Kun sammendrag og begrunnelse".
   - **Treningsgrunnlag** — `background: #F2FCFA`, `border: 2px solid #85B590`, `padding: 24px`. Big numeral 34px/500 ("142") with "merkede eksempler" beside it, a 15px paragraph at `0.75` breaking the count down by department plus holdout precision, then a text button "TREN MODELLEN PÅ NYTT →" separated by a `1px solid #85B590` top rule.
   - **Siste kjøring** — 6 log lines, each a 44px timestamp column (12px Archivo at `0.45`) plus text at 14px/1.5 and `0.78`.

---

### 4. Mobil

**Purpose** — show the responsive intent for the two reading screens. Not a separate product; the same content in one column.

**Layout** — the two mobile frames sit side by side in a wrapping flex row with `gap: 40px`, each `390px` wide with a `2px solid #00313B` outline. In production these are of course the same routes at a narrow viewport, not separate views.

**Frame A — brief**
- Petroleum top bar, `padding: 16px 20px`, space-between: "NYHETSRADAR" and "UKE 36" in mint.
- Header block, `padding: 22px 20px 8px`, `border-bottom: 2px`: rust list-name label, "UKENS BRIEF" at 26px/500 upper, then a `gap: 18px` row of two 14px stats at `0.65`.
- Three feed items, each `padding: 20px`, `border-bottom: 1px solid #E3DBCC`, `gap: 9px`: meta row where the **score becomes a filled rust chip** (`padding: 3px 7px`, paper text) followed by source and date; title 20px/600; then the "why this matters" block with its `2px` rust left border at 15px italic.
- Footer row: "VIS ALLE 14" and "→" in rust, space-between.

**Frame B — article**
- Petroleum top bar with "← BRIEF".
- Title block `padding: 22px 20px 24px`, `border-bottom: 2px`: score chip + source, then the title at 26px/600.
- **Fromage "why this matters" block immediately below the title** — on mobile this is promoted above the summary, because it is the one paragraph that justifies opening the story.
- Summary block, `border-bottom: 1px`.
- Action buttons stacked full-width, `padding: 14px 16px` each — rust primary, outlined secondary. Both clear the 44px minimum hit target.

The reordering in Frame B (why-this-matters before summary) is the only content difference between mobile and desktop and should be preserved.

---

## Interactions & Behavior

**Navigation**
- Sidebar nav switches screens. Active state = the 6×6px rust square at `opacity: 1`.
- Sidebar watchlist click: set active list **and** go to the brief.
- Feed row click (anywhere in the row): open that story's detail, and reset the flag state.
- "← Tilbake til brief" returns to the brief.

**Hover states** (all instant, no transition specified — if the codebase has a standard easing, `~120ms ease-out` on colour is appropriate)
- Feed row: `background: rgba(250,242,207,0.4)`.
- Sidebar nav: label → mint. Sidebar watchlist: label → fromage.
- Secondary button: fill `#FAF2CF` (or `#E3DBCC` for the muted "Ikke relevant" variant, plus border → petroleum).
- Primary rust button: fill and border → petroleum.
- Text/link buttons: rust → petroleum. Body links: rust → petroleum + underline.

**Flag toggle** — "Flagg som viktig" toggles to "Flagget som viktig ✓" with a petroleum fill. In production this should be an optimistic write to the training store with an undo affordance; the prototype only toggles local state.

**Not yet designed** — loading states, empty states (no stories above threshold this week), error states (pipeline failed, source unreachable), the "vis 9 saker under terskel" expansion, the digest send/Teams share flows, and pagination beyond the current week. Each of these needs a design pass before build. Ask before inventing them.

**Responsive** — desktop is the primary target; the two mobile frames define the narrow-viewport intent for the brief and the article. The admin screen has no mobile design. Sensible breakpoint behaviour: below ~1100px collapse the article-detail right rail beneath the main column; below ~760px use the mobile layouts and replace the fixed sidebar with a top bar.

## State Management

Prototype state (in `Nyhetsradar.dc.html`):

| Variable | Values | Trigger |
|---|---|---|
| `screen` | `brief` \| `art` \| `admin` \| `mobile` | sidebar nav, feed row click, back link |
| `sel` | index into the story array | feed row click |
| `list` | watchlist id (`fu`, `komm`, `led`, `min`) | sidebar watchlist click |
| `flagged` | boolean | flag button; reset on story change |

In production, `screen` and `sel` become routing (`/brief/:week`, `/sak/:id`, `/drift`), `list` is a query param or persisted user preference, and `flagged` is server state.

Prototype props (tweakable in the design host, not necessarily production features): `accent` (rust / petroleum / mint), `watchlistScope` (`begge` / `rolle` / `person`), `showScores` (boolean — hides the numeric score while keeping the bar, for stakeholders who read a number as more precise than it is).

**Data the frontend needs**

- **Brief** — week identifier and date range; pipeline counts (collected, unique stories, above threshold, pending review); the active watchlist's name, count and provenance blurb; and per story: id, watchlist name, source, date, cluster size, title, summary, why-this-matters, relevance score 0–100.
- **Article** — everything above plus body excerpt paragraphs, canonical source URL, a score explanation, nearest training examples (similarity + title), the full dedup cluster (title + source per member), and related archive hits (title + source + date + similarity).
- **Admin** — three health metrics (label, value, note); per source: name, ingest type, 7-day count, status; the model stack (role, name, note); training-basis counts by department plus holdout precision; and the last run's log lines (timestamp + message).

**Norwegian formatting** — decimal comma throughout (`0,91`, `0,81`), lowercase month names (`2. sep`, `31. august`), space as thousands separator (`1 900`), and "kroner"/"millioner" spelled out in prose.

## Assets

None. No images, no icon set, no SVG. Every visual element is type, a rule, a filled rectangle, or an arrow/checkmark character (`→`, `←`, `✓`, `×`).

Fonts in the prototype load from Google Fonts: Archivo (400/500/600) and Source Serif 4 (400/600 + italic). **Replace both** with the licensed Selvaag Sans and Tiempos webfonts, self-hosted, in any real deployment.

The Selvaag brand system (profile manual at profilmanual.selvaageiendom.no) is the authority for colour, type and the "Kunsten å utvikle eiendom" line. If the target codebase already implements the brand system, use its tokens rather than the hex values above — the values here are transcriptions of that system, not a new palette.

## Files

- `Nyhetsradar.dc.html` — the full prototype: all four screens, sample data, and interaction logic. Open it directly in a browser. Screen markup is delimited by comments (`<!-- ===== UKENS BRIEF ===== -->` and so on); sample data sits in the script block as the constants `LISTS`, `ITEMS`, `HEALTH`, `SOURCES`, `MODELS`, `LOG`.
- `README.md` — this document.
