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
    // narrow screens. The scrim and Escape both dismiss it.
    // -----------------------------------------------------------------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const scrim = document.querySelector('.sidebar-scrim');
    const sidebarCloseButtons = document.querySelectorAll('[data-sidebar-close]');
    let sidebarReturnFocus = null;

    function setSidebar(open) {
        if (!sidebar) return;
        sidebar.classList.toggle('is-open', open);
        const isMobile = window.matchMedia('(max-width: 920px)').matches;
        const isClosedOnMobile = isMobile && !open;
        sidebar.inert = isClosedOnMobile;
        sidebar.setAttribute('aria-hidden', isClosedOnMobile ? 'true' : 'false');
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            sidebarToggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
            const icon = sidebarToggle.querySelector('use');
            if (icon) icon.setAttribute('href', open ? '#i-close' : '#i-menu');
            if (open) {
                sidebarReturnFocus = document.activeElement;
                const firstLink = sidebar.querySelector('.sidebar-nav a');
                if (firstLink) firstLink.focus();
            } else if (sidebarReturnFocus && sidebar.contains(document.activeElement)) {
                sidebarToggle.focus();
                sidebarReturnFocus = null;
            }
        }
        if (scrim) scrim.hidden = !open;
        document.body.style.overflow = open ? 'hidden' : '';
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
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && sidebar.classList.contains('is-open')) {
                setSidebar(false);
            }
        });
        window.addEventListener('resize', () => {
            setSidebar(sidebar.classList.contains('is-open') && window.innerWidth <= 920);
        });
        setSidebar(sidebar.classList.contains('is-open'));
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
