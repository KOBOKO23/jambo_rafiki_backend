from unittest.mock import patch

from django.test import Client, TestCase


class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_endpoint_returns_ok(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_ready_endpoint_returns_ok_when_database_available(self):
        response = self.client.get('/ready/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ready')
        self.assertEqual(response.json()['checks']['database'], 'ok')

    @patch('core.health_views.check_database_ready', return_value=(False, 'db unavailable'))
    def test_ready_endpoint_returns_503_when_database_unavailable(self, _mock_check):
        response = self.client.get('/ready/')
        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload['status'], 'not_ready')
        self.assertEqual(payload['checks']['database'], 'error')
        self.assertIn('database', payload['errors'])

    def test_organization_config_endpoint_returns_expected_defaults(self):
        response = self.client.get('/api/v1/organization/')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertNotIn('website', payload)
        self.assertNotIn('bank_account', payload)
        self.assertEqual(payload['contact']['email'], 'info@jamborafiki.org')
        self.assertNotIn('call_redirect_number', payload['contact'])
        self.assertEqual(payload['contact']['call_redirect_url'], 'tel:+254799616542')

    def test_organization_config_endpoint_uses_settings_overrides(self):
        with self.settings(
            ORGANIZATION_DOMAIN='example.org',
            ORGANIZATION_WEBSITE_URL='https://example.org',
            ORGANIZATION_PUBLIC_EMAIL='ops@example.org',
            ORGANIZATION_CALL_REDIRECT_NUMBER='+254700000000',
            ORGANIZATION_BANK_CODE='01',
            ORGANIZATION_BANK_BRANCH_CODE='999',
            ORGANIZATION_BANK_SWIFT_CODE='EXAMPLEXX',
            ORGANIZATION_BANK_ACCOUNT_NAME='Example Account',
            ORGANIZATION_BANK_ACCOUNT_NUMBER='000111222333',
        ):
            response = self.client.get('/api/v1/organization/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['website']['domain'], 'example.org')
        self.assertEqual(payload['contact']['email'], 'ops@example.org')
        self.assertEqual(payload['contact']['call_redirect_url'], 'tel:+254700000000')
        self.assertEqual(payload['bank_account']['account_number'], '000111222333')
