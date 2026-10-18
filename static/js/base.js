// Base functionality for all pages
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    const navbar = document.querySelector('.navbar');
    let overlay = null;
    let lastFocusedElement = null;
    
    // Scroll-to-hide functionality for mobile navbar
    let lastScrollTop = 0;
    let scrollTimeout;
    const scrollThreshold = 5; // Minimum scroll amount to trigger hide/show
    
    // Handle scroll events for navbar hide/show
    function handleScroll() {
        if (!navbar || window.innerWidth > 768) return;
        
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Clear any existing timeout
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        
        // Debounce scroll events
        scrollTimeout = setTimeout(() => {
            if (scrollTop > lastScrollTop + scrollThreshold) {
                // Scrolling down - hide navbar
                if (!navbar.classList.contains('navbar-hidden')) {
                    navbar.classList.add('navbar-hidden');
                    document.body.classList.add('navbar-hidden');
                }
            } else if (scrollTop < lastScrollTop - scrollThreshold) {
                // Scrolling up - show navbar
                if (navbar.classList.contains('navbar-hidden')) {
                    navbar.classList.remove('navbar-hidden');
                    document.body.classList.remove('navbar-hidden');
                }
            }
            lastScrollTop = scrollTop;
        }, 10);
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Reset navbar visibility when window is resized above mobile breakpoint
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && navbar) {
            navbar.classList.remove('navbar-hidden');
            document.body.classList.remove('navbar-hidden');
        }
    });

    // Accessibility: Add ARIA attributes
    if (mobileMenuBtn) {
        mobileMenuBtn.setAttribute('aria-label', 'Open navigation menu');
        mobileMenuBtn.setAttribute('aria-controls', 'navLinks');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
    }
    if (navLinks) {
        // Only hide the drawer from screen readers while it is actually
        // closed on mobile — on desktop the menu is always visible.
        if (window.innerWidth <= 768) {
            navLinks.setAttribute('aria-hidden', 'true');
        } else {
            navLinks.removeAttribute('aria-hidden');
        }
    }

    // Create overlay element
    function createOverlay() {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'nav-overlay';
            overlay.addEventListener('click', closeMobileMenu);
            // Always append as last child for z-index
            document.body.appendChild(overlay);
        }
    }

    // Focus trap for nav menu
    function trapFocus(e) {
        if (!navLinks.classList.contains('active')) return;
        const focusableEls = navLinks.querySelectorAll('a, button, [tabindex]:not([tabindex="-1"])');
        const firstEl = focusableEls[0];
        const lastEl = focusableEls[focusableEls.length - 1];
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                if (document.activeElement === firstEl) {
                    e.preventDefault();
                    lastEl.focus();
                }
            } else {
                if (document.activeElement === lastEl) {
                    e.preventDefault();
                    firstEl.focus();
                }
            }
        }
    }

    // Open mobile menu
    function openMobileMenu() {
        createOverlay();
        mobileMenuBtn.classList.add('active');
        navLinks.classList.add('active');
        navbar.classList.add('menu-open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.body.classList.add('menu-open');
        // Accessibility
        mobileMenuBtn.setAttribute('aria-expanded', 'true');
        navLinks.setAttribute('aria-hidden', 'false');
        // Save last focused element
        lastFocusedElement = document.activeElement;
        // Focus first nav link
        const firstLink = navLinks.querySelector('a, button');
        if (firstLink) firstLink.focus();
        // Trap focus
        document.addEventListener('keydown', trapFocus);
    }

    // Close mobile menu
    function closeMobileMenu() {
        mobileMenuBtn.classList.remove('active');
        navLinks.classList.remove('active');
        navbar.classList.remove('menu-open');
        if (overlay) {
            overlay.classList.remove('active');
        }
        document.body.style.overflow = '';
        document.body.classList.remove('menu-open');
        // Accessibility
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        navLinks.setAttribute('aria-hidden', 'true');
        // Restore focus
        if (lastFocusedElement) lastFocusedElement.focus();
        document.removeEventListener('keydown', trapFocus);
    }

    // Toggle mobile menu (guarded against touchend + click double firing)
    function toggleMobileMenu() {
        if (navLinks.classList.contains('active')) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    }

    let lastToggleTime = 0;
    function toggleMobileMenuGuarded() {
        const now = Date.now();
        if (now - lastToggleTime < 500) return;
        lastToggleTime = now;
        toggleMobileMenu();
    }

    // Initialize mobile menu if elements exist
    if (mobileMenuBtn && navLinks) {
        // Mobile menu button click handler
        mobileMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMobileMenuGuarded();
        });
        // Touch support for mobile
        mobileMenuBtn.addEventListener('touchend', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMobileMenuGuarded();
        });
        // Close menu when clicking on a navigation link
        const navLinkElements = navLinks.querySelectorAll('.nav-link');
        navLinkElements.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = link.getAttribute('href');
                if (href && (href.startsWith('#') || href === '#')) {
                    e.preventDefault();
                }
                closeMobileMenu();
                if (href && href !== '#') {
                    setTimeout(() => {
                        window.location.href = href;
                    }, 200);
                }
            });
            // Touch support for nav links
            link.addEventListener('touchend', function(e) {
                closeMobileMenu();
            });
        });
        // Close menu on escape key press
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && navLinks.classList.contains('active')) {
                closeMobileMenu();
            }
        });
        // Handle window resize - close menu if switching to desktop
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768 && navLinks.classList.contains('active')) {
                closeMobileMenu();
            }
            if (navLinks) {
                if (window.innerWidth > 768) {
                    navLinks.removeAttribute('aria-hidden');
                } else if (!navLinks.classList.contains('active')) {
                    navLinks.setAttribute('aria-hidden', 'true');
                }
            }
        });
    } else {
        console.warn('Mobile menu elements not found');
    }

    // Flash messages: dismiss button + auto-hide after 6 seconds
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

    // Highlight the nav link of the current page
    (function highlightCurrentNav() {
        const path = window.location.pathname;
        if (!navLinks) return;
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (!href || href === '#' || href.startsWith('http')) return;
            // Exact match, or section match (e.g. /edit-user/5/ under /manage-users/)
            if (path === href || (href !== '/' && path.startsWith(href))) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }
        });
    })();
});
