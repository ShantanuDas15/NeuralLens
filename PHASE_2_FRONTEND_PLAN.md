# NeuralLens — Phase 2 Frontend Development Plan
### React 18 + Vite · Firebase Auth · Industry-Grade UI/UX

> **Mandate**: The backend is fully implemented, tested, and hardened. Phase 2 builds the React frontend from scratch — no code is scaffolded until this plan is fully reviewed and approved.
> This document is the single execution guide for Phase 2. Update task checkboxes and commit hashes after each milestone is validated.

---

## System & Constraint Audit

| Property | Value | Notes |
|----------|-------|-------|
| **OS** | Linux (Ubuntu) | Native dev environment |
| **Node** | 20+ LTS | Required for Vite 5 |
| **Backend URL** | `http://localhost:8000` | Dev; production URL via `.env` |
| **CORS Origin** | `http://localhost:5173` | Vite default; already whitelisted in backend |
| **Firebase Project** | `neurallens-*` | Auth project with Email/Password + Google OAuth |
| **Max Upload** | 2 MB | Enforced on both frontend (validation) and backend (413) |
| **Auth** | Firebase ID Token (Bearer) | Injected via Axios interceptor on every request |
| **Free-Tier Constraints** | Firebase Spark plan | No Cloud Functions needed; Auth free tier is sufficient |

---

## Design System Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Color Mode** | Dark-first (with system-aware) | AI tools benefit from dark mode focus; premium feel |
| **Primary Accent** | Violet to Indigo gradient (`#7C3AED` to `#4F46E5`) | Modern, sophisticated AI brand color |
| **Secondary Accent** | Cyan (`#06B6D4`) | Contrasts cleanly for interactive highlights |
| **Background** | `#09090B` (Zinc-950) base | Maximizes contrast for image previews |
| **Surface** | `#18181B` (Zinc-900) cards | Subtle layering hierarchy |
| **Typography** | `Inter` (Google Fonts) | Industry standard — clean, legible, modern |
| **Border Radius** | `12px` base, `8px` compact | Soft premium card aesthetic |
| **Animation** | Micro-transitions (200ms ease) | Smooth without feeling sluggish |
| **Icon Library** | `lucide-react` | Lightweight, consistent, tree-shakeable |
| **Image Comparison** | Custom CSS + pointer events | No heavy third-party slider library needed |

---

## Current Project Progress

| Artefact | Status |
|---------|--------|
| `PROJECT.md` | Complete |
| `DATABASE_DESIGN.md` | Complete |
| `GEMINI.md` | Complete |
| `PHASE_1_BACKEND_PLAN.md` | Complete — All 5 milestones + hardening done |
| `backend/` directory | Fully implemented, 45/45 tests passing |
| `frontend/` directory | Not yet created — Phase 2 begins here |
| `docker-compose.yml` | Ready for full-stack deployment |
| Git repository | Clean `main` branch |

---

## Final Frontend Directory Structure

