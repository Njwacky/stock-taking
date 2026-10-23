"""CSV export of the dashboard kit table: scope, filters, and file format."""
import csv
import io

import pytest
from django.contrib.auth import get_user_model

from stockT.models import Kit

User = get_user_model()

pytestmark = pytest.mark.django_db


def rows(response):
    content = response.content.decode('utf-8-sig')
    return list(csv.reader(io.StringIO(content)))


class TestAccess:
    def test_requires_login(self, client):
        response = client.get('/export/kits.csv')
        assert response.status_code == 302
        assert '/login' in response.url


class TestScope:
    def test_member_exports_only_own_kits(self, as_member, member, other_member, kit_type, workspace):
        Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=5, workspace=workspace)
        Kit.objects.create(user=other_member, kit_type_fk=kit_type, kit_type_string='x', quantity=9, workspace=workspace)
        data = rows(as_member.get('/export/kits.csv'))
        usernames = {row[5] for row in data[1:]}
        assert usernames == {member.username}

    def test_manager_exports_all_kits(self, as_manager, member, other_member, kit_type, workspace):
        Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=5, workspace=workspace)
        Kit.objects.create(user=other_member, kit_type_fk=kit_type, kit_type_string='x', quantity=9, workspace=workspace)
        data = rows(as_manager.get('/export/kits.csv'))
        usernames = {row[5] for row in data[1:]}
        assert member.username in usernames
        assert other_member.username in usernames

    def test_inactive_kits_excluded(self, as_member, member, kit_type, workspace):
        Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=5, is_active=False, workspace=workspace)
        data = rows(as_member.get('/export/kits.csv'))
        assert len(data) == 1  # header only


class TestFilters:
    def test_user_filter_applied(self, as_manager, member, other_member, kit_type, workspace):
        Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=5, workspace=workspace)
        Kit.objects.create(user=other_member, kit_type_fk=kit_type, kit_type_string='x', quantity=9, workspace=workspace)
        data = rows(as_manager.get(f'/export/kits.csv?user={other_member.username}'))
        assert {row[5] for row in data[1:]} == {other_member.username}

    def test_search_filter_applied(self, as_manager, member, kit_type, workspace):
        Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=5, location='Aisle 3', workspace=workspace)
        Kit.objects.create(user=member, kit_type_fk=kit_type, kit_type_string='x', quantity=5, location='Bay 9', workspace=workspace)
        data = rows(as_manager.get('/export/kits.csv?search=Aisle'))
        assert len(data) == 2
        assert data[1][6] == 'Aisle 3'


class TestFormat:
    def test_headers_and_filename(self, as_member, kit):
        response = as_member.get('/export/kits.csv')
        assert response['Content-Type'].startswith('text/csv')
        assert 'attachment; filename="stock_export_' in response['Content-Disposition']

    def test_utf8_bom_for_excel(self, as_member, kit):
        response = as_member.get('/export/kits.csv')
        assert response.content.startswith(b'\xef\xbb\xbf')

    def test_row_values(self, as_member, member, kit):
        data = rows(as_member.get('/export/kits.csv'))
        header, row = data[0], data[1]
        assert header[0] == 'ID' and header[1] == 'Kit Type' and 'Quantity' in header
        assert row[1] == 'Test Kit'
        assert row[3] == '100'
        assert row[5] == member.username

    def test_condition_translated(self, as_member, member, kit_type, workspace):
        Kit.objects.create(
            user=member, kit_type_fk=kit_type, kit_type_string='x',
            quantity=1, condition='damaged', workspace=workspace,
        )
        data = rows(as_member.get('/export/kits.csv'))
        assert data[1][4] == 'Damaged'
