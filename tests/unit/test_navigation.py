"""Navigation (blaqVibe pattern) and shared UI markup."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestNavMarkup:
    def test_mobile_sidebar_has_working_open_and_close_controls(self, as_member):
        content = as_member.get('/').content.decode()
        assert 'id="sidebarToggle"' in content
        assert 'aria-label="Open navigation"' in content
        assert 'aria-controls="sidebar"' in content
        assert 'data-sidebar-close' in content
        assert 'id="sidebar"' in content

    def test_account_menu_present_for_authenticated(self, as_member):
        content = as_member.get('/').content.decode()
        assert 'navUserBtn' in content
        assert 'navMenu' in content
        assert '<body class="app-body">' in content
        assert 'Change Password' in content
        assert 'Logout' in content

    def test_mobile_primary_navigation_uses_account_menu_for_profile(self, as_member):
        content = as_member.get('/').content.decode()
        for label in [
            'Dashboard', 'Add Stock', 'Track Usage', 'Distribute', 'Calculator',
        ]:
            assert label in content
        assert content.count('<span>Dashboard</span>') == 1
        assert content.count('<span>Track Usage</span>') == 1
        assert '<span>Profile</span>' not in content
        assert 'aria-hidden="true">More</span>' in content
        assert 'href="/profile/"' in content
        assert 'href="/profile/" aria-current="page"' in as_member.get('/profile/').content.decode()

    def test_theme_toggle_is_available_to_all_users(self, client, as_member):
        for response in (client.get('/'), as_member.get('/')):
            content = response.content.decode()
            assert 'data-theme-toggle' in content
            assert 'Switch to dark mode' in content
            assert '/static/js/base.js' in content

    def test_manager_menu_items_gated(self, as_member, as_manager):
        member_content = as_member.get('/').content.decode()
        manager_content = as_manager.get('/').content.decode()
        for label in ['Manage Users', 'Analytics', 'Kit Types', 'Password Resets']:
            assert label not in member_content
            assert label in manager_content

    def test_anon_nav_has_login_not_account(self, client):
        content = client.get('/').content.decode()
        assert 'navUserBtn' not in content
        assert 'app-body--guest' in content
        assert 'Login' in content

    def test_aria_current_marks_dashboard(self, as_member):
        content = as_member.get('/').content.decode()
        assert 'href="/" aria-current="page"' in content

    def test_skip_link_present(self, client):
        assert 'skip-link' in client.get('/').content.decode()

    def test_ui_css_loaded(self, client):
        assert 'ui.css' in client.get('/').content.decode()

    def test_shared_styles_load_in_cascade_order(self, client):
        content = client.get('/').content.decode()
        styles = ['base.css', 'navbar.css', 'footer.css', 'ui.css']
        positions = [content.index(name) for name in styles]
        assert positions == sorted(positions)
        # Legacy sheets (old hamburger/navbar layer) must never be linked again.
        for legacy in ('style.css', 'white-theme.css'):
            assert legacy not in content

    def test_quoted_service_worker_url_tag_renders(self, client):
        from django.urls import reverse

        content = client.get('/').content.decode()
        assert f"navigator.serviceWorker.register('{reverse('service_worker')}')" in content


class TestFlashMessages:
    def test_alert_renders_with_close_button(self, as_member):
        """Submit nothing so the view warns; the alert must be dismissible."""
        as_member.post('/add-items/', {})
        content = as_member.get('/add-items/').content.decode()
        assert 'alert' in content
        assert 'alert-close' in content

    def test_messages_container_has_aria(self, as_member):
        as_member.post('/add-items/', {})
        assert 'aria-live="polite"' in as_member.get('/add-items/').content.decode()


class TestRegistrationContext:
    def test_register_link_always_in_nav(self, client, register_workspace):
        assert 'Register' in client.get('/').content.decode()
        register_workspace()
        client.logout()
        assert 'Register' in client.get('/').content.decode()


class TestSingleNavigationImplementation:
    """There must be exactly one mobile navigation system.

    The project once shipped the legacy navbar hamburger and the newer sidebar
    drawer at the same time; the two fought over positioning and z-index and
    left the menu unusable. These tests keep the legacy layer from coming back.
    """

    LEGACY_MARKUP = (
        'mobileMenuBtn',
        'mobile-menu-btn',
        'hamburger-line',
        'navLinks',
        'nav-links',
        'class="navbar"',
        'navbar-hidden',
        'has-mobile-tabbar',
    )

    def test_pages_render_no_legacy_hamburger_markup(self, as_member, as_manager, client):
        for response in (client.get('/'), as_member.get('/'), as_manager.get('/')):
            content = response.content.decode()
            for marker in self.LEGACY_MARKUP:
                assert marker not in content, f'legacy navigation markup: {marker}'

    def test_exactly_one_menu_toggle_is_rendered(self, as_member):
        content = as_member.get('/').content.decode()
        assert content.count('id="sidebarToggle"') == 1
        # One hamburger icon, one close affordance inside the drawer.
        assert content.count('href="#i-menu"') == 1

    def test_legacy_stylesheets_are_gone(self):
        from pathlib import Path

        static_css = Path('static/css')
        assert not (static_css / 'style.css').exists()
        assert not (static_css / 'white-theme.css').exists()
        navbar_css = (static_css / 'navbar.css').read_text()
        # Only a comment may mention them; no legacy selector may survive.
        for selector in ('.mobile-menu-btn {', '.hamburger-line {', '.nav-links {', '.navbar {'):
            assert selector not in navbar_css

    def test_service_worker_precaches_only_existing_assets(self):
        """A stale precache entry aborts the SW install, so the PWA stops updating."""
        import re
        from pathlib import Path

        sw = Path('static/sw.js').read_text()
        urls = re.findall(r"'(/static/[^']+)'", sw)
        assert urls, 'service worker precache list vanished'
        assert '/static/css/ui.css' in urls, 'the live design system is not precached'
        for url in urls:
            assert (Path('.') / url.lstrip('/')).exists(), f'precache URL missing on disk: {url}'
        for legacy in ('/static/css/style.css', '/static/css/white-theme.css'):
            assert legacy not in urls
