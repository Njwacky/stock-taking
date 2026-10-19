"""Kit types: seeded defaults (migration) and manager CRUD."""
import pytest
from django.contrib.auth import get_user_model

from stockT.models import KitType

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestSeedData:
    def test_standard_kit_types_seeded(self):
        """Regression: fresh installs used to have zero kit types (empty dropdowns)."""
        codes = set(KitType.objects.values_list('code', flat=True))
        assert {'FEET', 'VHB18', 'VHB12', 'VHB7', 'PISTRIP', 'RIV8', 'RIV6', 'RIV5', 'RIV4'} <= codes

    def test_add_items_shows_seeded_types(self, as_member):
        response = as_member.get('/add-items/')
        assert 'VHB Boss Tape 18mm' in response.content.decode()


class TestManagement:
    def test_manager_can_add(self, as_manager):
        response = as_manager.post('/kit-types/', {
            'action': 'add', 'name': 'Custom Tape', 'code': 'CT1', 'unit_of_measure': 'rolls',
        })
        assert response.status_code == 302
        assert KitType.objects.filter(code='CT1', name='Custom Tape').exists()

    def test_duplicate_code_rejected(self, as_manager):
        as_manager.post('/kit-types/', {'action': 'add', 'name': 'A', 'code': 'DUP'})
        response = as_manager.post('/kit-types/', {'action': 'add', 'name': 'B', 'code': 'DUP'})
        assert response.status_code == 302
        assert not KitType.objects.filter(name='B').exists()

    def test_toggle_deactivates_and_reactivates(self, as_manager, kit_type):
        as_manager.post('/kit-types/', {'action': 'toggle', 'kit_type_id': kit_type.id})
        kit_type.refresh_from_db()
        assert kit_type.is_active is False
        as_manager.post('/kit-types/', {'action': 'toggle', 'kit_type_id': kit_type.id})
        kit_type.refresh_from_db()
        assert kit_type.is_active is True

    def test_deactivated_type_hidden_from_add_items(self, as_manager, as_member, kit_type):
        kit_type.is_active = False
        kit_type.save()
        response = as_member.get('/add-items/')
        assert kit_type.name not in response.content.decode()

    def test_plain_member_blocked(self, as_member):
        response = as_member.get('/kit-types/')
        assert response.status_code == 302
