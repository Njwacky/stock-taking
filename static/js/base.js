// Base functionality for all pages
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('[data-theme-toggle]');
    const themeColor = document.querySelector('meta[name="theme-color"]');

    function setTheme(theme, persist) {
        const isDark = theme === 'dark';
        document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
        if (themeToggle) {
            themeToggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
            themeToggle.setAttribute(
                'aria-label',
                isDark ? 'Switch to light mode' : 'Switch to dark mode'
            );
        }
        if (themeColor) {
            themeColor.setAttribute('content', isDark ? '#0f1512' : '#f5f6f4');
        }
        if (persist) {
            try {
                localStorage.setItem('stock-theme', isDark ? 'dark' : 'light');
            } catch (error) {
                console.warn('Could not save the theme preference:', error);
            }
        }
    }

    setTheme(document.documentElement.dataset.theme, false);
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const nextTheme = document.documentElement.dataset.theme === 'dark'
                ? 'light'
                : 'dark';
            setTheme(nextTheme, true);
        });
    }

    // -----------------------------------------------------------------
    // Responsive navigation: the sidebar becomes an off-canvas drawer on
    // narrow screens. While it is open it behaves like a modal sheet: the
    // scrim, Escape and the close button dismiss it, the page behind it is
    // inert, and Tab is trapped inside the drawer.
    // -----------------------------------------------------------------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const scrim = document.querySelector('.sidebar-scrim');
    const sidebarCloseButtons = document.querySelectorAll('[data-sidebar-close]');
    const appMain = document.querySelector('.app-main');
    const drawerQuery = window.matchMedia('(max-width: 920px)');

    function drawerIsActive() {
        return !!sidebar && sidebar.classList.contains('is-open');
    }

    function drawerFocusables() {
        if (!sidebar) return [];
        return Array.from(sidebar.querySelectorAll(
            'a[href], button:not([disabled]), select:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )).filter(element => !element.closest('[hidden]'));
    }

    function setSidebar(open) {
        if (!sidebar) return;
        // Only treat "open" as true on narrow screens: a stale class on a
        // desktop viewport would otherwise show the scrim over the page.
        const shouldOpen = !!open && drawerQuery.matches;
        // Captured before anything turns inert: browsers blur a focused
        // element the moment it becomes inert, which would otherwise drop
        // the caret on <body> and lose the keyboard position.
        const focusWasInside = sidebar.contains(document.activeElement);

        sidebar.classList.toggle('is-open', shouldOpen);

        // Off-canvas on mobile: keep the hidden drawer out of the tab order
        // and the accessibility tree. On desktop the rail is always visible.
        const hideFromA11yTree = drawerQuery.matches && !shouldOpen;
        if (hideFromA11yTree) sidebar.setAttribute('inert', '');
        else sidebar.removeAttribute('inert');
        sidebar.setAttribute('aria-hidden', hideFromA11yTree ? 'true' : 'false');

        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
            sidebarToggle.setAttribute('aria-label', shouldOpen ? 'Close navigation' : 'Open navigation');
            const icon = sidebarToggle.querySelector('use');
            if (icon) icon.setAttribute('href', shouldOpen ? '#i-close' : '#i-menu');
        }
        if (scrim) scrim.hidden = !shouldOpen;

        // While the drawer covers the page, the page must not be reachable
        // by Tab, pointer or screen reader.
        if (appMain) {
            if (shouldOpen) appMain.setAttribute('inert', '');
            else appMain.removeAttribute('inert');
        }

        document.body.classList.toggle('drawer-open', shouldOpen);

        if (shouldOpen) {
            // Start keyboard users on the page they are already on, falling
            // back to the first link, then the first focusable control.
            const firstTarget = sidebar.querySelector('.sidebar-nav [aria-current="page"]')
                || sidebar.querySelector('.sidebar-nav a')
                || drawerFocusables()[0];
            if (firstTarget) firstTarget.focus();
        } else if (focusWasInside && sidebarToggle && drawerQuery.matches) {
            // Hand focus back to the control that opened the drawer. Runs
            // after the inert attributes are cleared, or the focus call
            // would be ignored.
            sidebarToggle.focus();
        }
    }

    if (sidebar) {
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                setSidebar(!sidebar.classList.contains('is-open'));
            });
        }
        sidebarCloseButtons.forEach(closeButton => {
            closeButton.addEventListener('click', function() {
                setSidebar(false);
            });
        });
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => setSidebar(false));
        });
        // The feedback panel is layered above the drawer, so dismiss the
        // drawer first instead of leaving the page scroll-locked behind it.
        const sidebarFeedback = document.getElementById('floatingCommentBtn');
        if (sidebarFeedback) {
            sidebarFeedback.addEventListener('click', () => setSidebar(false));
        }
        document.addEventListener('keydown', function(event) {
            if (!drawerIsActive()) return;
            if (event.key === 'Escape') {
                event.preventDefault();
                setSidebar(false);
                return;
            }
            if (event.key !== 'Tab') return;
            const focusables = drawerFocusables();
            if (!focusables.length) return;
            const first = focusables[0];
            const last = focusables[focusables.length - 1];
            const active = document.activeElement;
            const outsideDrawer = !sidebar.contains(active);
            if (event.shiftKey && (outsideDrawer || active === first)) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && (outsideDrawer || active === last)) {
                event.preventDefault();
                first.focus();
            }
        });
        // Close only when the drawer breakpoint is actually crossed. A plain
        // resize (mobile browser chrome, on-screen keyboard) must not re-run
        // the open state, which used to yank focus to the first link.
        let drawerWasAvailable = drawerQuery.matches;
        window.addEventListener('resize', function() {
            if (drawerQuery.matches === drawerWasAvailable) return;
            drawerWasAvailable = drawerQuery.matches;
            setSidebar(false);
        });
        // A bfcache restore keeps the DOM as it was left, including the open
        // drawer and its scroll lock.
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) setSidebar(false);
        });
        setSidebar(false);
    }

    // -----------------------------------------------------------------
    // Account menu: toggle on the avatar button, close on any outside
    // click. Escape dismisses and hands focus back — click-outside only
    // covers pointer users.
    // -----------------------------------------------------------------
    const navUser = document.getElementById('navUser');
    const navUserBtn = document.getElementById('navUserBtn');
    const navMenu = document.getElementById('navMenu');

    function closeNavMenu(refocus) {
        if (!navMenu || !navMenu.classList.contains('open')) return;
        navMenu.classList.remove('open');
        if (navUserBtn) {
            navUserBtn.setAttribute('aria-expanded', 'false');
            if (refocus) navUserBtn.focus();
        }
    }

    if (navUserBtn && navMenu) {
        navUserBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const open = navMenu.classList.toggle('open');
            navUserBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        });

        document.addEventListener('click', function(e) {
            if (navMenu.classList.contains('open') && !navUser.contains(e.target)) {
                closeNavMenu(false);
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeNavMenu(true);
            }
        });

        // Close after choosing a destination (mobile especially)
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => closeNavMenu(false));
        });

        // Keep the menu anchored when the pill row scrolls on mobile
        window.addEventListener('resize', () => closeNavMenu(false));
    }

    // -----------------------------------------------------------------
    // Double-submit guard: absorbs accidental double taps (especially on
    // mobile) without locking out intentional re-submits on async forms.
    // -----------------------------------------------------------------
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (form.dataset.busy === '1') {
            e.preventDefault();
            e.stopImmediatePropagation();
            return;
        }
        form.dataset.busy = '1';
        setTimeout(function() {
            form.dataset.busy = '';
        }, 1500);
    }, true);

    // -----------------------------------------------------------------
    // Flash messages: dismiss button + auto-hide after 6 seconds
    // -----------------------------------------------------------------
    function dismissAlert(alert) {
        if (!alert || alert.dataset.dismissing === '1') return;
        alert.dataset.dismissing = '1';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        alert.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
        setTimeout(() => {
            if (alert.parentNode) alert.remove();
        }, 360);
    }

    document.querySelectorAll('.alert').forEach(alert => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissAlert(alert));
        }
        if (alert.hasAttribute('data-auto-dismiss')) {
            setTimeout(() => dismissAlert(alert), 6000);
        }
    });
});
