# design-system.md — UI/UX Components, Tokens, Interaction Rules (Priority 4)

**Honesty note**: there is no formal design system in this codebase today. `dashboard.html`, `projects.html`, `brand.html`, `tools.html`, `phase_dashboard.html` are hand-written static HTML/JS with no framework, no component library, and no shared token file. This document does not invent a mature system that doesn't exist — it captures the conventions the existing pages already follow (so new work stays consistent) and sets minimal rules for what comes next.

## Current state

- **No framework**: plain HTML + inline/embedded JS + CSS per page. No React/Vue/build step.
- **No shared token file**: colors/spacing are ad hoc per page today, except where a brand's own `brand_profile.json` (colors, typography) is read and applied to generated cards/video — that brand-level theming is real and must be preserved.
- **One reusable interaction pattern already established** (per recent commit history): the **per-tab command bar** on `phase_dashboard.html` — step number, dependencies, outputs, and run/copy buttons rendered consistently per tab. Any new phase-dashboard tab must follow this same command-bar shape rather than inventing a new per-tab layout.
- **Existing page inventory** (do not create a 6th top-level static page without checking whether one of these already covers the need):
  | Page | Purpose |
  |---|---|
  | `dashboard.html` | Main entry point |
  | `projects.html` | Brand/project list |
  | `brand.html` | Brand profile view/edit |
  | `tools.html` | Tool status/utilities |
  | `phase_dashboard.html` | Per-phase run view — command bar, tabs, version history, platform-output preview |

## Rules for new UI work

1. **Reuse the phase_dashboard command-bar pattern** for any new per-step or per-tab control surface — do not design a new interaction pattern for something the command bar already generalizes over (step number, deps, outputs, run, copy).
2. **Brand colors/typography always come from `brand_profile.json`** at render/display time — never hardcode a specific brand's colors into a shared page or component.
3. **No new framework dependency** without checking `architecture.md`/`coding-rules.md` first — introducing React/Vue for one page while the rest stays plain HTML creates exactly the kind of inconsistency this document exists to prevent. If a framework migration is ever warranted, it is a `roadmap.md` phase of its own, not an incidental choice inside an unrelated task.
4. **Version/history displays** (`.versions/{step}/vN/`) must always show version provenance (which tier/provider produced it, when) — this already exists in spirit via `.versions/`; new displays of generated content should not regress this.
5. **Platform Output Preview blocks** (all 7 platform blocks expanded inline, per recent work) is the established pattern for showing multi-platform output — extend this pattern for new platforms (e.g. Facebook, flagged as missing in `product.md`) rather than inventing a different preview shape per platform.

## What's deliberately NOT specified yet

- A formal color/spacing token scale for the dashboard's own UI (as opposed to brand-generated content) — not needed until the dashboard UI itself becomes a priority investment (see `ARCHITECTURE_AUDIT.md` P15 / Phase 9 note: dashboard polish is explicitly de-prioritized while repo-root scratch clutter and core architecture debt remain unresolved).
- Component library choice for a future outcome-oriented UI (`roadmap.md` Phase 7's `ProjectOrchestrator` intake flow) — to be decided when that phase is actually reached, not speculatively now.
