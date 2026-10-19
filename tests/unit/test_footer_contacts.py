"""Footer contacts: superuser CRUD (the public footer is data, not hardcoded)."""
import pytest
from django.contrib.auth import get_user_model

from stockT.models import ContactInfo

User = get_user_model()

pytestmark = pytest.mark.django_db


def payload(**overrides):
    data = {
        'contact_type': 'email',
        'label': 'Support',
        'value': 'support@example.com',
        'is_active': 'on',
        'order': '1',
    }
    data.update(overrides)
    return data


class TestAccess:
    def test_superuser_allowed(self, as_owner):
        assert as_owner.get('/footer/contacts/').status_code == 200

    def test_manager_blocked(self, as_manager):
        assert as_manager.get('/footer/contacts/').status_code == 302


class TestCrud:
    def test_add_contact(self, as_owner):
        response = as_owner.post('/footer/contacts/add/', payload())
        assert response.status_code == 302
        assert ContactInfo.objects.filter(value='support@example.com').exists()

    def test_edit_contact(self, as_owner):
        contact = ContactInfo.objects.create(
            contact_type='email', label='Old', value='old@example.com', order=1,
        )
        response = as_owner.post(f'/footer/contacts/edit/{contact.id}/', payload(label='New'))
        assert response.status_code == 302
        contact.refresh_from_db()
        assert contact.label == 'New'

    def test_toggle_contact(self, as_owner):
        contact = ContactInfo.objects.create(
            contact_type='email', label='L', value='v@example.com', order=1, is_active=True,
        )
        as_owner.post(f'/footer/contacts/toggle/{contact.id}/')
        contact.refresh_from_db()
        assert contact.is_active is False

    def test_delete_contact(self, as_owner):
        contact = ContactInfo.objects.create(
            contact_type='email', label='L', value='v@example.com', order=1,
        )
        response = as_owner.post(f'/footer/contacts/delete/{contact.id}/')
        assert response.status_code == 302
        assert not ContactInfo.objects.filter(id=contact.id).exists()

    def test_contact_visible_on_public_footer(self, client):
        ContactInfo.objects.create(
            contact_type='phone', label='Call', value='0710000000', order=1, is_active=True,
        )
        response = client.get('/')
        assert '0710000000' in response.content.decode()
