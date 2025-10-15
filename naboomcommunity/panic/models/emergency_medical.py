"""
Emergency Medical Models
Handles medical information, privacy controls, and emergency medical data.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class EmergencyMedical(models.Model):
    """
    Emergency medical information with privacy controls and encryption support.
    Optimized for emergency response with proper data protection.
    """
    
    BLOOD_TYPES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    CONSENT_LEVELS = [
        ('none', 'No Consent'),
        ('basic', 'Basic Medical Info Only'),
        ('full', 'Full Medical Information'),
        ('emergency_only', 'Emergency Use Only'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='emergency_medical')
    
    # Basic medical information
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, blank=True)
    allergies = models.JSONField(default=list, blank=True, help_text="List of known allergies")
    medications = models.JSONField(default=list, blank=True, help_text="Current medications")
    medical_conditions = models.JSONField(default=list, blank=True, help_text="Known medical conditions")
    
    # Emergency contact information
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Privacy and consent
    consent_level = models.CharField(max_length=20, choices=CONSENT_LEVELS, default='none')
    consent_given_at = models.DateTimeField(null=True, blank=True)
    consent_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Data encryption
    is_encrypted = models.BooleanField(default=False)
    encryption_key_id = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'panic_emergency_medical'
        verbose_name = 'Emergency Medical Information'
        verbose_name_plural = 'Emergency Medical Information'
        
        indexes = [
            # User and consent level for privacy queries
            models.Index(fields=['user', 'consent_level'], name='emergency_med_user_consent_idx'),
            # Consent expiration for cleanup
            models.Index(fields=['consent_expires_at'], name='emergency_med_consent_exp_idx'),
            # Encryption status for data processing
            models.Index(fields=['is_encrypted'], name='emergency_med_encryption_idx'),
        ]
        
        constraints = [
            # Ensure consent expiration is after consent given
            models.CheckConstraint(
                check=models.Q(consent_expires_at__isnull=True) | 
                      models.Q(consent_given_at__isnull=True) |
                      models.Q(consent_expires_at__gt=models.F('consent_given_at')),
                name='emergency_medical_consent_expiry_valid'
            ),
        ]
    
    def __str__(self):
        return f"Medical info for {self.user.username} (Consent: {self.consent_level})"
    
    def has_valid_consent(self):
        """
        Check if user has valid consent for medical data access.
        
        Returns:
            Boolean
        """
        if self.consent_level == 'none':
            return False
        
        if self.consent_expires_at and timezone.now() > self.consent_expires_at:
            return False
        
        return True
    
    def get_emergency_summary(self):
        """
        Get a summary of emergency-relevant medical information.
        
        Returns:
            Dict containing emergency medical summary
        """
        if not self.has_valid_consent():
            return {
                'available': False,
                'reason': 'No valid consent for medical data access'
            }
        
        return {
            'available': True,
            'blood_type': self.blood_type,
            'allergies': self.allergies,
            'medications': self.medications,
            'medical_conditions': self.medical_conditions,
            'emergency_contact': {
                'name': self.emergency_contact_name,
                'phone': self.emergency_contact_phone,
                'relationship': self.emergency_contact_relationship,
            },
            'consent_level': self.consent_level,
            'last_verified': self.last_verified_at.isoformat() if self.last_verified_at else None,
        }


class MedicalCondition(models.Model):
    """
    Standardized medical conditions for emergency response.
    """
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    severity_level = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    
    # Emergency response information
    emergency_instructions = models.TextField(blank=True)
    requires_immediate_attention = models.BooleanField(default=False)
    
    # Medical codes
    icd10_code = models.CharField(max_length=10, blank=True)
    snomed_code = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_medical_condition'
        verbose_name = 'Medical Condition'
        verbose_name_plural = 'Medical Conditions'
        
        indexes = [
            # Name for searching
            models.Index(fields=['name'], name='med_condition_name_idx'),
            # Severity for filtering
            models.Index(fields=['severity_level'], name='med_condition_severity_idx'),
            # Emergency attention flag
            models.Index(fields=['requires_immediate_attention'], name='med_condition_emergency_idx'),
        ]
        
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.severity_level})"


class Medication(models.Model):
    """
    Standardized medications for emergency response.
    """
    
    MEDICATION_TYPES = [
        ('prescription', 'Prescription'),
        ('over_the_counter', 'Over the Counter'),
        ('supplement', 'Supplement'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    medication_type = models.CharField(max_length=20, choices=MEDICATION_TYPES, default='prescription')
    
    # Dosage information
    common_dosage = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    
    # Emergency information
    emergency_instructions = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    
    # Medical codes
    ndc_code = models.CharField(max_length=20, blank=True)
    rxnorm_code = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_medication'
        verbose_name = 'Medication'
        verbose_name_plural = 'Medications'
        
        indexes = [
            # Name for searching
            models.Index(fields=['name'], name='medication_name_idx'),
            # Generic name for searching
            models.Index(fields=['generic_name'], name='medication_generic_name_idx'),
            # Type for filtering
            models.Index(fields=['medication_type'], name='medication_type_idx'),
        ]
        
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.medication_type})"


class Allergy(models.Model):
    """
    Standardized allergies for emergency response.
    """
    
    SEVERITY_LEVELS = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('life_threatening', 'Life Threatening'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    severity_level = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='moderate')
    
    # Emergency response information
    emergency_instructions = models.TextField(blank=True)
    requires_immediate_attention = models.BooleanField(default=False)
    
    # Medical codes
    snomed_code = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panic_allergy'
        verbose_name = 'Allergy'
        verbose_name_plural = 'Allergies'
        
        indexes = [
            # Name for searching
            models.Index(fields=['name'], name='allergy_name_idx'),
            # Severity for filtering
            models.Index(fields=['severity_level'], name='allergy_severity_idx'),
            # Emergency attention flag
            models.Index(fields=['requires_immediate_attention'], name='allergy_emergency_idx'),
        ]
        
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.severity_level})"
