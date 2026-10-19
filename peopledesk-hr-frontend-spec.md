# PeopleDesk HR — Frontend Specification

A complete build spec for an HR management frontend. Give this file to any code
generator (Blackbox AI, etc.) to reproduce the UI.

---

## 1. Product summary

**Name:** PeopleDesk HR
**Tenant shown in UI:** Nexus Technologies (Pvt) Ltd
**Purpose:** HR dashboard for employees, attendance, leave and payroll, plus a
branded sign-in page.

**Pages**

| Route | Purpose |
| --- | --- |
| `/` | HR dashboard (stats, leave requests table, headcount by department) |
| `/auth` | Sign-in card with password visibility toggle |

---

## 2. Tech stack

- React 19 + TypeScript
- TanStack Start / TanStack Router (file-based routing under `src/routes`)
- Vite 7
- Tailwind CSS v4 (configured in `src/styles.css`, no `tailwind.config.js`)
- `lucide-react` icons
- Fonts via Google Fonts `<link>`: **Sora** (headings), **Plus Jakarta Sans** (body)

If your target stack is plain HTML/CSS or Next.js, keep the exact design tokens
and layout described below and swap only the routing layer.

---

## 3. Design system

All colors are **oklch** CSS variables. Never hardcode hex/`text-white` in components.

### Light theme tokens (`:root`)


--radius: 0.9375rem;              /* 15px */
--background:        oklch(0.972 0.005 255);   /* soft grey-blue #f4f6f9 feel */
--foreground:        oklch(0.24 0.03 265);
--card:              oklch(1 0 0);
--card-foreground:   oklch(0.24 0.03 265);
--popover:           oklch(1 0 0);
--popover-foreground:oklch(0.24 0.03 265);
--primary:           oklch(0.58 0.17 279);     /* indigo-violet */
--primary-foreground:oklch(0.99 0.003 250);
--primary-glow:      oklch(0.48 0.18 305);     /* gradient end */
--secondary:         oklch(0.958 0.008 265);
--secondary-foreground: oklch(0.32 0.04 265);
--muted:             oklch(0.958 0.008 265);
--muted-foreground:  oklch(0.55 0.03 260);
--accent:            oklch(0.94 0.03 279);
--accent-foreground: oklch(0.35 0.11 279);
--success:           oklch(0.68 0.15 155);
--warning:           oklch(0.78 0.16 75);
--info:              oklch(0.68 0.13 230);
--destructive:       oklch(0.577 0.245 27.325);
--border:            oklch(0.929 0.013 255.508);
--input:             oklch(0.929 0.013 255.508);
--ring:              oklch(0.704 0.04 256.788);

--gradient-brand: linear-gradient(135deg, var(--primary) 0%, var(--primary-glow) 100%);
--shadow-card:       0 5px 15px oklch(0.2 0.03 265 / 0.12);
--shadow-card-hover: 0 12px 28px oklch(0.2 0.03 265 / 0.18);
--shadow-auth:       0 15px 50px oklch(0.2 0.03 265 / 0.25);


A `.dark` variant exists with a near-black `oklch(0.129 0.042 264.695)` background
and light foreground; mirror every token above.

### Typography

- Headings (`h1,h2,h3`): `Sora`, weights 600/700/800
- Body: `Plus Jakarta Sans`, weights 400/500/600/700
- Dashboard stat value: `40px`, bold, `leading-none`, tight tracking
- Page title: `text-2xl font-bold tracking-tight`
- Labels/meta: `text-xs` / `text-sm` in `--muted-foreground`

### Reusable utilities


@utility stat-card {              /* white card */
  border: none;
  border-radius: var(--radius-lg);      /* 15px */
  background: var(--color-card);
  box-shadow: var(--shadow-card);
  transition: transform .3s ease, box-shadow .3s ease;
  &:hover { transform: translateY(-5px); box-shadow: var(--shadow-card-hover); }
}

@utility bg-brand-gradient { background-image: var(--gradient-brand); }
@utility shadow-auth       { box-shadow: var(--shadow-auth); }
@utility animate-slide-up  { animation: slide-up .5s ease both; }

@keyframes slide-up {
  from { opacity: 0; transform: translateY(30px); }
  to   { opacity: 1; transform: translateY(0); }
}


Radius scale: `--radius-sm/md/lg/xl/2xl/3xl/4xl` = radius −4, −2, +0, +4, +8, +12, +16 px.

---

## 4. Dashboard page (`/`)

Wrapper: `min-h-screen`. Content column: `mx-auto max-w-6xl px-5`.

### 4.1 Header (`border-b border-border bg-card`)

- Left: 40×40 rounded-xl brand-gradient tile with `Users` icon; next to it
  “PeopleDesk HR” (display font, bold) and “Nexus Technologies (Pvt) Ltd” (`text-xs muted`).
- Right (`ml-auto`, gap 3):
  - Search input, hidden below `sm`: height 40px, width 224px, rounded-xl,
    `bg-secondary/60`, `Search` icon absolutely positioned left, placeholder
    “Search employee…”, focus → primary border + `ring-3 ring-primary/15`.
  - Bell button: 40×40 rounded-xl bordered, with a 8px red dot badge top-right.
  - “Sign in” link → `/auth`: brand-gradient pill, `px-4 py-2.5`,
    `text-sm font-semibold`, hover `-translate-y-0.5`.

### 4.2 Greeting row