```
frontend/
├── index.html                        # Root HTML entry point
├── vite.config.js                    # Vite build configuration + proxy
├── .env.local                        # Firebase keys (gitignored)
├── .env.local.example                # Committed template
├── package.json
├── public/
│   └── logo.svg                      # NeuralLens logo mark
└── src/
    ├── main.jsx                      # React entry — mounts App
    ├── App.jsx                       # Route definitions, AuthProvider
    ├── index.css                     # Global CSS design system tokens
    │
    ├── firebase.js                   # Firebase SDK init (auth + app)
    ├── api.js                        # Axios instance + auth interceptor
    │
    ├── contexts/
    │   └── AuthContext.jsx           # Auth state, user object, loading
    │
    ├── hooks/
    │   ├── useAuth.js                # Consumes AuthContext
    │   └── useApi.js                 # Wraps fetch calls with loading/error state
    │
    ├── components/
    │   ├── layout/
    │   │   ├── Navbar.jsx            # Top nav with user avatar + links
    │   │   └── PageShell.jsx         # Consistent page wrapper with padding
    │   ├── ui/
    │   │   ├── Button.jsx            # Reusable button with variants + loading
    │   │   ├── Card.jsx              # Surface card container
    │   │   ├── Input.jsx             # Styled text/email/password input
    │   │   ├── Spinner.jsx           # Animated loading indicator
    │   │   ├── Toast.jsx             # Lightweight toast notifications
    │   │   └── Badge.jsx             # Status pill (completed / processing / failed)
    │   ├── auth/
    │   │   └── GoogleSignInButton.jsx # Branded Google OAuth button
    │   ├── upload/
    │   │   ├── DropZone.jsx          # Drag-and-drop upload area
    │   │   └── UploadProgress.jsx    # Animated upload + processing state
    │   └── compare/
    │       └── ImageCompare.jsx      # Interactive LR vs SR drag slider
    │
    └── pages/
        ├── Login.jsx                 # Email/pass + Google login
        ├── Signup.jsx                # Email/pass signup with validation
        ├── Dashboard.jsx             # Core upload + compare experience
        ├── History.jsx               # Paginated job history grid
        └── Profile.jsx               # User info + usage stats
```

---

## Dependencies

### Production
| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^18.3.1 | Core UI library |
| `react-dom` | ^18.3.1 | DOM renderer |
| `react-router-dom` | ^6.26.1 | Client-side routing |
| `firebase` | ^10.13.1 | Firebase Auth SDK |
| `axios` | ^1.7.7 | HTTP client |
| `lucide-react` | ^0.447.0 | Icon set |

### Development
| Package | Version | Purpose |
|---------|---------|---------|
| `vite` | ^5.4.2 | Build tool + dev server |
| `@vitejs/plugin-react` | ^4.3.1 | React JSX transform |

> **No CSS frameworks**. All styling via Vanilla CSS with custom properties. This is mandated by PROJECT.md.

---

## API Contract Reference (Backend to Frontend)

| Endpoint | Method | Auth | Response Shape |
|----------|--------|:----:|----------------|
| `/health` | GET | No | `{ status, version }` |
| `/api/enhance` | POST | Yes | `{ job_id, status, result_url, input_w, input_h, output_w, output_h, processing_time_ms }` |
| `/api/history` | GET | Yes | `{ items: HistoryItem[], total, page, page_size }` |
| `/api/profile` | GET | Yes | `{ uid, email, display_name, photo_url, auth_provider, member_since, stats }` |
| `/api/results/{filename}` | GET | Yes | Image binary |

---

---

## Milestone 2.1 — Project Scaffold & Design System

**Goal**: Bootstrap the Vite + React project, configure dev proxy, and implement the full CSS design system with all tokens, utilities, and base resets.

### Tasks
- `[ ]` Initialize Vite + React project inside `frontend/`
- `[ ]` Install all production and dev dependencies
- `[ ]` Configure `vite.config.js` with `/api` proxy to `http://localhost:8000`
- `[ ]` Create `frontend/.env.local.example` with Firebase key placeholders
- `[ ]` Implement `src/index.css` — Full design system (tokens, resets, utilities)
- `[ ]` Implement `src/main.jsx` — React root mount
- `[ ]` Implement basic `src/App.jsx` stub with BrowserRouter
- `[ ]` Verify dev server starts: `npm run dev` at `http://localhost:5173`

### CSS Design Token Specification

