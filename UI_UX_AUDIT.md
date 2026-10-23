# UI / UX audit — October 2026

A pass over every screen in the app, focused on pages that still looked unfinished.
The work is grouped into a shared design system plus page-level fixes.

## What was wrong

| Page | Problem found |
| --- | --- |
| All pages | No shared button styles. `.btn`, `.btn-primary`, `.btn-danger`, `.btn-sm` … were only defined inside `stock-usage-tracking.css` and scoped to `.usage-page`, so almost every button rendered as a bare link/button. |
| All pages | `.data-table` (used by ~11 pages) had **no CSS at all**. Tables were unstyled, full-bleed and unusable on mobile. |
| All pages | `.text-muted`, `.text-success`, `.text-danger`, `.empty-state`, `.inline-form`, `.field-errors` and `.messages-container` were undefined or only defined in page-specific files. Flash messages were unstyled on every page except Profile. |
| All pages | Global `style.css` `@import`ed ten page-specific stylesheets, so page styles leaked everywhere (e.g. the Add Stock page painted a full-screen purple gradient on any page that used the same container class). |
| Analytics / devices / milestones | Plain tables plus six unstyled "stat cards"; chart canvas had no height, so the chart either collapsed or overflowed. |
| Notifications | Cards, icons and the “Mark as read” action were unstyled; no unread/read distinction. |
| My feedback / manage feedback | Unstyled table and filter buttons; no empty state; respond form was always expanded and cramped. |
| Stock usage + history | Both pages linked a stylesheet written for a `.usage-page` layout that the templates never used, so nearly the whole page was unstyled. |
| Stock distribution | Long single-column form, tables with no borders, submit button lost at the bottom. |
| Add stock | Card grid, toolbars and modals referenced classes (`kit-type-*`, `modal*`, `kits-toolbar`) that no stylesheet defined. Edit/delete modals also relied on jQuery + Bootstrap JS that is not loaded, so they never opened. |
| Inventory calculator | Linked a 1,100-line stylesheet for a completely different calculator UI; none of the visible markup matched it. |
| Footer contact add/edit/delete, create admin, password reset, submit feedback | Reused the login screen container (`min-height:100vh` + purple gradient + 400 px card), so admin forms looked like a login page. |
| Profile | New markup used `.profile-card/.profile-avatar/.profile-qr`, which did not exist; QR card and details list were unstyled. |
| Logout confirm | Template classes did not exist in `logout-confirm.css`; page rendered as raw markup. |
| 404 / 500 / offline | `.error-page` was never defined; screens were bare text. |
| Footer | Markup used `.footer/.footer-content/.footer-section`, while `footer.css` styles `.app-footer/.footer-container` — the footer had no styling at all. |
| Navbar | Up to 12 links with 40 px gaps overflowed the bar on laptop widths and were clipped. |
| Feedback widget | Tabs used `.floating-tabs`, CSS defined `.floating-panel-tabs`; panel content wrapper missing. |
| Dashboard pagination | Pagination links stopped working after the first AJAX page change (inline script in the replaced partial never re-runs). |

## What was built

* **`static/css/components.css`** — a shared UI kit: design tokens, page header, cards/panels, buttons (all variants + sizes), form controls, alerts, badges/status chips, data tables + responsive wrappers, empty states, modals, pagination, filter tabs, footer, navbar density and utilities.
* **`static/css/style.css`** — reduced to true globals (reset, grid helpers, focus ring). Page-specific imports removed so styles stay scoped.
* Page stylesheets: `analytics.css`, `feedback.css`, `distribution.css`, `stock-usage.css`, `dashboard-page.css`, `profile-page.css`, `add-items-page.css`, `calculator-page.css`.
* Templates reworked to use the shared classes, with consistent page headers, descriptions, back links, empty states and mobile behaviour:
  dashboard, add stock, stock usage + history, distribution, most received kits, calculator,
  analytics, devices, milestones, notifications, my feedback, manage feedback, manage users,
  manage admins, footer contacts (list/add/edit/delete), profile, edit user, create admin,
  password reset, submit feedback, logout confirm, 404/500/offline.
* `base.html`: stylesheet order, skip link, `aria-current` nav highlighting, accessible mobile menu state,
  footer markup aligned with its CSS, floating feedback panel structure fixed, flash-message icons.
* `add_items.js`: small plain-DOM modal helper so the edit/delete dialogs actually open (Escape,
  backdrop and × close), plus unit hint element used by the existing scripting.
* `dashboard.js`: delegated pagination handler that survives AJAX table refreshes.

## Design conventions now in place

* Indigo (`#5b6ee1 → #7c4dff`) gradient headers and primary actions, matching the navbar.
* White panels on `#f4f6fb`, 18 px radius, soft shadows, consistent 20 px gutters.
* Tables always wrapped in `.table-responsive`; horizontal scroll on small screens.
* Status chips share one palette: pending (amber), approved/reviewed (blue), completed/resolved (green), rejected/dismissed (red).
* Every collection has an empty state with icon, explanation and (where useful) a call to action.
* Touch targets ≥ 40 px; forms use 44 px controls and full-width actions on phones.

## Known follow-ups (not changed here)

* `add_items.js` still contains legacy jQuery/Bootstrap-flavoured code paths (`viewKit` modal content
  uses Bootstrap grid classes). The modal shim makes them usable, but a rewrite would be cleaner.
* Unused legacy stylesheets remain in `static/css/` (`add-items.css`, `inventory-calculator.css`,
  `calculator.css`, `stock-usage-tracking.css`, `edit-user.css`, `most-received-kits.css`,
  `logout-confirm.css`, `danger-confirm.css`, `manage-users.css`, `white-theme.css`, `developer.css`).
  They are no longer linked; delete them once you are happy with the new pages.
* `logs/` must exist for `settings.py` logging to start (pre-existing issue, worked around locally).
* `STATICFILES_DIRS` points at a non-existent `stockT/static` directory (check warning is harmless).
