# Phase 4 — NeuralLens Feature Roadmap

> **Role**: Principal Architect & Senior Software Engineer
> **Scope**: Full-stack feature additions to upgrade NeuralLens from an MVP to a compelling, polished product.

---

## Executive Summary

The current application is a solid, production-hardened MVP: auth, single-image upload, 4× ESRGAN enhancement, comparison slider, history, and profile. The next phase should target **three axes of improvement**:

1. **User Experience** — reduce friction, add delight, improve trust
2. **Feature Depth** — new capabilities that make users return
3. **Infrastructure** — scalability and reliability improvements

The features below are ranked by **Impact / Effort ratio** — highest value, lowest cost first.

---

## Milestone 4.1 — History Page: Delete & Re-Enhance

**Priority**: 🔴 High | **Effort**: Low | **Impact**: High

### Problem
The History page is currently read-only. Users have no way to manage their job list — they cannot remove an unwanted result or re-process an old file.

### Features
- **Soft-delete a job**: Add a trash icon on each history card. On click, show a confirm dialog and call `DELETE /api/history/{job_id}` (sets `deleted_at` — never hard-deletes). The card fades out.
- **Re-enhance button**: A "Process Again" icon that navigates the user back to the Dashboard with the session pre-primed to remind them to re-upload.

### Implementation Plan

#### Backend (`backend/routers/history.py`)
```python
# NEW: DELETE /api/history/{job_id}
@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, current_user: ..., db: ...):
    """Soft-delete an enhancement job (sets deleted_at)."""
    ...
```

#### Frontend (`frontend/src/pages/History.jsx`)
- Add `Trash2` icon button per card with confirm prompt
- Call `api.delete('/history/' + job.job_id)` on confirm
- Remove the card from local state optimistically on success

---

## Milestone 4.2 — Dashboard: Drag & Drop Preview Before Uploading

**Priority**: 🔴 High | **Effort**: Low | **Impact**: High

### Problem
After selecting an image, users immediately kick off processing with no chance to confirm their selection. If they drop the wrong file, they must wait for processing to finish before resetting.

### Features
- Show a **full-resolution preview** of the selected image below the drop zone before the user commits.
- Add a **"Enhance This Image" CTA button** and a **"Choose Different" link** that lets them re-select.
- Processing only starts when the user explicitly clicks the CTA.

### Implementation Plan

#### Frontend (`frontend/src/pages/Dashboard.jsx`)
- New state: `previewState: 'idle' | 'preview' | 'uploading' | 'processing' | 'success' | 'error'`
- When a file is selected, set state to `'preview'` and render a new `<ImagePreview />` component
- The `handleEnhance()` call moves to the CTA button's `onClick`

---

## Milestone 4.3 — Scale Factor Selection (2×, 4×, 8×)

**Priority**: 🟡 Medium | **Effort**: Medium | **Impact**: High | **Status**: ✅ Completed

### Problem
All images are unconditionally upscaled 4×. This wastes processing time for users who only need 2× upscaling and creates unnecessarily large output files.

### Features
- A **scale factor toggle** in the Dashboard (2× / 4× / 8×) before submitting.
- The selected scale is sent as a form field to the backend.
- The backend selects the correct model weights.

### Implementation Plan

#### Backend
- Add `scale: int = Form(4)` to the `/api/enhance` endpoint.
- Load an `x2` RealESRGAN model variant at startup (`RealESRGAN_x2plus.pth`) alongside the existing `x4`.
- A model registry (`ModelConfig` table is already seeded for this) routes the request to the correct `RealESRGANer` instance.

#### Frontend (`frontend/src/pages/Dashboard.jsx`)
- Add a `<ScalePicker />` component: 3 buttons (`2×`, `4×`, `8×`) styled as a toggle group.
- Pass `scale` as a field in the `FormData` sent to the backend.

---

## Milestone 4.4 — History Page: In-Page Comparison Viewer

**Priority**: 🟡 Medium | **Effort**: Medium | **Impact**: High | **Status**: ✅ Completed

### Problem
Users cannot re-view the side-by-side comparison for a historical job. Clicking the "View" icon opens the raw result image in a new browser tab — this is not the same rich experience as the interactive slider.

### Features
- A **"Compare" button** on each history card that opens a **full-screen modal** with the `<ImageCompare />` slider pre-loaded with the stored original vs. enhanced images.