```
Color Tokens:
--color-bg:            #09090B   Page background (Zinc-950)
--color-surface:       #18181B   Cards, modals (Zinc-900)
--color-surface-alt:   #27272A   Inputs, hover (Zinc-800)
--color-border:        #3F3F46   Dividers, input borders (Zinc-700)
--color-text-primary:  #FAFAFA
--color-text-secondary:#A1A1AA
--color-text-muted:    #71717A

Accent Colors:
--color-accent-from:   #7C3AED   Violet-600 (gradient start)
--color-accent-to:     #4F46E5   Indigo-600 (gradient end)
--color-accent:        #7C3AED   Single accent for borders/focus
--color-cyan:          #06B6D4   Cyan-500 — secondary interactive

Status Colors:
--color-success:   #22C55E
--color-warning:   #F59E0B
--color-error:     #EF4444

Spacing:
--radius-sm:   6px
--radius-md:   12px
--radius-lg:   16px
--radius-pill: 9999px

Shadows:
--shadow-card: 0 4px 24px rgba(0,0,0,0.4)
--shadow-glow: 0 0 32px rgba(124,58,237,0.25)
```

### Verification Gateway
```bash
cd frontend && npm run dev
# Vite server starts at http://localhost:5173
# No console errors
# Hot reload works
```

### Completion Checklist
- `[ ]` frontend/ directory created and npm install succeeds
- `[ ]` vite.config.js proxy routes /api to backend port 8000
- `[ ]` index.css contains all design tokens
- `[ ]` App renders without errors in browser
- **Status**: `[ ] Pending`

**Commit**: `feat: Implement Milestone 2.1 — Frontend scaffold and design system`

---

## Milestone 2.2 — Firebase Auth Integration

**Goal**: Configure Firebase SDK, implement AuthContext, protect routes, and build the Login and Signup pages with full validation and premium UI.

### Tasks
- `[ ]` Create `src/firebase.js` — Firebase app + auth init from env vars
- `[ ]` Create `src/contexts/AuthContext.jsx` — Provides user, loading, signOut
- `[ ]` Create `src/hooks/useAuth.js` — Clean consumer hook
- `[ ]` Implement ProtectedRoute component logic inside `App.jsx`
- `[ ]` Create `src/api.js` — Axios instance with base URL + auth interceptor
- `[ ]` Implement `src/pages/Login.jsx` — Email/pass + Google Sign-In, error feedback
- `[ ]` Implement `src/pages/Signup.jsx` — Email/pass with confirm + validation
- `[ ]` Wire routes in `App.jsx`: `/login`, `/signup`, `/` (protected dashboard)
- `[ ]` Add `GoogleSignInButton.jsx` component

### AuthContext API
```
Provides: { user, loading, signOut }
- user: Firebase User object or null
- loading: boolean (initial auth state resolving)
- signOut: calls Firebase signOut then navigates to /login
```

### Login Page UX Requirements
- Full-page centered card layout on dark background with glassmorphism effect
- NeuralLens logo/wordmark at top of card
- Email + Password inputs with error state (red border + message below)
- Primary gradient "Sign In" button — full-width, shows spinner during request
- Horizontal "or" divider with lines
- Google Sign-In button with Google SVG icon, white background on dark
- "Don't have an account? Sign Up" link below
- Smooth 300ms fade-slide-up animation on page load
- Error toast on invalid credentials

### Signup Page UX Requirements
- Same card layout as Login
- Fields: Display Name, Email, Password, Confirm Password
- Real-time password strength meter: weak (red) / medium (amber) / strong (green)
- Confirm Password match validation
- Submit shows loading state; on success auto-login and redirect to dashboard

### Verification Gateway
```
Manual verification:
1. Navigate to /login — renders clean auth card
2. Submit wrong credentials — error message appears under inputs
3. Sign in with Google account — redirected to /
4. Navigate to / while unauthenticated — redirected to /login
5. Refresh while authenticated — user persists without flash
6. Sign up new account — auto-logged in and redirected to dashboard
```

### Completion Checklist
- `[ ]` Firebase SDK initializes without console errors
- `[ ]` AuthContext provides user state across the app
- `[ ]` Unauthenticated users redirected from protected routes
- `[ ]` Google OAuth flow works end-to-end
- `[ ]` Email/password login and signup work
- `[ ]` Login/Signup pages match the design spec
- **Status**: `[ ] Pending`

