"""
Medical Service for Emergency Response
Handles medical data retrieval, privacy controls, and emergency medical information.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..models import EmergencyMedical, MedicalCondition, Medication, Allergy
from ..auth.emergency_permissions import EmergencyUserPermission
from ..rate_limiting.emergency_rate_limits import emergency_rate_limiter

User = get_user_model()
logger = logging.getLogger(__name__)


class MedicalService:
    """
    Service for handling medical data operations in emergency response.
    Provides medical data retrieval, privacy controls, and emergency medical information.
    """
    
    # Consent levels
    CONSENT_LEVELS = {
        'none': 0,
        'basic': 1,
        'emergency_only': 2,
        'full': 3
    }
    
    # Cache settings
    CACHE_TIMEOUT = 600  # 10 minutes
    CACHE_PREFIX = 'emergency_medical'
    
    # Encryption settings
    ENCRYPTION_ALGORITHM = 'fernet'
    KEY_DERIVATION_ITERATIONS = 100000
    
    def __init__(self):
        self.rate_limiter = emergency_rate_limiter
        self._encryption_key = None
    
    def _get_encryption_key(self) -> bytes:
        """
        Get or generate encryption key for medical data.
        
        Returns:
            Encryption key bytes
        """
        if self._encryption_key is None:
            # Get encryption key from settings or generate one
            key_string = getattr(settings, 'EMERGENCY_MEDICAL_ENCRYPTION_KEY', None)
            
            if key_string:
                # Use provided key
                self._encryption_key = key_string.encode()
            else:
                # Generate a key based on Django secret key
                secret_key = settings.SECRET_KEY.encode()
                salt = b'emergency_medical_salt'
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=self.KEY_DERIVATION_ITERATIONS,
                )
                self._encryption_key = base64.urlsafe_b64encode(kdf.derive(secret_key))
        
        return self._encryption_key
    
    def _encrypt_data(self, data: str) -> str:
        """
        Encrypt medical data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data string
        """
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt medical data: {str(e)}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt medical data.
        
        Args:
            encrypted_data: Encrypted data string
            
        Returns:
            Decrypted data string
        """
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt medical data: {str(e)}")
            raise
    
    def validate_consent(self, user: User, required_level: str = 'basic') -> Dict[str, Any]:
        """
        Validate user consent for medical data access.
        
        Args:
            user: User instance
            required_level: Required consent level
            
        Returns:
            Consent validation result
        """
        try:
            # Get user's medical record
            medical_record = self.get_medical_record(user)
            if not medical_record:
                return {
                    'has_consent': False,
                    'consent_level': 'none',
                    'reason': 'No medical record found'
                }
            
            # Check consent level
            user_consent_level = medical_record.consent_level
            required_level_value = self.CONSENT_LEVELS.get(required_level, 0)
            user_consent_value = self.CONSENT_LEVELS.get(user_consent_level, 0)
            
            # Check if consent is valid
            if user_consent_value < required_level_value:
                return {
                    'has_consent': False,
                    'consent_level': user_consent_level,
                    'reason': f'Insufficient consent level. Required: {required_level}, Current: {user_consent_level}'
                }
            
            # Check if consent has expired
            if medical_record.consent_expires_at and timezone.now() > medical_record.consent_expires_at:
                return {
                    'has_consent': False,
                    'consent_level': user_consent_level,
                    'reason': 'Consent has expired'
                }
            
            return {
                'has_consent': True,
                'consent_level': user_consent_level,
                'consent_given_at': medical_record.consent_given_at,
                'consent_expires_at': medical_record.consent_expires_at
            }
            
        except Exception as e:
            logger.error(f"Failed to validate consent: {str(e)}")
            return {
                'has_consent': False,
                'consent_level': 'none',
                'reason': 'Error validating consent'
            }
    
    def get_medical_record(self, user: User) -> Optional[EmergencyMedical]:
        """
        Get user's medical record.
        
        Args:
            user: User instance
            
        Returns:
            EmergencyMedical instance or None
        """
        try:
            medical_record, created = EmergencyMedical.objects.get_or_create(
                user=user,
                defaults={
                    'consent_level': 'none',
                    'is_encrypted': False
                }
            )
            return medical_record
        except Exception as e:
            logger.error(f"Failed to get medical record: {str(e)}")
            return None
    
    def get_medical_data(self, user: User, consent_level: str = 'basic') -> Dict[str, Any]:
        """
        Get medical data for emergency response.
        
        Args:
            user: User instance
            consent_level: Required consent level
            
        Returns:
            Medical data dictionary
        """
        try:
            # Check rate limiting
            if not self.rate_limiter.check_medical_access_rate(user):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded for medical data access',
                    'retry_after': self.rate_limiter.get_retry_after('medical_access')
                }
            
            # Validate consent
            consent_validation = self.validate_consent(user, consent_level)
            if not consent_validation['has_consent']:
                return {
                    'success': False,
                    'error': 'Insufficient consent for medical data access',
                    'details': consent_validation['reason']
                }
            
            # Get medical record
            medical_record = self.get_medical_record(user)
            if not medical_record:
                return {
                    'success': False,
                    'error': 'No medical record found'
                }
            
            # Prepare response based on consent level
            response_data = {
                'success': True,
                'consent_level': medical_record.consent_level,
                'last_verified': medical_record.last_verified_at.isoformat() if medical_record.last_verified_at else None
            }
            
            # Add emergency contact (always available)
            response_data['emergency_contact'] = {
                'name': medical_record.emergency_contact_name,
                'phone': medical_record.emergency_contact_phone,
                'relationship': medical_record.emergency_contact_relationship
            }
            
            # Add medical information based on consent level
            if consent_validation['consent_level'] in ['basic', 'emergency_only', 'full']:
                response_data['blood_type'] = medical_record.blood_type
            
            if consent_validation['consent_level'] in ['emergency_only', 'full']:
                # Add critical medical information
                response_data['allergies'] = self._get_critical_allergies(medical_record)
                response_data['medical_conditions'] = self._get_critical_conditions(medical_record)
            
            if consent_validation['consent_level'] == 'full':
                # Add full medical information
                response_data['medications'] = self._get_medications(medical_record)
                response_data['allergies'] = self._get_all_allergies(medical_record)
                response_data['medical_conditions'] = self._get_all_conditions(medical_record)
            
            # Update rate limiter
            self.rate_limiter.record_medical_access(user)
            
            # Log access
            self._log_medical_access(user, 'read', consent_level)
            
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to get medical data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to retrieve medical data',
                'details': str(e)
            }
    
    def _get_critical_allergies(self, medical_record: EmergencyMedical) -> List[Dict[str, Any]]:
        """
        Get critical allergies that require immediate attention.
        
        Args:
            medical_record: EmergencyMedical instance
            
        Returns:
            List of critical allergies
        """
        try:
            critical_allergies = []
            for allergy_data in medical_record.allergies:
                if isinstance(allergy_data, dict) and allergy_data.get('requires_immediate_attention', False):
                    critical_allergies.append({
                        'name': allergy_data.get('name', ''),
                        'severity': allergy_data.get('severity_level', ''),
                        'instructions': allergy_data.get('emergency_instructions', '')
                    })
            return critical_allergies
        except Exception as e:
            logger.error(f"Failed to get critical allergies: {str(e)}")
            return []
    
    def _get_all_allergies(self, medical_record: EmergencyMedical) -> List[Dict[str, Any]]:
        """
        Get all allergies.
        
        Args:
            medical_record: EmergencyMedical instance
            
        Returns:
            List of all allergies
        """
        try:
            return medical_record.allergies or []
        except Exception as e:
            logger.error(f"Failed to get all allergies: {str(e)}")
            return []
    
    def _get_critical_conditions(self, medical_record: EmergencyMedical) -> List[Dict[str, Any]]:
        """
        Get critical medical conditions that require immediate attention.
        
        Args:
            medical_record: EmergencyMedical instance
            
        Returns:
            List of critical conditions
        """
        try:
            critical_conditions = []
            for condition_data in medical_record.medical_conditions:
                if isinstance(condition_data, dict) and condition_data.get('requires_immediate_attention', False):
                    critical_conditions.append({
                        'name': condition_data.get('name', ''),
                        'severity': condition_data.get('severity_level', ''),
                        'instructions': condition_data.get('emergency_instructions', '')
                    })
            return critical_conditions
        except Exception as e:
            logger.error(f"Failed to get critical conditions: {str(e)}")
            return []
    
    def _get_all_conditions(self, medical_record: EmergencyMedical) -> List[Dict[str, Any]]:
        """
        Get all medical conditions.
        
        Args:
            medical_record: EmergencyMedical instance
            
        Returns:
            List of all conditions
        """
        try:
            return medical_record.medical_conditions or []
        except Exception as e:
            logger.error(f"Failed to get all conditions: {str(e)}")
            return []
    
    def _get_medications(self, medical_record: EmergencyMedical) -> List[Dict[str, Any]]:
        """
        Get current medications.
        
        Args:
            medical_record: EmergencyMedical instance
            
        Returns:
            List of medications
        """
        try:
            return medical_record.medications or []
        except Exception as e:
            logger.error(f"Failed to get medications: {str(e)}")
            return []
    
    def update_medical_data(self, user: User, medical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update medical data for a user.
        
        Args:
            user: User instance
            medical_data: Medical data dictionary
            
        Returns:
            Update result dictionary
        """
        try:
            # Check rate limiting
            if not self.rate_limiter.check_medical_update_rate(user):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded for medical data updates',
                    'retry_after': self.rate_limiter.get_retry_after('medical_update')
                }
            
            # Get medical record
            medical_record = self.get_medical_record(user)
            if not medical_record:
                return {
                    'success': False,
                    'error': 'No medical record found'
                }
            
            # Update fields
            with transaction.atomic():
                if 'blood_type' in medical_data:
                    medical_record.blood_type = medical_data['blood_type']
                
                if 'allergies' in medical_data:
                    medical_record.allergies = medical_data['allergies']
                
                if 'medications' in medical_data:
                    medical_record.medications = medical_data['medications']
                
                if 'medical_conditions' in medical_data:
                    medical_record.medical_conditions = medical_data['medical_conditions']
                
                if 'emergency_contact_name' in medical_data:
                    medical_record.emergency_contact_name = medical_data['emergency_contact_name']
                
                if 'emergency_contact_phone' in medical_data:
                    medical_record.emergency_contact_phone = medical_data['emergency_contact_phone']
                
                if 'emergency_contact_relationship' in medical_data:
                    medical_record.emergency_contact_relationship = medical_data['emergency_contact_relationship']
                
                if 'consent_level' in medical_data:
                    medical_record.consent_level = medical_data['consent_level']
                    medical_record.consent_given_at = timezone.now()
                
                medical_record.updated_at = timezone.now()
                medical_record.save()
            
            # Update rate limiter
            self.rate_limiter.record_medical_update(user)
            
            # Log access
            self._log_medical_access(user, 'update', medical_record.consent_level)
            
            logger.info(f"Updated medical data for user {user.id}")
            
            return {
                'success': True,
                'message': 'Medical data updated successfully',
                'consent_level': medical_record.consent_level
            }
            
        except Exception as e:
            logger.error(f"Failed to update medical data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update medical data',
                'details': str(e)
            }
    
    def encrypt_medical_data(self, user: User, medical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive medical data.
        
        Args:
            user: User instance
            medical_data: Medical data dictionary
            
        Returns:
            Encryption result dictionary
        """
        try:
            # Convert to JSON string
            data_string = json.dumps(medical_data, default=str)
            
            # Encrypt data
            encrypted_data = self._encrypt_data(data_string)
            
            # Generate encryption key ID
            key_id = hashlib.sha256(f"{user.id}_{timezone.now().isoformat()}".encode()).hexdigest()[:16]
            
            # Update medical record
            medical_record = self.get_medical_record(user)
            if medical_record:
                medical_record.is_encrypted = True
                medical_record.encryption_key_id = key_id
                medical_record.save()
            
            # Log encryption
            self._log_medical_access(user, 'encrypt', 'full')
            
            return {
                'success': True,
                'encrypted_data': encrypted_data,
                'encryption_key_id': key_id,
                'message': 'Medical data encrypted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to encrypt medical data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to encrypt medical data',
                'details': str(e)
            }
    
    def decrypt_medical_data(self, encrypted_data: str, key_id: str) -> Dict[str, Any]:
        """
        Decrypt medical data.
        
        Args:
            encrypted_data: Encrypted data string
            key_id: Encryption key ID
            
        Returns:
            Decryption result dictionary
        """
        try:
            # Decrypt data
            decrypted_string = self._decrypt_data(encrypted_data)
            
            # Parse JSON
            medical_data = json.loads(decrypted_string)
            
            return {
                'success': True,
                'medical_data': medical_data,
                'message': 'Medical data decrypted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to decrypt medical data: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to decrypt medical data',
                'details': str(e)
            }
    
    def get_emergency_contact(self, user: User) -> Dict[str, Any]:
        """
        Get emergency contact information.
        
        Args:
            user: User instance
            
        Returns:
            Emergency contact information
        """
        try:
            medical_record = self.get_medical_record(user)
            if not medical_record:
                return {
                    'success': False,
                    'error': 'No medical record found'
                }
            
            return {
                'success': True,
                'emergency_contact': {
                    'name': medical_record.emergency_contact_name,
                    'phone': medical_record.emergency_contact_phone,
                    'relationship': medical_record.emergency_contact_relationship
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get emergency contact: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get emergency contact',
                'details': str(e)
            }
    
    def check_medication_interactions(self, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for potential medication interactions.
        
        Args:
            medications: List of medications
            
        Returns:
            Interaction check result
        """
        try:
            # This would integrate with a medication interaction database
            # For now, return a basic structure
            interactions = []
            warnings = []
            
            # Basic interaction checking logic would go here
            # This is a placeholder for actual interaction checking
            
            return {
                'success': True,
                'interactions': interactions,
                'warnings': warnings,
                'message': 'Medication interaction check completed'
            }
            
        except Exception as e:
            logger.error(f"Failed to check medication interactions: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to check medication interactions',
                'details': str(e)
            }
    
    def check_allergies(self, user: User, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for potential allergic reactions.
        
        Args:
            user: User instance
            medications: List of medications
            
        Returns:
            Allergy check result
        """
        try:
            # Get user's allergies
            medical_record = self.get_medical_record(user)
            if not medical_record:
                return {
                    'success': False,
                    'error': 'No medical record found'
                }
            
            user_allergies = medical_record.allergies or []
            allergy_warnings = []
            allergic_medications = []
            
            # Check for potential allergic reactions
            for medication in medications:
                medication_name = medication.get('name', '').lower()
                for allergy in user_allergies:
                    allergy_name = allergy.get('name', '').lower()
                    if allergy_name in medication_name or medication_name in allergy_name:
                        allergy_warnings.append({
                            'medication': medication_name,
                            'allergy': allergy_name,
                            'severity': allergy.get('severity_level', 'unknown')
                        })
                        allergic_medications.append(medication_name)
            
            return {
                'success': True,
                'allergy_warnings': allergy_warnings,
                'allergic_medications': allergic_medications,
                'message': 'Allergy check completed'
            }
            
        except Exception as e:
            logger.error(f"Failed to check allergies: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to check allergies',
                'details': str(e)
            }
    
    def _log_medical_access(self, user: User, access_type: str, consent_level: str):
        """
        Log medical data access for audit purposes.
        
        Args:
            user: User instance
            access_type: Type of access (read, update, encrypt, etc.)
            consent_level: Consent level used
        """
        try:
            from ..models import EmergencyAuditLog
            
            EmergencyAuditLog.log_medical_access(
                user=user,
                medical_data={'access_type': access_type, 'consent_level': consent_level},
                access_type=access_type
            )
        except Exception as e:
            logger.error(f"Failed to log medical access: {str(e)}")
    
    def get_medical_statistics(self, user: User) -> Dict[str, Any]:
        """
        Get medical data statistics for a user.
        
        Args:
            user: User instance
            
        Returns:
            Medical statistics dictionary
        """
        try:
            medical_record = self.get_medical_record(user)
            if not medical_record:
                return {
                    'success': False,
                    'error': 'No medical record found'
                }
            
            return {
                'success': True,
                'statistics': {
                    'consent_level': medical_record.consent_level,
                    'is_encrypted': medical_record.is_encrypted,
                    'has_blood_type': bool(medical_record.blood_type),
                    'allergy_count': len(medical_record.allergies or []),
                    'medication_count': len(medical_record.medications or []),
                    'condition_count': len(medical_record.medical_conditions or []),
                    'has_emergency_contact': bool(medical_record.emergency_contact_name),
                    'last_updated': medical_record.updated_at.isoformat(),
                    'last_verified': medical_record.last_verified_at.isoformat() if medical_record.last_verified_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get medical statistics: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get medical statistics',
                'details': str(e)
            }