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
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-moon', !isDark);
                icon.classList.toggle('fa-sun', isDark);
            }
        }
        if (themeColor) {
            themeColor.setAttribute('content', isDark ? '#1d1918' : '#2E6347');
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
    // Account menu (blaqVibe pattern): toggle on the avatar button, close
    // on any outside click. Escape dismisses and hands focus back —
    // click-outside only covers pointer users.
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
            if (e.key === 'Escape') closeNavMenu(true);
        });

        // Close after choosing a destination (mobile especially)
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => closeNavMenu(false));
        });

        // Keep the menu anchored when the pill row scrolls on mobile
        window.addEventListener('resize', () => closeNavMenu(false));
    }

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
