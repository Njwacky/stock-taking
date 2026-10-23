"""Kits: add/update/delete permissions, dashboard scoping, bulk delete."""
import json

import pytest
from django.contrib.auth import get_user_model

from stockT.models import Kit

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestAddItems:
    def test_add_stock_page_has_searchable_kit_catalog(self, as_member, kit_type):
        content = as_member.get('/add-items/').content.decode()

        assert 'id="kitTypeSearch"' in content
        assert 'id="catalogCount"' in content
        assert 'id="catalogNoResults"' in content
        assert 'id="selectionSummary"' in content
        assert f'id="quantity_{kit_type.id}"' in content
        assert f'for="quantity_{kit_type.id}"' in content
        assert 'Add stock' in content

    def test_user_adds_stock_for_self(self, as_member, member, kit_type):
        response = as_member.post('/add-items/', {
            'user': member.id, f'quantity_{kit_type.id}': '5',
            f'condition_{kit_type.id}': 'new',
        })
        assert response.status_code == 302
        kit = Kit.objects.get(user=member)
        assert kit.quantity == 5
        assert kit.created_by == member

    def test_user_cannot_add_stock_for_others(self, as_member, other_member, kit_type):
        response = as_member.post('/add-items/', {
            'user': other_member.id, f'quantity_{kit_type.id}': '5',
        })
        assert response.status_code == 302
        assert not Kit.objects.filter(user=other_member).exists()

    def test_invalid_quantity_and_condition_are_rejected(self, as_member, member, kit_type):
        response = as_member.post('/add-items/', {
            'user': member.id,
            f'quantity_{kit_type.id}': '3',
            f'condition_{kit_type.id}': 'not-a-condition',
        }, follow=True)
        assert response.status_code == 200
        assert not Kit.objects.filter(user=member).exists()
        assert 'valid condition' in response.content.decode()

        response = as_member.post('/add-items/', {
            'user': member.id,
            f'quantity_{kit_type.id}': '-2',
            f'condition_{kit_type.id}': 'new',
        }, follow=True)
        assert response.status_code == 200
        assert not Kit.objects.filter(user=member).exists()
        assert 'cannot be negative' in response.content.decode()

    def test_manager_adds_stock_for_others(self, as_manager, other_member, kit_type):
        as_manager.post('/add-items/', {
            'user': other_member.id, f'quantity_{kit_type.id}': '7',
        })
        assert Kit.objects.filter(user=other_member, quantity=7).exists()


class TestUpdateKit:
    def test_owner_updates_own_kit(self, as_member, kit):
        response = as_member.post(f'/update_kit/{kit.id}/', {
            'quantity': '50', 'condition': 'good',
        })
        assert response.status_code == 200
        kit.refresh_from_db()
        assert kit.quantity == 50
        assert kit.condition == 'good'

    def test_other_member_forbidden(self, client, other_member, kit):
        client.force_login(other_member)
        response = client.post(f'/update_kit/{kit.id}/', {'quantity': '1'})
        assert response.status_code == 403

    def test_manager_updates_any_kit(self, as_manager, kit):
        response = as_manager.post(f'/update_kit/{kit.id}/', {'quantity': '10'})
        assert response.status_code == 200
        kit.refresh_from_db()
        assert kit.quantity == 10

    def test_invalid_quantity_rejected(self, as_member, kit):
        response = as_member.post(f'/update_kit/{kit.id}/', {'quantity': 'abc'})
        assert response.status_code == 400


class TestDeleteKit:
    def test_owner_deletes_own_kit(self, as_member, kit):
        response = as_member.post(f'/delete_kit/{kit.id}/')
        assert response.status_code == 200
        assert not Kit.objects.filter(id=kit.id).exists()

    def test_other_member_forbidden(self, client, other_member, kit):
        client.force_login(other_member)
        response = client.post(f'/delete_kit/{kit.id}/')
        assert response.status_code == 403
        assert Kit.objects.filter(id=kit.id).exists()


class TestDashboard:
    def test_member_sees_only_own_kits(self, as_member, kit, other_member, kit_type):
        Kit.objects.create(user=other_member, kit_type_fk=kit_type, kit_type_string='x', quantity=3)
        response = as_member.get('/')
        content = response.content.decode()
        assert 'Test Kit' in content
        assert 'other_member' not in content

    def test_manager_sees_all_kits(self, as_manager, kit, other_member, kit_type):
        Kit.objects.create(user=other_member, kit_type_fk=kit_type, kit_type_string='x', quantity=3)
        response = as_manager.get('/')
        content = response.content.decode()
        assert 'member' in content and 'other_member' in content

    def test_member_does_not_see_bulk_selection_controls(self, as_member, kit):
        content = as_member.get('/').content.decode()
        assert 'bulk-delete-form' not in content
        assert 'select-all' not in content
        assert 'kit-checkbox' not in content

    def test_dashboard_filters_have_visible_labels(self, as_member):
        content = as_member.get('/').content.decode()
        assert 'for="filter-search"' in content
        assert 'for="filter-sort"' in content
        assert 'for="filter-order"' in content
        assert 'Search inventory' in content

    def test_bulk_delete_manager_only(self, as_member, kit):
        as_member.post('/', {'action': 'bulk_delete', 'kit_ids': [kit.id]})
        assert Kit.objects.filter(id=kit.id, is_active=True).exists()

    def test_bulk_delete_by_manager(self, as_manager, kit):
        as_manager.post('/', {'action': 'bulk_delete', 'kit_ids': [kit.id]})
        assert not Kit.objects.filter(id=kit.id, is_active=True).exists()


class TestKitApi:
    def test_get_user_kits_own(self, as_member, member, kit):
        response = as_member.get(f'/get_user_kits/{member.id}/')
        data = json.loads(response.content)
        assert data['success'] is True
        assert len(data['kits']) == 1

    def test_get_user_kits_others_forbidden(self, as_member, other_member):
        response = as_member.get(f'/get_user_kits/{other_member.id}/')
        assert response.status_code == 403