**Commit**: `feat: Implement Milestone 2.2 — Firebase Auth integration and auth pages`

---

## Milestone 2.3 — Layout Shell & Navigation

**Goal**: Build the persistent layout shell (Navbar + page wrapper) and all UI primitives that all authenticated pages share.

### Tasks
- `[ ]` Create `src/components/layout/Navbar.jsx`
- `[ ]` Create `src/components/layout/PageShell.jsx`
- `[ ]` Create UI primitives: `Button.jsx`, `Card.jsx`, `Input.jsx`, `Spinner.jsx`, `Badge.jsx`, `Toast.jsx`
- `[ ]` Implement `src/hooks/useApi.js` with `{ data, loading, error, execute }`
- `[ ]` Integrate Navbar into `App.jsx` for all authenticated routes

### Navbar Specification
- Left: NeuralLens logo SVG wordmark + nav links (Dashboard, History)
- Right: User avatar (photo URL or gradient initials) with dropdown
- Style: Dark background with `backdrop-filter: blur(12px)`, bottom border
- Mobile: Hamburger icon with smooth slide-down menu at < 768px
- Active route: Violet left-border accent on the active link item

### UI Component Contracts

| Component | Props | Visual Behavior |
|-----------|-------|-----------------|
| `Button` | variant (primary/ghost/danger), size (sm/md/lg), loading, disabled | Primary = full gradient; Ghost = transparent border |
| `Card` | className, children | Dark surface, 1px border, shadow-card |
| `Input` | label, error, type, placeholder | Shows red border + error message below on error |
| `Spinner` | size (sm/md/lg) | CSS rotating ring in accent color |
| `Badge` | status (completed/processing/failed/pending) | Color-coded pill with dot |
| `Toast` | message, type (success/error/info), duration | Slides in from top-right, auto-dismisses |

### Verification Gateway
```
Manual verification:
1. Log in — Navbar appears with logo, nav links, avatar
2. Click Dashboard link — navigates to /
3. Click History link — navigates to /history
4. Click avatar — dropdown shows Profile and Logout options
5. Click Logout — signs out and redirects to /login
6. Resize below 768px — Navbar collapses to hamburger gracefully
```

### Completion Checklist
- `[ ]` Navbar renders consistently on all auth pages
- `[ ]` All UI primitives implemented and visually consistent
- `[ ]` useApi hook tracks loading/error/data state
- `[ ]` Mobile responsiveness confirmed at 375px, 768px, 1280px
- **Status**: `[ ] Pending`

**Commit**: `feat: Implement Milestone 2.3 — Layout shell, Navbar, and UI primitives`

---

## Milestone 2.4 — Dashboard: Upload, Processing & Image Comparison

**Goal**: The core user experience — drag-and-drop upload, animated processing state, and the interactive before/after comparison slider.

### Tasks
- `[ ]` Implement `src/components/upload/DropZone.jsx`
- `[ ]` Implement `src/components/upload/UploadProgress.jsx`
- `[ ]` Implement `src/components/compare/ImageCompare.jsx`
- `[ ]` Implement `src/pages/Dashboard.jsx` orchestrating all components
- `[ ]` Wire `POST /api/enhance` via `api.js` with correct `multipart/form-data` payload
- `[ ]` Display result metadata: input/output dimensions, processing time

### DropZone Specification
- Dashed border rectangle with cloud-upload icon and "Drop your image here" text
- Drag-over state: border pulses violet, background lightens, scale(1.02)
- Click to open file picker — accept JPEG/PNG only, max 2MB
- Client-side validation with inline error messages
- On file selected: show thumbnail preview + filename + size chip
- "Enhance Image" CTA button — primary gradient, full-width

