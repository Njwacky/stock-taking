#!/usr/bin/env python
"""
Test script for the new Stock Distribution page functionality.
Tests manager and supervisor access, password verification, and distribution workflow.
"""

import os
import sys
import django

# Add the project root to Python path after moving this script under tests/manual.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_conf.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from stockT.models import KitType, Kit
from django.urls import reverse

User = get_user_model()

class StockDistributionTestCase(TestCase):
    def setUp(self):
        """Set up test users and data"""
        # Create test users with different roles
        self.manager = User.objects.create_user(
            username='test_manager',
            password='testpass123',
            role='manager',
            email='manager@test.com'
        )
        
        self.supervisor = User.objects.create_user(
            username='test_supervisor',
            password='testpass123',
            role='supervisor',
            email='supervisor@test.com'
        )
        
        self.admin = User.objects.create_user(
            username='test_admin',
            password='testpass123',
            role='admin',
            email='admin@test.com'
        )
        
        self.regular_user = User.objects.create_user(
            username='test_user',
            password='testpass123',
            role='user',
            email='user@test.com'
        )
        
        # Create test kit types
        self.kit_type1 = KitType.objects.create(
            name='Test Kit 1',
            code='TK1',
            description='Test kit type 1',
            created_by=self.manager
        )
        
        self.kit_type2 = KitType.objects.create(
            name='Test Kit 2',
            code='TK2',
            description='Test kit type 2',
            created_by=self.manager
        )
        
        self.client = Client()

    def test_manager_access(self):
        """Test that managers can access the stock distribution page"""
        self.client.login(username='test_manager', password='testpass123')
        response = self.client.get(reverse('stock_distribution'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Distribution')
        self.assertContains(response, 'Manager & Supervisor Stock Assignment Portal')

    def test_supervisor_access(self):
        """Test that supervisors can access the stock distribution page"""
        self.client.login(username='test_supervisor', password='testpass123')
        response = self.client.get(reverse('stock_distribution'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Stock Distribution')

    def test_admin_denied(self):
        """Test that admins cannot access the stock distribution page"""
        self.client.login(username='test_admin', password='testpass123')
        response = self.client.get(reverse('stock_distribution'))
        
        # Should redirect to dashboard with access denied message
        self.assertEqual(response.status_code, 302)
        # Follow the redirect to check the message
        response = self.client.get(response.url, follow=True)
        self.assertContains(response, 'Access denied')

    def test_regular_user_denied(self):
        """Test that regular users cannot access the stock distribution page"""
        self.client.login(username='test_user', password='testpass123')
        response = self.client.get(reverse('stock_distribution'))
        
        # Should redirect to dashboard with access denied message
        self.assertEqual(response.status_code, 302)

    def test_distribution_form_submission(self):
        """Test successful stock distribution"""
        self.client.login(username='test_manager', password='testpass123')
        
        # Submit distribution form
        data = {
            'recipient_user': self.regular_user.id,
            'confirm_password': 'testpass123',
            f'kit_type_{self.kit_type1.id}_qty': '5',
            f'kit_type_{self.kit_type1.id}_condition': 'new',
            f'kit_type_{self.kit_type2.id}_qty': '3',
            f'kit_type_{self.kit_type2.id}_condition': 'good',
        }
        
        response = self.client.post(reverse('stock_distribution'), data)
        
        # Should redirect back to distribution page on success
        self.assertEqual(response.status_code, 302)
        
        # Check that kits were created
        kits = Kit.objects.filter(user=self.regular_user, created_by=self.manager)
        self.assertEqual(kits.count(), 2)
        
        # Check specific kit quantities
        kit1 = kits.get(kit_type_fk=self.kit_type1)
        kit2 = kits.get(kit_type_fk=self.kit_type2)
        self.assertEqual(kit1.quantity, 5)
        self.assertEqual(kit2.quantity, 3)

    def test_password_verification_required(self):
        """Test that password verification is required"""
        self.client.login(username='test_manager', password='testpass123')
        
        # Submit without password
        data = {
            'recipient_user': self.regular_user.id,
            'confirm_password': '',  # Empty password
            f'kit_type_{self.kit_type1.id}_qty': '5',
        }
        
        response = self.client.post(reverse('stock_distribution'), data)
        
        # Should stay on page with error message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please select a user and enter your password for confirmation.')

    def test_wrong_password_rejected(self):
        """Test that wrong password is rejected"""
        self.client.login(username='test_manager', password='testpass123')
        
        # Submit with wrong password
        data = {
            'recipient_user': self.regular_user.id,
            'confirm_password': 'wrongpassword',
            f'kit_type_{self.kit_type1.id}_qty': '5',
        }
        
        response = self.client.post(reverse('stock_distribution'), data)
        
        # Should stay on page with error message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password verification failed')

    def test_no_kits_selected(self):
        """Test that form is rejected when no kits are selected"""
        self.client.login(username='test_manager', password='testpass123')
        
        # Submit with zero quantities
        data = {
            'recipient_user': self.regular_user.id,
            'confirm_password': 'testpass123',
            f'kit_type_{self.kit_type1.id}_qty': '0',
            f'kit_type_{self.kit_type2.id}_qty': '0',
        }
        
        response = self.client.post(reverse('stock_distribution'), data)
        
        # Should stay on page with error message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please select at least one kit type')

    def test_recent_activity_display(self):
        """Test that recent distribution activity is displayed"""
        self.client.login(username='test_manager', password='testpass123')
        
        # Create some test distributions
        Kit.objects.create(
            user=self.regular_user,
            created_by=self.manager,
            kit_type_fk=self.kit_type1,
            quantity=5
        )
        
        Kit.objects.create(
            user=self.regular_user,
            created_by=self.supervisor,
            kit_type_fk=self.kit_type2,
            quantity=3
        )
        
        response = self.client.get(reverse('stock_distribution'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent Distribution Activity')
        self.assertContains(response, self.manager.username)
        self.assertContains(response, self.supervisor.username)

    def test_user_selection_excludes_admins(self):
        """Test that admin users are excluded from recipient selection"""
        self.client.login(username='test_manager', password='testpass123')
        
        response = self.client.get(reverse('stock_distribution'))
        
        self.assertEqual(response.status_code, 200)
        
        # Should not contain admin users in the selection dropdown
        self.assertNotContains(response, f'value="{self.admin.id}"')
        # Should contain regular users
        self.assertContains(response, f'value="{self.regular_user.id}"')

def run_tests():
    """Run the test suite"""
    print("🧪 Running Stock Distribution Tests...")
    print("=" * 50)
    
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(StockDistributionTestCase)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed! Stock Distribution functionality is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
