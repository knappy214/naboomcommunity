"""
Integration Tests for Medical Information Retrieval
Tests medical data integration and privacy controls for emergency response.
"""

import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from django.core.cache import cache

from ..models import EmergencyMedical, MedicalCondition, Medication, Allergy
from ..services.medical_service import MedicalService

User = get_user_model()


class MedicalIntegrationTest(APITestCase):
    """
    Integration tests for medical information retrieval and processing.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='+27123456789'
        )
        
        # Create JWT token for authentication
        self.token = AccessToken.for_user(self.user)
        
        # Set up API client with authentication
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Clear cache before each test
        cache.clear()
        
        # Create medical data
        self.setup_medical_data()
    
    def setup_medical_data(self):
        """Set up medical test data."""
        # Create medical conditions
        self.diabetes = MedicalCondition.objects.create(
            name='Type 2 Diabetes',
            description='Diabetes mellitus type 2',
            severity_level='moderate',
            requires_immediate_attention=False,
            icd10_code='E11',
            snomed_code='44054006'
        )
        
        self.hypertension = MedicalCondition.objects.create(
            name='Hypertension',
            description='High blood pressure',
            severity_level='moderate',
            requires_immediate_attention=False,
            icd10_code='I10',
            snomed_code='38341003'
        )
        
        # Create medications
        self.insulin = Medication.objects.create(
            name='Insulin Glargine',
            generic_name='insulin glargine',
            medication_type='insulin',
            dosage='100 units/mL',
            frequency='Once daily',
            ndc_code='00088-5040-01',
            rxnorm_code='261551'
        )
        
        self.metformin = Medication.objects.create(
            name='Metformin',
            generic_name='metformin hydrochloride',
            medication_type='antidiabetic',
            dosage='500mg',
            frequency='Twice daily',
            ndc_code='00088-5040-02',
            rxnorm_code='860975'
        )
        
        # Create allergies
        self.penicillin_allergy = Allergy.objects.create(
            name='Penicillin',
            description='Allergic reaction to penicillin',
            severity_level='severe',
            requires_immediate_attention=True,
            snomed_code='294461005'
        )
        
        self.latex_allergy = Allergy.objects.create(
            name='Latex',
            description='Latex allergy',
            severity_level='moderate',
            requires_immediate_attention=False,
            snomed_code='294461006'
        )
        
        # Create emergency medical record
        self.emergency_medical = EmergencyMedical.objects.create(
            user=self.user,
            blood_type='O+',
            consent_level='full',
            consent_given_at=timezone.now(),
            consent_expires_at=timezone.now() + timezone.timedelta(days=365),
            emergency_contact_name='John Doe',
            emergency_contact_phone='+27123456789',
            emergency_contact_relationship='Spouse',
            is_encrypted=False
        )
        
        # Add medical conditions
        self.emergency_medical.medical_conditions.add(self.diabetes, self.hypertension)
        
        # Add medications
        self.emergency_medical.medications.add(self.insulin, self.metformin)
        
        # Add allergies
        self.emergency_medical.allergies.add(self.penicillin_allergy, self.latex_allergy)
    
    def test_medical_data_retrieval_with_full_consent(self):
        """
        Test medical data retrieval with full consent.
        Should return complete medical information.
        """
        url = reverse('panic:medical-data')
        
        response = self.client.get(url)
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include medical information
        self.assertIn('blood_type', response.data)
        self.assertIn('medical_conditions', response.data)
        self.assertIn('medications', response.data)
        self.assertIn('allergies', response.data)
        self.assertIn('emergency_contact', response.data)
        
        # Should include specific data
        self.assertEqual(response.data['blood_type'], 'O+')
        self.assertEqual(len(response.data['medical_conditions']), 2)
        self.assertEqual(len(response.data['medications']), 2)
        self.assertEqual(len(response.data['allergies']), 2)
        
        # Should include emergency contact
        emergency_contact = response.data['emergency_contact']
        self.assertEqual(emergency_contact['name'], 'John Doe')
        self.assertEqual(emergency_contact['phone'], '+27123456789')
        self.assertEqual(emergency_contact['relationship'], 'Spouse')
    
    def test_medical_data_retrieval_with_basic_consent(self):
        """
        Test medical data retrieval with basic consent.
        Should return limited medical information.
        """
        # Update consent level
        self.emergency_medical.consent_level = 'basic'
        self.emergency_medical.save()
        
        url = reverse('panic:medical-data')
        
        response = self.client.get(url)
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include basic information only
        self.assertIn('blood_type', response.data)
        self.assertIn('emergency_contact', response.data)
        
        # Should not include detailed medical information
        self.assertNotIn('medical_conditions', response.data)
        self.assertNotIn('medications', response.data)
        self.assertNotIn('allergies', response.data)
    
    def test_medical_data_retrieval_without_consent(self):
        """
        Test medical data retrieval without consent.
        Should return minimal information only.
        """
        # Update consent level
        self.emergency_medical.consent_level = 'none'
        self.emergency_medical.save()
        
        url = reverse('panic:medical-data')
        
        response = self.client.get(url)
        
        # Should succeed but with limited data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include only emergency contact
        self.assertIn('emergency_contact', response.data)
        
        # Should not include medical information
        self.assertNotIn('blood_type', response.data)
        self.assertNotIn('medical_conditions', response.data)
        self.assertNotIn('medications', response.data)
        self.assertNotIn('allergies', response.data)
    
    def test_medical_data_retrieval_expired_consent(self):
        """
        Test medical data retrieval with expired consent.
        Should return minimal information only.
        """
        # Set expired consent
        self.emergency_medical.consent_level = 'full'
        self.emergency_medical.consent_expires_at = timezone.now() - timezone.timedelta(days=1)
        self.emergency_medical.save()
        
        url = reverse('panic:medical-data')
        
        response = self.client.get(url)
        
        # Should succeed but with limited data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should include only emergency contact
        self.assertIn('emergency_contact', response.data)
        
        # Should not include medical information due to expired consent
        self.assertNotIn('blood_type', response.data)
        self.assertNotIn('medical_conditions', response.data)
        self.assertNotIn('medications', response.data)
        self.assertNotIn('allergies', response.data)
    
    def test_medical_data_retrieval_unauthorized(self):
        """
        Test medical data retrieval without authentication.
        Should return 401 Unauthorized.
        """
        # Create new client without authentication
        unauthenticated_client = APIClient()
        
        url = reverse('panic:medical-data')
        
        response = unauthenticated_client.get(url)
        
        # Should return unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_medical_data_retrieval_different_user(self):
        """
        Test medical data retrieval for different user.
        Should return 403 Forbidden.
        """
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Create token for other user
        other_token = AccessToken.for_user(other_user)
        
        # Set up client with other user's token
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        
        url = reverse('panic:medical-data')
        
        response = other_client.get(url)
        
        # Should return forbidden (no medical data for other user)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_medical_data_retrieval_encrypted_data(self):
        """
        Test medical data retrieval with encrypted data.
        Should decrypt and return data correctly.
        """
        # Mark data as encrypted
        self.emergency_medical.is_encrypted = True
        self.emergency_medical.encryption_key_id = 'test-key-123'
        self.emergency_medical.save()
        
        url = reverse('panic:medical-data')
        
        with patch('panic.services.medical_service.MedicalService.decrypt_medical_data') as mock_decrypt:
            mock_decrypt.return_value = {
                'blood_type': 'O+',
                'medical_conditions': [
                    {'name': 'Type 2 Diabetes', 'severity': 'moderate'},
                    {'name': 'Hypertension', 'severity': 'moderate'}
                ],
                'medications': [
                    {'name': 'Insulin Glargine', 'dosage': '100 units/mL'},
                    {'name': 'Metformin', 'dosage': '500mg'}
                ],
                'allergies': [
                    {'name': 'Penicillin', 'severity': 'severe'},
                    {'name': 'Latex', 'severity': 'moderate'}
                ]
            }
            
            response = self.client.get(url)
            
            # Should succeed
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Should call decrypt function
            mock_decrypt.assert_called_once()
            
            # Should include decrypted data
            self.assertIn('blood_type', response.data)
            self.assertIn('medical_conditions', response.data)
            self.assertIn('medications', response.data)
            self.assertIn('allergies', response.data)
    
    def test_medical_data_retrieval_performance(self):
        """
        Test medical data retrieval performance.
        Should complete within acceptable time limits.
        """
        url = reverse('panic:medical-data')
        
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should complete within 2 seconds
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, f"Response time {response_time:.2f}s exceeds 2 second limit")
    
    def test_medical_data_retrieval_caching(self):
        """
        Test medical data retrieval caching.
        Should cache medical data for performance.
        """
        url = reverse('panic:medical-data')
        
        # First request
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Should have similar response times (cached)
        # This is a basic test - in practice, you'd check cache hit rates
        self.assertEqual(response1.data['blood_type'], response2.data['blood_type'])
    
    def test_medical_data_retrieval_audit_logging(self):
        """
        Test medical data retrieval audit logging.
        Should log access to medical data.
        """
        url = reverse('panic:medical-data')
        
        response = self.client.get(url)
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should create audit log
        from ..models import EmergencyAuditLog
        audit_logs = EmergencyAuditLog.objects.filter(
            user=self.user,
            action_type='medical_access'
        )
        self.assertEqual(audit_logs.count(), 1)
        
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.severity, 'medium')
        self.assertIn('Medical data accessed', audit_log.description)
    
    def test_medical_data_retrieval_rate_limiting(self):
        """
        Test medical data retrieval rate limiting.
        Should respect rate limits for medical data access.
        """
        url = reverse('panic:medical-data')
        
        # Make multiple requests quickly to trigger rate limiting
        responses = []
        for i in range(10):  # Exceed rate limit
            response = self.client.get(url)
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited_responses = [r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        self.assertGreater(len(rate_limited_responses), 0, "Rate limiting not working")
    
    def test_medical_data_retrieval_error_handling(self):
        """
        Test medical data retrieval error handling.
        Should handle errors gracefully.
        """
        url = reverse('panic:medical-data')
        
        # Mock an internal error
        with patch('panic.models.EmergencyMedical.objects.get', side_effect=Exception('Database error')):
            response = self.client.get(url)
            
            # Should return error response
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)
            self.assertIn('Internal server error', response.data['error'])


class MedicalServiceIntegrationTest(TransactionTestCase):
    """
    Integration tests for the MedicalService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='+27123456789'
        )
        
        self.medical_service = MedicalService()
        
        # Create medical data
        self.setup_medical_data()
    
    def setup_medical_data(self):
        """Set up medical test data."""
        # Create medical conditions
        self.diabetes = MedicalCondition.objects.create(
            name='Type 2 Diabetes',
            description='Diabetes mellitus type 2',
            severity_level='moderate',
            requires_immediate_attention=False
        )
        
        # Create medications
        self.insulin = Medication.objects.create(
            name='Insulin Glargine',
            generic_name='insulin glargine',
            medication_type='insulin',
            dosage='100 units/mL'
        )
        
        # Create allergies
        self.penicillin_allergy = Allergy.objects.create(
            name='Penicillin',
            description='Allergic reaction to penicillin',
            severity_level='severe',
            requires_immediate_attention=True
        )
        
        # Create emergency medical record
        self.emergency_medical = EmergencyMedical.objects.create(
            user=self.user,
            blood_type='O+',
            consent_level='full',
            consent_given_at=timezone.now(),
            emergency_contact_name='John Doe',
            emergency_contact_phone='+27123456789',
            is_encrypted=False
        )
        
        # Add medical data
        self.emergency_medical.medical_conditions.add(self.diabetes)
        self.emergency_medical.medications.add(self.insulin)
        self.emergency_medical.allergies.add(self.penicillin_allergy)
    
    def test_medical_service_data_retrieval(self):
        """
        Test MedicalService data retrieval.
        Should retrieve medical data correctly.
        """
        result = self.medical_service.get_medical_data(self.user)
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('medical_data', result)
        
        medical_data = result['medical_data']
        self.assertEqual(medical_data['blood_type'], 'O+')
        self.assertEqual(len(medical_data['medical_conditions']), 1)
        self.assertEqual(len(medical_data['medications']), 1)
        self.assertEqual(len(medical_data['allergies']), 1)
    
    def test_medical_service_consent_validation(self):
        """
        Test MedicalService consent validation.
        Should validate consent levels correctly.
        """
        # Test full consent
        result = self.medical_service.validate_consent(self.user, 'full')
        self.assertTrue(result['has_consent'])
        self.assertEqual(result['consent_level'], 'full')
        
        # Test basic consent
        self.emergency_medical.consent_level = 'basic'
        self.emergency_medical.save()
        
        result = self.medical_service.validate_consent(self.user, 'basic')
        self.assertTrue(result['has_consent'])
        self.assertEqual(result['consent_level'], 'basic')
        
        # Test no consent
        self.emergency_medical.consent_level = 'none'
        self.emergency_medical.save()
        
        result = self.medical_service.validate_consent(self.user, 'full')
        self.assertFalse(result['has_consent'])
        self.assertEqual(result['consent_level'], 'none')
    
    def test_medical_service_encryption(self):
        """
        Test MedicalService encryption.
        Should encrypt and decrypt medical data correctly.
        """
        medical_data = {
            'blood_type': 'O+',
            'medical_conditions': [
                {'name': 'Type 2 Diabetes', 'severity': 'moderate'}
            ],
            'medications': [
                {'name': 'Insulin Glargine', 'dosage': '100 units/mL'}
            ],
            'allergies': [
                {'name': 'Penicillin', 'severity': 'severe'}
            ]
        }
        
        # Test encryption
        encrypted_result = self.medical_service.encrypt_medical_data(
            self.user, medical_data
        )
        
        self.assertTrue(encrypted_result['success'])
        self.assertIn('encrypted_data', encrypted_result)
        self.assertIn('encryption_key_id', encrypted_result)
        
        # Test decryption
        decrypted_result = self.medical_service.decrypt_medical_data(
            encrypted_result['encrypted_data'],
            encrypted_result['encryption_key_id']
        )
        
        self.assertTrue(decrypted_result['success'])
        self.assertEqual(decrypted_result['medical_data']['blood_type'], 'O+')
    
    def test_medical_service_emergency_contact_retrieval(self):
        """
        Test MedicalService emergency contact retrieval.
        Should retrieve emergency contact information correctly.
        """
        result = self.medical_service.get_emergency_contact(self.user)
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('emergency_contact', result)
        
        emergency_contact = result['emergency_contact']
        self.assertEqual(emergency_contact['name'], 'John Doe')
        self.assertEqual(emergency_contact['phone'], '+27123456789')
    
    def test_medical_service_critical_conditions_retrieval(self):
        """
        Test MedicalService critical conditions retrieval.
        Should retrieve critical medical conditions correctly.
        """
        result = self.medical_service.get_critical_conditions(self.user)
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('critical_conditions', result)
        
        critical_conditions = result['critical_conditions']
        self.assertEqual(len(critical_conditions), 1)  # Penicillin allergy
        self.assertEqual(critical_conditions[0]['name'], 'Penicillin')
        self.assertEqual(critical_conditions[0]['severity'], 'severe')
    
    def test_medical_service_medication_interactions(self):
        """
        Test MedicalService medication interactions.
        Should check for potential medication interactions.
        """
        medications = [
            {'name': 'Insulin Glargine', 'dosage': '100 units/mL'},
            {'name': 'Metformin', 'dosage': '500mg'}
        ]
        
        result = self.medical_service.check_medication_interactions(medications)
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('interactions', result)
        self.assertIn('warnings', result)
    
    def test_medical_service_allergy_check(self):
        """
        Test MedicalService allergy check.
        Should check for potential allergic reactions.
        """
        medications = [
            {'name': 'Penicillin', 'dosage': '500mg'}
        ]
        
        result = self.medical_service.check_allergies(self.user, medications)
        
        # Should succeed
        self.assertTrue(result['success'])
        self.assertIn('allergy_warnings', result)
        self.assertIn('allergic_medications', result)
        
        # Should detect penicillin allergy
        self.assertGreater(len(result['allergy_warnings']), 0)
        self.assertIn('Penicillin', result['allergic_medications'])
    
    def test_medical_service_error_handling(self):
        """
        Test MedicalService error handling.
        Should handle errors gracefully.
        """
        # Test with invalid user
        result = self.medical_service.get_medical_data(None)
        
        # Should fail gracefully
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_medical_service_caching(self):
        """
        Test MedicalService caching.
        Should cache medical data for performance.
        """
        # First call
        result1 = self.medical_service.get_medical_data(self.user)
        self.assertTrue(result1['success'])
        
        # Second call
        result2 = self.medical_service.get_medical_data(self.user)
        self.assertTrue(result2['success'])
        
        # Should have similar response times (cached)
        # This is a basic test - in practice, you'd check cache hit rates
        self.assertEqual(result1['medical_data']['blood_type'], result2['medical_data']['blood_type'])
    
    def test_medical_service_audit_logging(self):
        """
        Test MedicalService audit logging.
        Should log medical data access.
        """
        result = self.medical_service.get_medical_data(self.user)
        
        # Should succeed
        self.assertTrue(result['success'])
        
        # Should create audit log
        from ..models import EmergencyAuditLog
        audit_logs = EmergencyAuditLog.objects.filter(
            user=self.user,
            action_type='medical_access'
        )
        self.assertEqual(audit_logs.count(), 1)
        
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.severity, 'medium')
        self.assertIn('Medical data accessed', audit_log.description)