### UploadProgress State Machine
```
IDLE       — DropZone visible
UPLOADING  — Animated horizontal progress bar, "Uploading..." text
PROCESSING — Pulsing spinner, "Real-ESRGAN processing..." + elapsed time counter
COMPLETE   — Smooth 400ms transition to ImageCompare component
ERROR      — Error card with message, "Try Again" button
```

### ImageCompare Specification
- `position: relative` container holding two stacked images
- Draggable vertical divider with circular handle (32px circle, violet bg)
- Left panel: original LR image clipped via CSS clip-path
- Right panel: enhanced SR image
- Drag handle smoothly reveals left/right images (60fps)
- Labels: "Original" left badge, "Enhanced 4x" right badge (semi-transparent)
- Below slider: "Download Enhanced" button + "Enhance Another" ghost button
- Metadata chip: `{input_w}x{input_h} → {output_w}x{output_h} · {ms}ms`

### Verification Gateway
```
Manual verification:
1. Drag valid PNG — thumbnail + filename appear in DropZone
2. Click Enhance — progress bar and processing spinner shown
3. Backend responds — ImageCompare slider appears smoothly
4. Drag slider handle — LR/SR images reveal correctly
5. Click Download Enhanced — file downloads to local machine
6. Drop a file > 2MB — inline error shown, no API call
7. Drop a .gif file — format error shown
8. Backend returns 429 — Toast shows rate limit message
9. Backend returns 500 — Error state shown with retry option
```

### Completion Checklist
- `[ ]` DropZone validates file type and size before upload
- `[ ]` Upload and processing states render correctly
- `[ ]` API call sends correct multipart/form-data with Bearer token
- `[ ]` ImageCompare slider is smooth and touch-friendly on mobile
- `[ ]` Download button works for result image
- `[ ]` All error states handled with user-friendly messages
- **Status**: `[ ] Pending`

**Commit**: `feat: Implement Milestone 2.4 — Dashboard upload, processing, and comparison`

---

## Milestone 2.5 — History & Profile Pages

**Goal**: Build the paginated enhancement history grid and the user profile page with stats.

### Tasks
- `[ ]` Implement `src/pages/History.jsx` — Grid of past jobs with pagination
- `[ ]` Implement `src/pages/Profile.jsx` — User stats + account info
- `[ ]` Wire `GET /api/history?page=N&page_size=12`
- `[ ]` Wire `GET /api/profile`

### History Page Specification
- Header: "Enhancement History" with total count pill badge
- Responsive grid: 3-col (desktop) / 2-col (tablet) / 1-col (mobile)
- Job card contains:
  - Thumbnail of result image from result_url
  - Original filename (truncated)
  - Badge for status: completed (green) / failed (red) / processing (amber)
  - Input to output dimensions
  - Relative timestamp ("2 hours ago") with ISO on hover tooltip
  - Download icon button (aria-label="Download result")
- Empty state: Centered illustration + "No enhancements yet" + Upload CTA
- Pagination: Previous/Next buttons + "Page 1 of 4" indicator
- Loading state: Skeleton shimmer cards (CSS animation, no spinner)

### Profile Page Specification
- Avatar section: photo_url image or gradient initials avatar
- User info card: Display name, email, auth provider badge
- Member since date formatted as "August 2026"
- Stats grid (2 columns):
  - Total Enhancements (violet accent)
  - Successful (green)
  - Failed (red)
  - Last Enhancement date
- Logout button: Full-width at bottom, danger/ghost variant with confirmation

### Verification Gateway
```
Manual verification:
1. Navigate to /history — cards load (or empty state)
2. Paginate forward/back — new page loads, scroll resets to top
3. Click download icon — result image downloads
4. Navigate to /profile — name, email, provider all shown
5. Stats match backend values
6. Logout from profile — signs out and redirects to /login
```

### Completion Checklist
- `[ ]` History grid renders jobs with correct metadata and thumbnails
- `[ ]` Pagination controls work correctly
- `[ ]` Skeleton loading state shows during data fetch
- `[ ]` Empty state renders when user has no jobs
- `[ ]` Profile page displays all user fields and stats
- `[ ]` Logout works from Profile page
- **Status**: `[ ] Pending`

