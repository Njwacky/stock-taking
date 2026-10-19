"""Navigation (blaqVibe pattern) and shared UI markup."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestNavMarkup:
    def test_no_hamburger_anywhere(self, as_member):
        content = as_member.get('/').content.decode()
        assert 'mobileMenuBtn' not in content
        assert 'hamburger' not in content

    def test_account_menu_present_for_authenticated(self, as_member):
        content = as_member.get('/').content.decode()
        assert 'navUserBtn' in content
        assert 'navMenu' in content
        assert '<body class="has-mobile-tabbar">' in content
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
        assert 'has-mobile-tabbar' not in content
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
        assert 'style.css' not in content

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
