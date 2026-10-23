# Mobile navigation

There is **one** mobile navigation implementation in this project. It replaced an
older top-navbar hamburger that used to ship alongside it; keeping both was what
made the menu appear broken (two elements fighting over `position: fixed`,
`z-index` and body padding).

## The implementation

| Piece | Where it lives |
| --- | --- |
| Off-canvas drawer | `.sidebar` in `static/css/ui.css` |
| Menu button (hamburger) | `#sidebarToggle` inside `.topbar`, `stockT/templates/base.html` |
| Page scrim | `.sidebar-scrim` (dismissed via `data-sidebar-close`) |
| Close button inside drawer | `.sidebar-close` (also `data-sidebar-close`) |
| Behaviour | `static/js/base.js` → `setSidebar(open)` |

Nothing else owns navigation. `static/css/navbar.css` is an intentionally empty
placeholder kept so the shared stylesheet cascade stays stable.

### Behaviour

- **≥ 921px** – the sidebar is always visible next to the content; the menu
  button and the close button are hidden.
- **≤ 920px** – the sidebar becomes an off-canvas drawer (`translateX(-100%)`)
  and the hamburger in the topbar opens it.
- Opening the drawer: sets `.sidebar.is-open` on the sidebar, un-hides the
  scrim, sets `body.drawer-open` (scroll lock), moves focus into the drawer and
  traps Tab inside it.
- Closing: the close button, the scrim, `Escape`, following a link inside the
  drawer, or clicking the feedback button. Focus returns to `#sidebarToggle`.
- State is exposed with `aria-expanded` on the button and `aria-hidden` /
  `inert` on the drawer, so the hidden drawer never enters the tab order.

### Layering (do not exceed these casually)

```
2000  .skip-link (when focused)
  80  account dropdown (.nav-menu)
  70  floating feedback widget
  60  .sidebar (drawer)
  55  .sidebar-scrim
  40  .topbar (sticky)
```

The drawer must stay **below** the floating feedback widget and above the
scrim/topbar. The old design documented 10000+ values; that hierarchy is gone.

## Verifying

1. Open any authenticated page and resize to ≤ 920px.
2. The topbar shows exactly **one** hamburger (`#sidebarToggle`).
3. Tap it: the drawer slides in, the page dims, Tab stays inside the drawer.
4. `Escape` closes it and focus returns to the hamburger.

Automated coverage lives in `tests/unit/test_navigation.py`
(`TestNavMarkup`, `TestSingleNavigationImplementation`).

## Do not reintroduce

These were removed on purpose — adding any of them back recreates the clash:

- `#mobileMenuBtn` / `.mobile-menu-btn` / `.hamburger-line`
- `#navLinks` / `.nav-links.active`
- `.navbar` / `.nav-link` / `.nav-brand` layout rules
- `body.navbar-hidden`
- `has-mobile-tabbar` (there is no bottom tab bar)
- `static/css/style.css` (legacy `@import` bundle with the old hamburger rules)
   and `static/css/white-theme.css` (old `.navbar` colour overrides)

New navigation rules go in `static/css/ui.css`; new behaviour goes in
`static/js/base.js`.