**Commit**: `feat: Implement Milestone 2.5 — History and Profile pages`

---

## Milestone 2.6 — Polish, Responsiveness & Accessibility

**Goal**: Final quality gate — every page fully responsive, animated, accessible, and production-ready.

### Tasks
- `[ ]` Audit all pages at 375px, 768px, and 1280px widths
- `[ ]` Add page-level transition animations (fadeSlideUp)
- `[ ]` Ensure all interactive elements have `:focus-visible` styles
- `[ ]` Add `aria-label` to all icon-only buttons
- `[ ]` Set `document.title` per page for browser tab clarity
- `[ ]` Test full flow with keyboard navigation only
- `[ ]` Confirm zero `console.error` or `console.warn` in browser
- `[ ]` Confirm `npm run build` produces a clean production bundle

### Animation Specification
```css
Page entrance — applied to all top-level page containers:
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
Duration: 300ms, timing: ease, fill: forwards

Skeleton shimmer for loading cards:
@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position:  200% 0; }
}
Background: linear-gradient(90deg, surface, surface-alt, surface)
Background-size: 200% 100%
Duration: 1.5s, timing: linear, iteration: infinite
```

### Responsive Breakpoints
```
Mobile-first approach:
Base styles:              mobile  (< 640px)
@media min-width 640px:  tablet
@media min-width 1024px: desktop
@media min-width 1280px: wide desktop
```

### Verification Gateway
```bash
# Build verification:
cd frontend && npm run build
# No errors — dist/ created successfully

# Manual device verification:
# iPhone 14 (390px): no overflow, no broken layouts
# iPad (768px): 2-column history grid
# Desktop 1440px: 3-column history, wide compare slider

# Accessibility:
# Tab through Login: all inputs focusable in logical order
# All img elements have alt text
# All icon buttons have aria-label
```

### Completion Checklist
- `[ ]` All pages pass visual QA at all three breakpoints
- `[ ]` Page transitions animate smoothly
- `[ ]` Keyboard navigation works across all pages
- `[ ]` `npm run build` succeeds with no errors or warnings
- `[ ]` No console errors in production build preview
- **Status**: `[ ] Pending`

**Commit**: `feat: Implement Milestone 2.6 — Polish, responsiveness, and accessibility`

---

## Phase 2 Completion Gate

> **All of the following must be true before Phase 3 (Deployment / DevOps) begins:**

- `[ ]` All 6 milestones complete and committed
- `[ ]` Full user flow works end-to-end: Signup → Upload → Compare → History → Profile → Logout
- `[ ]` Google OAuth and Email/Password auth both work
- `[ ]` Image comparison slider is smooth with no jank
- `[ ]` All 5 pages are responsive at 375px, 768px, 1280px
- `[ ]` `npm run build` produces a clean bundle
- `[ ]` No console errors or warnings in the browser
- `[ ]` All API endpoints called with correct Bearer token
- `[ ]` Error states (429, 413, 415, 500) handled gracefully with user-friendly messages
- `[ ]` All milestone commits pushed to GitHub `main`

---

## Progress Log

| Milestone | Status | Commit Hash | Date |
|-----------|--------|-------------|------|
| 2.1 — Scaffold & Design System | `[ ] Pending` | — | — |
| 2.2 — Firebase Auth Integration | `[ ] Pending` | — | — |
| 2.3 — Layout Shell & Navigation | `[ ] Pending` | — | — |
| 2.4 — Dashboard & Image Compare | `[ ] Pending` | — | — |
| 2.5 — History & Profile Pages | `[ ] Pending` | — | — |
| 2.6 — Polish & Accessibility | `[ ] Pending` | — | — |
| **Phase 2 Complete** | `[ ] Pending` | — | — |
