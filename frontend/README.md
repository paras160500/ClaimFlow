# ClaimFlow — Stage 4: React Frontend

A React + Vite (plain JSX, no TypeScript) dashboard for the ClaimFlow internal
claims-investigation platform. Talks to the Stage 3 Node.js API.

## Design

Built as an internal enterprise tool, not a consumer SaaS dashboard: deep
navy sidebar, warm paper canvas, one working accent blue, and a strict
three-color risk system (green/amber/red) used consistently everywhere —
badges, borders, charts, rule-check icons all mean the same thing wherever
they appear. Headings in Space Grotesk, body text in IBM Plex Sans, claim IDs
and money figures in IBM Plex Mono (for alignment/scanning, not decoration).

## Pages

- **Login** — split-screen, with one-click demo account buttons
- **Dashboard** — hero stat, 4 supporting stat cards, claims-over-time line
  chart, risk-distribution bar chart
- **Claims list** — searchable, filterable (type/status/investigation
  status), paginated table
- **Claim detail** — the centerpiece investigation workspace: claim info,
  risk gauge, rule checks, relationship analysis (with clickable "other
  claims at this repair shop" mini-cards), retrieved policy evidence,
  retrieved investigator notes, AI summary (labeled LLM vs. fallback), and
  the human decision panel with investigation history timeline
- **Investigations** — filterable list of open/closed investigations
- **Employees** (Admin only) — list + add-employee modal
- **Audit log** (Admin only) — filterable action history

## Setup

```bash
cd frontend
npm install
cp .env.example .env      # point VITE_API_BASE_URL at your Stage 3 backend
npm run dev
```

Log in with any of the Stage 3 seed accounts (buttons pre-filled on the
login screen): `admin@claimflow.demo`, `investigator@claimflow.demo`,
`reviewer@claimflow.demo`.

## Build

```bash
npm run build   # outputs to dist/
npm run preview # serve the production build locally
```

## Notes

- All API calls go through `src/api/client.js`, which attaches the stored
  login token to every request and redirects to `/login` on a 401.
- Role gating (`RequireRole`) hides Admin-only nav items and pages from
  Investigators/Reviewers — mirrors the RBAC already enforced server-side.
- The Claim Detail page never calls the AI service until you click "Run AI
  Investigation" — this keeps normal browsing fast and avoids re-running the
  LLM every time a claim is opened.
