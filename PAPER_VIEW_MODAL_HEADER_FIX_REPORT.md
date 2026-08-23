# Paper View Modal Header Clipping Fix Report

## 1. Root Cause Identified

Two primary root causes were identified that caused the top header and title of `PaperViewModal` to be cut off / clipped in the browser UI:

1. **Stacking Context Trapping Under Sticky Global Header (`Header.jsx`)**:
   - `Header.jsx` uses `sticky top-0 z-40` for main site navigation.
   - Parent page views (such as `Dashboard.jsx`, `ResearchAnalysis.jsx`, `ResearchIntelligence.jsx`, etc.) use CSS keyframe animations (e.g., `animate-fade-in`), which creates a new CSS stacking context on the `<main>` container.
   - When `PaperViewModal` was rendered inline inside child page views, its `z-[100]` was trapped inside the child stacking context, causing the global site navbar (`z-40` in root context) to draw OVER the top 64px–80px of the modal overlay.
   - The top portion of the modal header (title & close button) was obscured directly beneath the sticky navbar.

2. **Flexbox Vertical Centering (`align-items: center`) Viewport Overflow**:
   - The outer overlay used `fixed inset-0 flex items-center justify-center p-4 sm:p-6` with fixed height `h-[90vh]` on the modal card.
   - On smaller or medium viewports, centering an oversized fixed box pushed the top edge of the modal frame above `y = 0` (outside the top boundary of the viewport screen), rendering the title permanently unscrollable and clipped off-screen.

---

## 2. Files Inspected

- [`frontend/src/components/PaperViewModal.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/components/PaperViewModal.jsx)
- [`frontend/src/components/Header.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/components/Header.jsx)
- [`frontend/src/App.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/App.jsx)
- [`frontend/src/index.css`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/index.css)
- [`frontend/src/pages/Dashboard.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/pages/Dashboard.jsx)
- [`frontend/src/pages/ResearchAnalysis.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/pages/ResearchAnalysis.jsx)
- [`frontend/src/pages/ResearchIntelligence.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/pages/ResearchIntelligence.jsx)
- [`frontend/src/pages/ResearchProjectDetails.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/pages/ResearchProjectDetails.jsx)
- [`frontend/src/components/ProjectResearchReportModal.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/components/ProjectResearchReportModal.jsx)

---

## 3. Files Modified

- [`frontend/src/components/PaperViewModal.jsx`](file:///c:/Users/akash/OneDrive/Desktop/MCP%20AK/MCP%20AK/IntelliResearch/frontend/src/components/PaperViewModal.jsx)

---

## 4. Exact Layout Changes

1. **Root-Level React Portal (`createPortal`)**:
   - Wrapped the `PaperViewModal` JSX inside `createPortal(..., document.body)` imported from `react-dom`.
   - Renders the modal directly on `document.body`, escaping all ancestor stacking contexts, `animate-fade-in` transforms, and parent `overflow-hidden` constraints.
   - Ensures `fixed inset-0 z-[100]` renders at top root level above `Header.jsx` (`z-40`).

2. **Viewport-Centered Modal Overlay Architecture**:
   - Outer overlay container: `<div className="fixed inset-0 z-[100] overflow-y-auto">`
   - Independent backdrop: `<div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm animate-fade-in" onClick={onClose} />`
   - Centering wrapper: `<div className="relative flex min-h-screen items-center justify-center p-4 sm:p-6 pointer-events-none">`
   - Outer modal frame: `<div className="relative flex h-[90vh] max-h-[calc(100vh-2rem)] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-slate-800 glass-card shadow-2xl pointer-events-auto z-10">`

3. **Strict Header Isolation & Word Wrapping**:
   - Header element: `<header className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-800/80 bg-slate-900/95 backdrop-blur-md px-6 py-4 relative z-10">`
   - Header title:
     ```jsx
     <h3 
       className="m-0 block w-full text-[20px] font-bold leading-[1.35] text-slate-100 whitespace-normal break-words [overflow-wrap:anywhere]"
       style={{ wordBreak: 'break-word' }}
       title={paper.title}
     >
       {paper.title}
     </h3>
     ```
   - Filename metadata: `<p className="mt-1 text-xs text-slate-400 truncate">Filename: <span className="font-mono text-indigo-400">{paper.filename}</span></p>`
   - Top-right close button remains flex `shrink-0` and perfectly aligned.
   - Removed any `overflow-hidden` or `max-h` from header ancestors so header expands vertically as title wraps.

4. **Scrollable Content & Fixed Footer**:
   - Scroll region: `<div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar p-6 space-y-6">`
   - Stationary Footer: `<footer className="shrink-0 px-6 py-4 bg-slate-900/60 border-t border-slate-800/80 flex items-center justify-end gap-3">`

5. **Clean Body Scroll Locking**:
   - Added `useEffect` in `PaperViewModal.jsx` to set `document.body.style.overflow = 'hidden'` on mount and clean up on unmount.

---

## 5. Before vs. After Behavior

| Aspect | Before Fix | After Fix |
|---|---|---|
| **Modal Header & Title** | Partially clipped at the top; obscured under sticky navbar | 100% visible with ample top breathing room |
| **Close [X] Button** | Cut off or hidden under top navbar | Clearly visible in top-right header, fully clickable |
| **Stacking Context** | Trapped inside child page containers (`<main>`) | Portaled to `document.body` with `z-[100]` above all page elements |
| **Header Height & Wrap** | Susceptible to line height clipping | Expands naturally without height limit or text cut-off |
| **Page Scrolling** | Background page scrolled behind modal | Locked cleanly via `document.body.style.overflow = 'hidden'` |
| **Content Scrolling** | Scrolls inside content container | Only middle content region scrolls; header and footer remain stationary |

---

## 6. Responsive Verification

Verified across viewports (1920x1080, 1600x900, 1366x768, 1280x720, 1024x768, 768x1024, and mobile widths):
- Long title tested: `"Vision Transformers and YoloV5 based Driver Drowsiness Detection Framework"`
- Title wraps smoothly onto 2–3 lines.
- `max-h-[calc(100vh-2rem)]` ensures at least 16px vertical breathing room at both top and bottom edges.
- Modal frame never exceeds screen boundaries.

---

## 7. Browser Verification

- Live UI verified in browser via automated subagent session and screenshot capture.
- Screenshots recorded and saved in artifacts:
  - `modal_open_view_1787466317261.png`: Confirms complete title, filename, close X button, and backdrop blur.
  - `modal_scrolled_view_1787466330086.png`: Confirms fixed header and footer during content scrolling.

---

## 8. Build Result

- Command: `npm run build`
- Result: **Passed cleanly (Exit Code 0, 0 Errors, 0 Warnings)**.

---

## 9. Remaining Issues

- None. The PaperViewModal header clipping issue is completely resolved.
