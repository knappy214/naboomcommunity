"""
Emergency Consent Management Migration
Creates emergency consent management system.
"""

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    """
    Emergency Consent Management Migration
    
    Creates the emergency consent management models:
    - EmergencyConsent: User consent records
    - EmergencyConsentTemplate: Consent templates
    """
    
    dependencies = [
        ('panic', '0005_emergency_auth_permissions'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        # Create EmergencyConsentTemplate model
        migrations.CreateModel(
            name='EmergencyConsentTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('consent_type', models.CharField(choices=[('medical_basic', 'Basic Medical Information'), ('medical_full', 'Full Medical Information'), ('location_tracking', 'Location Tracking'), ('emergency_contact', 'Emergency Contact Access'), ('family_notification', 'Family Notification'), ('external_services', 'External Emergency Services'), ('data_sharing', 'Data Sharing with Responders')], max_length=50)),
                ('category', models.CharField(choices=[('medical', 'Medical Information'), ('location', 'Location Data'), ('emergency', 'Emergency Response'), ('privacy', 'Privacy & Data Protection')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('consent_text', models.TextField()),
                ('legal_text', models.TextField(blank=True)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_required', models.BooleanField(default=True)),
                ('expires_days', models.IntegerField(blank=True, help_text='Consent expiration in days', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Consent Template',
                'verbose_name_plural': 'Emergency Consent Templates',
                'db_table': 'panic_emergency_consent_template',
                'ordering': ['category', 'name'],
            },
        ),
        
        # Create EmergencyConsent model
        migrations.CreateModel(
            name='EmergencyConsent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('consent_type', models.CharField(choices=[('medical_basic', 'Basic Medical Information'), ('medical_full', 'Full Medical Information'), ('location_tracking', 'Location Tracking'), ('emergency_contact', 'Emergency Contact Access'), ('family_notification', 'Family Notification'), ('external_services', 'External Emergency Services'), ('data_sharing', 'Data Sharing with Responders')], max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('granted', 'Granted'), ('denied', 'Denied'), ('expired', 'Expired'), ('revoked', 'Revoked')], default='pending', max_length=20)),
                ('granted_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('consent_text', models.TextField(help_text='Text of the consent agreement')),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('context_data', models.JSONField(blank=True, default=dict)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='emergency_consents', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency Consent',
                'verbose_name_plural': 'Emergency Consents',
                'db_table': 'panic_emergency_consent',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add constraints
        migrations.AddConstraint(
            model_name='emergencyconsent',
            constraint=models.UniqueConstraint(fields=['user', 'consent_type'], name='emergency_consent_user_type_unique'),
        ),
        
        # Add indexes
        migrations.RunSQL(
            "CREATE INDEX emergency_consent_user_type_idx ON panic_emergency_consent (user_id, consent_type);",
            reverse_sql="DROP INDEX IF EXISTS emergency_consent_user_type_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_consent_status_expiry_idx ON panic_emergency_consent (status, expires_at);",
            reverse_sql="DROP INDEX IF EXISTS emergency_consent_status_expiry_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_consent_type_status_idx ON panic_emergency_consent (consent_type, status);",
            reverse_sql="DROP INDEX IF EXISTS emergency_consent_type_status_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_consent_template_type_active_idx ON panic_emergency_consent_template (consent_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_consent_template_type_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_consent_template_category_active_idx ON panic_emergency_consent_template (category, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_consent_template_category_active_idx;"
        ),
    ]