### Tasks
- [x] Refactor `<ImageCompare />` to be generic (if it isn't already).
- [x] Add a "Compare" button to each history item.
- [x] Implement an in-page modal or expandable section in `History.jsx` to render the comparison view.

> **Challenge**: The original (LR) image URL is not currently stored. It is only available as a blob URL during the active session.

### Implementation Plan

#### Backend (`backend/routers/enhance.py`)
- Save the original input image to a separate path (already stored to `uploads/`) and expose it via a new route `GET /api/uploads/{filename}` — same auth guard as `GET /api/results/{filename}`.

#### Backend (`backend/routers/history.py`)
- Include `original_url` in the `HistoryItem` schema response.

#### Frontend
- Add a `<Modal />` component (`frontend/src/components/ui/Modal.jsx`).
- Render `<ImageCompare result={selectedJob} />` inside the modal when the "Compare" button is clicked.

---

## Milestone 4.5 — Toast Queue & Enhanced Notifications

**Priority**: 🟡 Medium | **Effort**: Low | **Impact**: Medium

### Problem
The current Toast system shows a single toast at a time. If multiple events fire rapidly (e.g., download + refresh), one notification silently disappears.

### Features
- **Stacked toasts**: Support up to 3 simultaneous visible toasts, each with independent timers.
- **Processing toast with spinner**: When an enhancement starts, show a persistent "Processing your image…" toast that auto-dismisses only on success or error.

### Implementation Plan

#### Frontend (`frontend/src/components/ui/Toast.jsx`)
- The `useReducer` already manages an array. Update the JSX to render all items in the state array, stacked vertically with `position: fixed; bottom: 1rem; right: 1rem; display: flex; flex-direction: column; gap: 0.5rem;`.
- Add a `toast.loading('Processing...')` method that returns an ID. Call `toast.dismiss(id)` when done.

---

## Milestone 4.6 — Dark/Light Theme Toggle

**Priority**: 🟢 Low | **Effort**: Low | **Impact**: Medium

### Problem
The application is hardcoded dark. Some users (especially those using it in bright environments) prefer a light theme.

### Features
- A **theme toggle button** in the Navbar.
- Theme persists across sessions via `localStorage`.

### Implementation Plan

#### Frontend
- Create a `ThemeContext` that sets a `data-theme` attribute on `<html>`.
- Add `[data-theme="light"]` overrides in `index.css` for all CSS custom properties.
- The existing CSS variable system makes this trivially easy — no component-level changes needed.

```css
/* src/index.css */
[data-theme="light"] {
  --color-bg: #F9FAFB;
  --color-surface: #FFFFFF;
  --color-surface-alt: #F3F4F6;
  --color-border: #E5E7EB;
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  --color-text-muted: #9CA3AF;
}
```

---

## Milestone 4.7 — Batch Processing (Multi-Upload)

**Priority**: 🟢 Low | **Effort**: High | **Impact**: Very High

### Problem
Power users want to enhance multiple images without going through the upload-wait-download cycle repeatedly.

### Features
- **Multi-file drop zone**: Accept up to 5 images simultaneously.
- **Job queue UI**: A list showing each image's processing status (`queued → processing → done`).
- **Bulk download**: A "Download All as ZIP" button powered by the `JSZip` library on the frontend.

### Implementation Plan

#### Backend
- The `/api/enhance` endpoint is already designed for one file. For batch, create a new `POST /api/enhance/batch` that accepts `files: list[UploadFile]`.
- Process each file sequentially (respecting the existing `inference_semaphore`) and return an array of job responses.

#### Frontend
- Refactor `DropZone` to accept `multiple` prop.
- New `<BatchQueue />` component renders the queue list with individual progress per file.

---

## Feature Priority Matrix

| Milestone | Feature | Priority | Backend Work | Frontend Work | Estimated Effort |
|-----------|---------|----------|-------------|--------------|-----------------|
| 4.1 | Delete history jobs | 🔴 High | 1 endpoint | 1 component | ~2 hours |
| 4.2 | Preview before enhance | 🔴 High | None | Dashboard refactor | ~2 hours |
| 4.3 | Scale factor selection | 🟡 Medium | Model registry update | Toggle UI | ~4 hours |
| 4.4 | History comparison modal | 🟡 Medium | 1 new route + schema | Modal + ImageCompare | ~4 hours |
| 4.5 | Stacked toasts + loading toast | 🟡 Medium | None | Toast refactor | ~2 hours |
| 4.6 | Light/Dark theme toggle | 🟢 Low | None | ThemeContext + CSS vars | ~2 hours |
| 4.7 | Batch processing | 🟢 Low | New batch endpoint | BatchQueue component | ~8 hours |

---

## Open Questions

> [!IMPORTANT]
> Before implementation begins, please confirm the following:

1. **Scale factor**: Should 8× upscaling be included? It requires separate `x8` model weights (~80MB extra) and can be very slow on CPU.
2. **Batch limit**: For batch processing, how many images max per submission? (Suggested: 5)
3. **Storage**: Original input images are currently stored in `backend/uploads/`. Is this acceptable long-term, or should we plan for cloud storage (Firebase Storage / S3) migration now?
4. **Which milestone(s) should be implemented first?** The recommendation is to start with **4.1** and **4.2** as they deliver immediate UX improvements with minimal risk.
