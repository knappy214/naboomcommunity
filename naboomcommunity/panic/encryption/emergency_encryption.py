"""
Emergency Data Encryption Service
Handles encryption and decryption of sensitive emergency response data.
"""

import logging
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmergencyEncryptionService:
    """
    Service for encrypting and decrypting sensitive emergency response data.
    """
    
    def __init__(self):
        """Initialize the encryption service."""
        self.logger = logger
        self.secret_key = self._get_secret_key()
        self.cipher_suite = Fernet(self.secret_key)
    
    def _get_secret_key(self) -> bytes:
        """
        Get or generate the secret key for encryption.
        
        Returns:
            Secret key bytes
        """
        try:
            # Use Django's SECRET_KEY as the base for encryption
            secret_key = settings.SECRET_KEY.encode('utf-8')
            
            # Derive a proper Fernet key from the secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'naboom_emergency_salt',  # In production, use a random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key))
            return key
            
        except Exception as e:
            self.logger.error(f"Secret key generation error: {str(e)}")
            # Fallback to a generated key (not recommended for production)
            return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> Dict[str, any]:
        """
        Encrypt sensitive data.
        
        Args:
            data: String data to encrypt
            
        Returns:
            Dict containing encrypted data and metadata
        """
        try:
            # Convert string to bytes
            data_bytes = data.encode('utf-8')
            
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(data_bytes)
            
            # Encode to base64 for storage
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
            return {
                'encrypted_data': encrypted_b64,
                'encryption_method': 'Fernet',
                'encrypted_at': timezone.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Data encryption error: {str(e)}")
            return {
                'encrypted_data': None,
                'encryption_method': 'Fernet',
                'encrypted_at': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def decrypt_data(self, encrypted_data: str) -> Dict[str, any]:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Dict containing decrypted data and metadata
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt the data
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            
            # Convert back to string
            decrypted_data = decrypted_bytes.decode('utf-8')
            
            return {
                'decrypted_data': decrypted_data,
                'decryption_method': 'Fernet',
                'decrypted_at': timezone.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Data decryption error: {str(e)}")
            return {
                'decrypted_data': None,
                'decryption_method': 'Fernet',
                'decrypted_at': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def encrypt_medical_data(self, medical_data: Dict[str, any]) -> Dict[str, any]:
        """
        Encrypt medical data with additional security measures.
        
        Args:
            medical_data: Medical data dictionary to encrypt
            
        Returns:
            Dict containing encrypted medical data
        """
        try:
            import json
            
            # Convert medical data to JSON string
            medical_json = json.dumps(medical_data, default=str)
            
            # Encrypt the JSON data
            encryption_result = self.encrypt_data(medical_json)
            
            if encryption_result['success']:
                return {
                    'encrypted_medical_data': encryption_result['encrypted_data'],
                    'encryption_method': 'Fernet',
                    'data_type': 'medical',
                    'encrypted_at': timezone.now().isoformat(),
                    'success': True
                }
            else:
                return {
                    'encrypted_medical_data': None,
                    'encryption_method': 'Fernet',
                    'data_type': 'medical',
                    'encrypted_at': timezone.now().isoformat(),
                    'success': False,
                    'error': encryption_result.get('error')
                }
                
        except Exception as e:
            self.logger.error(f"Medical data encryption error: {str(e)}")
            return {
                'encrypted_medical_data': None,
                'encryption_method': 'Fernet',
                'data_type': 'medical',
                'encrypted_at': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def decrypt_medical_data(self, encrypted_medical_data: str) -> Dict[str, any]:
        """
        Decrypt medical data.
        
        Args:
            encrypted_medical_data: Encrypted medical data
            
        Returns:
            Dict containing decrypted medical data
        """
        try:
            import json
            
            # Decrypt the data
            decryption_result = self.decrypt_data(encrypted_medical_data)
            
            if decryption_result['success']:
                # Parse the JSON data
                medical_data = json.loads(decryption_result['decrypted_data'])
                
                return {
                    'medical_data': medical_data,
                    'decryption_method': 'Fernet',
                    'data_type': 'medical',
                    'decrypted_at': timezone.now().isoformat(),
                    'success': True
                }
            else:
                return {
                    'medical_data': None,
                    'decryption_method': 'Fernet',
                    'data_type': 'medical',
                    'decrypted_at': timezone.now().isoformat(),
                    'success': False,
                    'error': decryption_result.get('error')
                }
                
        except Exception as e:
            self.logger.error(f"Medical data decryption error: {str(e)}")
            return {
                'medical_data': None,
                'decryption_method': 'Fernet',
                'data_type': 'medical',
                'decrypted_at': timezone.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def validate_encryption_key(self) -> bool:
        """
        Validate that the encryption key is working properly.
        
        Returns:
            True if key is valid
        """
        try:
            # Test encryption and decryption
            test_data = "test_emergency_data"
            encrypted = self.encrypt_data(test_data)
            
            if not encrypted['success']:
                return False
            
            decrypted = self.decrypt_data(encrypted['encrypted_data'])
            
            return decrypted['success'] and decrypted['decrypted_data'] == test_data
            
        except Exception as e:
            self.logger.error(f"Encryption key validation error: {str(e)}")
            return False