- `h1`: “Good morning, Sana”
- Sub: “Wednesday, 29 July 2026 — here is how your workforce looks today.”
- Right chip: white card, `Clock` icon + “Payroll cut-off in 1 day”, shadow-card.

### 4.3 Stat cards

Grid: `1 / sm:2 / lg:4` columns, gap 20px. Each `stat-card p-5` contains a
44×44 rounded-xl tinted icon tile, the value, the label, and a delta line with
`TrendingUp` (success color) or `TrendingDown` (warning color).

| Label | Value | Delta | Trend | Icon | Tile tone |
| --- | --- | --- | --- | --- | --- |
| Total Employees | 248 | +12 this quarter | up | `Users` | `text-primary bg-accent` |
| Present Today | 221 | 89.1% attendance | up | `UserCheck` | `text-success bg-success/10` |
| On Leave | 14 | 6 pending approval | down | `CalendarOff` | `text-warning bg-warning/10` |
| Monthly Payroll | ₨ 4.8M | Runs on 30 Jul | up | `Wallet` | `text-info bg-info/10` |

### 4.4 Lower grid (`lg:grid-cols-3`, gap 20px)

**A. Recent leave requests — `lg:col-span-2`, `stat-card p-5`**

Header row: “Recent leave requests” + “View all” (`text-xs text-primary`).
Table `w-full min-w-[520px] text-sm`, horizontally scrollable, header row in
uppercase `text-xs muted`, each row separated by `border-t border-border`.
Employee cell = name (medium) over role (`text-xs muted`).
Status = pill `rounded-full px-2.5 py-1 text-xs font-semibold`:

- Pending → `bg-warning/15 text-warning`
- Approved → `bg-success/15 text-success`
- Rejected → `bg-destructive/10 text-destructive`

| Employee | Role | Type | Duration | Status |
| --- | --- | --- | --- | --- |
| Ayesha Khan | UI Designer | Annual Leave | 3 days | Pending |
| Bilal Ahmed | Backend Engineer | Sick Leave | 1 day | Approved |
| Hira Sadiq | HR Executive | Casual Leave | 2 days | Pending |
| Usman Tariq | Sales Manager | Unpaid Leave | 5 days | Rejected |

**B. Headcount by department — `stat-card p-5`**

List with `space-y-4`; each item: name (left, medium) + count (right, muted),
then an 8px `bg-secondary` rounded track with a brand-gradient fill at `pct` width.

| Department | Count | % width |
| --- | --- | --- |
| Engineering | 96 | 39 |
| Sales & Marketing | 58 | 23 |
| Operations | 44 | 18 |
| Finance | 28 | 11 |
| Human Resources | 22 | 9 |

---

## 5. Auth page (`/auth`)

Full-screen `bg-brand-gradient`, centered, `p-5`.

Card: `max-w-[420px] w-full`, `rounded-3xl bg-card p-10`, `shadow-auth`,
entrance animation `animate-slide-up`.

1. **Head block (centered):** 60×60 brand-gradient circle with `Users` icon,
   `h1` “PeopleDesk HR”, sub “Sign in to your HR workspace”.
2. **Form (`mt-7 space-y-4`)**, submit is `preventDefault` (no backend yet):
   - Work email — label + input, `h-12 rounded-xl border-[1.5px] border-input px-4`,
     placeholder `sana.malik@nexustech.pk`, required.
   - Password — same input plus `pr-12` and a right-aligned toggle button using
     `Eye` / `EyeOff`, `aria-label` “Show password” / “Hide password”; toggles
     input type between `password` and `text`.
   - Row: “Keep me signed in” checkbox (`accent-primary`) and
     “Forgot password?” link (`text-primary hover:underline`).
   - Submit: full-width brand-gradient button, `rounded-xl py-3`,
     `font-semibold`, hover `-translate-y-0.5`.
3. **Footer:** “New employee? **Request an account**” linking to `/`.

Focus state everywhere: `focus:border-primary focus:ring-3 focus:ring-primary/15`.

---

## 6. Responsiveness

- Stat grid: 1 col (mobile) → 2 cols (≥640px) → 4 cols (≥1024px)
- Lower grid: stacked on mobile, 2:1 split at ≥1024px
- Header search hidden below `sm`; header wraps with `flex-wrap gap-4`
- Leave table scrolls horizontally inside `overflow-x-auto`
- Auth card stays ≤420px and keeps 20px viewport padding

---

## 7. SEO / head metadata

Per-route `<head>`; each route has a unique title/description plus
`og:title`, `og:description`, `og:type=website`, `twitter:card=summary_large_image`.

- `/` — “HR Dashboard — Workforce, Attendance & Payroll” /
  “Track headcount, daily attendance, leave requests and monthly payroll for your team in one HR dashboard.”
- `/auth` — “Sign in — PeopleDesk HR” /
  “Sign in to PeopleDesk HR to manage employees, attendance, leave approvals and payroll.”

Also: single `h1` per page, semantic `header`/`main`/`section`/`article`,
`robots.txt` and `sitemap.xml` listing both routes.

---

## 8. Rules for the generator

1. Use only the semantic tokens above — no `text-white`, `bg-black`, or hex literals in components.
2. All data on both pages is static/mock; no API calls, no auth backend.
3. Keep hover motion subtle: cards lift 5px, buttons 2px.
4. Icons come from `lucide-react`: `Users`, `UserCheck`, `CalendarOff`, `Wallet`,
   `TrendingUp`, `TrendingDown`, `Clock`, `Bell`, `Search`, `Eye`, `EyeOff`.
5. Support dark mode through the `.dark` class token set.
