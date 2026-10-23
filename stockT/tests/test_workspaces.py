from django.test import TestCase
from django.urls import reverse
from stockT.models import User, Workspace, WorkspaceProduct


class WorkspaceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='test-pass')
        self.other = User.objects.create_user(username='other', password='test-pass', role='admin')
        self.workspace = Workspace.objects.create(owner=self.owner, name='Shop')
        self.client.force_login(self.owner)

    def product_data(self, **changes):
        return dict(name='Coffee', sku='C01', quantity=10, version=0, unit='bags', location='Shelf A', **changes)

    def test_create_empty_workspace_and_product(self):
        response = self.client.post(reverse('workspace_list'), {'name': 'New shop', 'description': ''})
        workspace = Workspace.objects.get(name='New shop')
        self.assertRedirects(response, reverse('workspace_detail', args=[workspace.pk]))
        self.assertEqual(workspace.products.count(), 0)
        response = self.client.post(reverse('workspace_detail', args=[workspace.pk]), self.product_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(workspace.products.get().quantity, 10)
        self.assertFalse(self.workspace.products.exists())

    def test_workspace_is_private_even_from_admin_role(self):
        self.client.force_login(self.other)
        url = reverse('workspace_detail', args=[self.workspace.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self.product_data()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('workspace_list')), 'Shop')

    def test_sku_unique_only_within_workspace_and_edit_is_scoped(self):
        product = WorkspaceProduct.objects.create(workspace=self.workspace, name='Coffee', sku='C01')
        url = reverse('workspace_detail', args=[self.workspace.pk])
        self.assertContains(self.client.post(url, self.product_data()), 'already exists')
        other_space = Workspace.objects.create(owner=self.owner, name='Other shop')
        other_url = reverse('workspace_detail', args=[other_space.pk])
        self.assertEqual(self.client.post(other_url, self.product_data()).status_code, 302)
        self.assertEqual(self.client.get(reverse('workspace_product_edit', args=[other_space.pk, product.pk])).status_code, 404)
        edit = reverse('workspace_product_edit', args=[self.workspace.pk, product.pk])
        self.assertEqual(self.client.post(edit, self.product_data()).status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.quantity, 10)

    def test_invalid_quantity_and_anonymous_access(self):
        data = self.product_data()
        data['quantity'] = -1
        url = reverse('workspace_detail', args=[self.workspace.pk])
        self.assertEqual(self.client.post(url, data).status_code, 200)
        self.assertFalse(self.workspace.products.exists())
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_stale_edit_cannot_overwrite_newer_quantity(self):
        product = WorkspaceProduct.objects.create(workspace=self.workspace, name='Coffee', sku='C01')
        url = reverse('workspace_product_edit', args=[self.workspace.pk, product.pk])
        self.assertEqual(self.client.post(url, self.product_data()).status_code, 302)
        stale_data = self.product_data()
        stale_data['quantity'] = 999
        self.assertContains(self.client.post(url, stale_data), 'changed since you opened')
        product.refresh_from_db()
        self.assertEqual(product.quantity, 10)
        self.assertEqual(product.version, 1)

    def test_required_fields_and_quantity_boundaries(self):
        url = reverse('workspace_detail', args=[self.workspace.pk])
        for value in ['', '1.5', 'not a number', '-1', '9999999999999999999999999999999']:
            data = self.product_data()
            data['quantity'] = value
            self.assertEqual(self.client.post(url, data).status_code, 200)
        self.assertEqual(self.client.post(url, {}).status_code, 200)
        data = self.product_data()
        data['quantity'] = 0
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.workspace.products.get().quantity, 0)

    def test_csrf_methods_and_owner_cannot_be_forged(self):
        from django.test import Client
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.owner)
        url = reverse('workspace_list')
        self.assertEqual(secure.post(url, {'name': 'Forged'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 405)
        self.client.post(url, {'name': 'Mine', 'owner': self.other.pk})
        self.assertEqual(Workspace.objects.get(name='Mine').owner, self.owner)

    def test_pagination_and_escaped_product_name(self):
        WorkspaceProduct.objects.bulk_create([
            WorkspaceProduct(workspace=self.workspace, name=f'Product {i:03}', sku=f'P{i}')
            for i in range(51)
        ])
        url = reverse('workspace_detail', args=[self.workspace.pk])
        response = self.client.get(url)
        self.assertEqual(len(response.context['products']), 50)
        self.assertEqual(response.context['product_count'], 51)
        self.assertEqual(len(self.client.get(url, {'page': 2}).context['products']), 1)
        self.assertEqual(self.client.get(url, {'page': 'invalid'}).status_code, 200)
        WorkspaceProduct.objects.create(workspace=self.workspace, name='<script>alert(1)</script>', sku='XSS')
        response = self.client.get(url)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
