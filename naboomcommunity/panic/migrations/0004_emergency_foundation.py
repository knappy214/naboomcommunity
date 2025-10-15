"""
Emergency Response Foundation Migration
Creates core emergency response models with PostGIS integration and optimized indexes.
"""

from django.db import migrations, models
import django.contrib.gis.db.models.fields
import django.core.validators
import django.contrib.postgres.operations
import uuid


class Migration(migrations.Migration):
    """
    Emergency Response Foundation Migration
    
    Creates the core emergency response models:
    - EmergencyLocation: GPS tracking with PostGIS
    - EmergencyZone: Service zones with PostGIS polygons
    - EmergencyMedical: Medical information with privacy controls
    - MedicalCondition, Medication, Allergy: Standardized medical data
    - EmergencyAuditLog: Comprehensive audit logging
    - EmergencyAuditConfig: Audit configuration
    """
    
    initial = False
    
    dependencies = [
        ('panic', '0003_add_performance_indexes'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        # Enable PostGIS extension
        django.contrib.postgres.operations.CreateExtension('postgis'),
        
        # Create EmergencyLocation model
        migrations.CreateModel(
            name='EmergencyLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(help_text='GPS coordinates as PostGIS Point', srid=4326)),
                ('accuracy', models.FloatField(help_text='GPS accuracy in meters', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10000)])),
                ('accuracy_level', models.CharField(choices=[('high', 'High Accuracy (< 50m)'), ('medium', 'Medium Accuracy (50-100m)'), ('low', 'Low Accuracy (> 100m)')], default='medium', max_length=10)),
                ('emergency_type', models.CharField(choices=[('medical', 'Medical Emergency'), ('security', 'Security Emergency'), ('fire', 'Fire Emergency'), ('other', 'Other Emergency')], max_length=20)),
                ('description', models.TextField(blank=True, help_text='Emergency description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this emergency is still active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('altitude', models.FloatField(blank=True, help_text='Altitude in meters', null=True)),
                ('speed', models.FloatField(blank=True, help_text='Speed in m/s', null=True)),
                ('heading', models.FloatField(blank=True, help_text='Heading in degrees', null=True)),
                ('device_id', models.CharField(blank=True, max_length=255)),
                ('network_type', models.CharField(blank=True, max_length=50)),
                ('battery_level', models.IntegerField(blank=True, help_text='Battery level (0-100)', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='emergency_locations', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency Location',
                'verbose_name_plural': 'Emergency Locations',
                'db_table': 'panic_emergency_location',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create EmergencyZone model
        migrations.CreateModel(
            name='EmergencyZone',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('zone_type', models.CharField(choices=[('medical', 'Medical Zone'), ('police', 'Police Zone'), ('fire', 'Fire Zone'), ('general', 'General Emergency Zone')], max_length=20)),
                ('boundary', django.contrib.gis.db.models.fields.PolygonField(help_text='Zone boundary as PostGIS Polygon', srid=4326)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('priority', models.IntegerField(default=1, help_text='Zone priority (1=highest)')),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Zone',
                'verbose_name_plural': 'Emergency Zones',
                'db_table': 'panic_emergency_zone',
                'ordering': ['priority', 'name'],
            },
        ),
        
        # Create EmergencyMedical model
        migrations.CreateModel(
            name='EmergencyMedical',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('blood_type', models.CharField(blank=True, choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], max_length=3)),
                ('allergies', models.JSONField(blank=True, default=list, help_text='List of known allergies')),
                ('medications', models.JSONField(blank=True, default=list, help_text='Current medications')),
                ('medical_conditions', models.JSONField(blank=True, default=list, help_text='Known medical conditions')),
                ('emergency_contact_name', models.CharField(blank=True, max_length=255)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=20)),
                ('emergency_contact_relationship', models.CharField(blank=True, max_length=100)),
                ('consent_level', models.CharField(choices=[('none', 'No Consent'), ('basic', 'Basic Medical Info Only'), ('full', 'Full Medical Information'), ('emergency_only', 'Emergency Use Only')], default='none', max_length=20)),
                ('consent_given_at', models.DateTimeField(blank=True, null=True)),
                ('consent_expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_encrypted', models.BooleanField(default=False)),
                ('encryption_key_id', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_verified_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='emergency_medical', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency Medical Information',
                'verbose_name_plural': 'Emergency Medical Information',
                'db_table': 'panic_emergency_medical',
            },
        ),
        
        # Create MedicalCondition model
        migrations.CreateModel(
            name='MedicalCondition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('severity_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=10)),
                ('emergency_instructions', models.TextField(blank=True)),
                ('requires_immediate_attention', models.BooleanField(default=False)),
                ('icd10_code', models.CharField(blank=True, max_length=10)),
                ('snomed_code', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Medical Condition',
                'verbose_name_plural': 'Medical Conditions',
                'db_table': 'panic_medical_condition',
                'ordering': ['name'],
            },
        ),
        
        # Create Medication model
        migrations.CreateModel(
            name='Medication',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('generic_name', models.CharField(blank=True, max_length=255)),
                ('medication_type', models.CharField(choices=[('prescription', 'Prescription'), ('over_the_counter', 'Over the Counter'), ('supplement', 'Supplement'), ('other', 'Other')], default='prescription', max_length=20)),
                ('common_dosage', models.CharField(blank=True, max_length=100)),
                ('unit', models.CharField(blank=True, max_length=50)),
                ('emergency_instructions', models.TextField(blank=True)),
                ('contraindications', models.TextField(blank=True)),
                ('ndc_code', models.CharField(blank=True, max_length=20)),
                ('rxnorm_code', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Medication',
                'verbose_name_plural': 'Medications',
                'db_table': 'panic_medication',
                'ordering': ['name'],
            },
        ),
        
        # Create Allergy model
        migrations.CreateModel(
            name='Allergy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('severity_level', models.CharField(choices=[('mild', 'Mild'), ('moderate', 'Moderate'), ('severe', 'Severe'), ('life_threatening', 'Life Threatening')], default='moderate', max_length=20)),
                ('emergency_instructions', models.TextField(blank=True)),
                ('requires_immediate_attention', models.BooleanField(default=False)),
                ('snomed_code', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Allergy',
                'verbose_name_plural': 'Allergies',
                'db_table': 'panic_allergy',
                'ordering': ['name'],
            },
        ),
        
        # Create EmergencyAuditLog model
        migrations.CreateModel(
            name='EmergencyAuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('action_type', models.CharField(choices=[('create', 'Create'), ('read', 'Read'), ('update', 'Update'), ('delete', 'Delete'), ('panic_activated', 'Panic Button Activated'), ('location_updated', 'Location Updated'), ('medical_accessed', 'Medical Data Accessed'), ('notification_sent', 'Notification Sent'), ('responder_assigned', 'Responder Assigned'), ('status_changed', 'Status Changed'), ('data_encrypted', 'Data Encrypted'), ('data_decrypted', 'Data Decrypted'), ('sync_started', 'Sync Started'), ('sync_completed', 'Sync Completed'), ('external_api_called', 'External API Called'), ('websocket_connected', 'WebSocket Connected'), ('websocket_disconnected', 'WebSocket Disconnected'), ('authentication_failed', 'Authentication Failed'), ('permission_denied', 'Permission Denied'), ('error_occurred', 'Error Occurred')], max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=10)),
                ('description', models.TextField()),
                ('session_id', models.CharField(blank=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('object_id', models.UUIDField(blank=True, null=True)),
                ('request_method', models.CharField(blank=True, max_length=10)),
                ('request_path', models.CharField(blank=True, max_length=500)),
                ('response_status', models.IntegerField(blank=True, null=True)),
                ('old_values', models.JSONField(blank=True, default=dict)),
                ('new_values', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('stack_trace', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='emergency_audit_logs', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency Audit Log',
                'verbose_name_plural': 'Emergency Audit Logs',
                'db_table': 'panic_emergency_audit_log',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Create EmergencyAuditConfig model
        migrations.CreateModel(
            name='EmergencyAuditConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('audit_level', models.CharField(choices=[('minimal', 'Minimal - Critical events only'), ('standard', 'Standard - Important events'), ('detailed', 'Detailed - All events'), ('comprehensive', 'Comprehensive - Everything including reads')], default='standard', max_length=20)),
                ('log_reads', models.BooleanField(default=False)),
                ('log_medical_access', models.BooleanField(default=True)),
                ('log_location_updates', models.BooleanField(default=True)),
                ('log_notifications', models.BooleanField(default=True)),
                ('log_websocket_events', models.BooleanField(default=False)),
                ('retention_days', models.IntegerField(default=365)),
                ('archive_after_days', models.IntegerField(default=90)),
                ('log_failed_attempts', models.BooleanField(default=True)),
                ('log_suspicious_activity', models.BooleanField(default=True)),
                ('alert_on_critical_events', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Audit Configuration',
                'verbose_name_plural': 'Emergency Audit Configurations',
                'db_table': 'panic_emergency_audit_config',
            },
        ),
        
        # Add indexes for EmergencyLocation
        migrations.RunSQL(
            "CREATE INDEX emergency_loc_spatial_idx ON panic_emergency_location USING GIST (location);",
            reverse_sql="DROP INDEX IF EXISTS emergency_loc_spatial_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_loc_user_active_idx ON panic_emergency_location (user_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_loc_user_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_loc_type_active_idx ON panic_emergency_location (emergency_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_loc_type_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_loc_created_idx ON panic_emergency_location (created_at);",
            reverse_sql="DROP INDEX IF EXISTS emergency_loc_created_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_loc_user_type_idx ON panic_emergency_location (user_id, emergency_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_loc_user_type_idx;"
        ),
        
        # Add indexes for EmergencyZone
        migrations.RunSQL(
            "CREATE INDEX  emergency_zone_spatial_idx ON panic_emergency_zone USING GIST (boundary);",
            reverse_sql="DROP INDEX IF EXISTS emergency_zone_spatial_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_zone_type_active_idx ON panic_emergency_zone (zone_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_zone_type_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_zone_priority_idx ON panic_emergency_zone (priority);",
            reverse_sql="DROP INDEX IF EXISTS emergency_zone_priority_idx;"
        ),
        
        # Add indexes for EmergencyMedical
        migrations.RunSQL(
            "CREATE INDEX  emergency_med_user_consent_idx ON panic_emergency_medical (user_id, consent_level);",
            reverse_sql="DROP INDEX IF EXISTS emergency_med_user_consent_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_med_consent_exp_idx ON panic_emergency_medical (consent_expires_at);",
            reverse_sql="DROP INDEX IF EXISTS emergency_med_consent_exp_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_med_encryption_idx ON panic_emergency_medical (is_encrypted);",
            reverse_sql="DROP INDEX IF EXISTS emergency_med_encryption_idx;"
        ),
        
        # Add indexes for MedicalCondition
        migrations.RunSQL(
            "CREATE INDEX  med_condition_name_idx ON panic_medical_condition (name);",
            reverse_sql="DROP INDEX IF EXISTS med_condition_name_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  med_condition_severity_idx ON panic_medical_condition (severity_level);",
            reverse_sql="DROP INDEX IF EXISTS med_condition_severity_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  med_condition_emergency_idx ON panic_medical_condition (requires_immediate_attention);",
            reverse_sql="DROP INDEX IF EXISTS med_condition_emergency_idx;"
        ),
        
        # Add indexes for Medication
        migrations.RunSQL(
            "CREATE INDEX  medication_name_idx ON panic_medication (name);",
            reverse_sql="DROP INDEX IF EXISTS medication_name_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  medication_generic_name_idx ON panic_medication (generic_name);",
            reverse_sql="DROP INDEX IF EXISTS medication_generic_name_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  medication_type_idx ON panic_medication (medication_type);",
            reverse_sql="DROP INDEX IF EXISTS medication_type_idx;"
        ),
        
        # Add indexes for Allergy
        migrations.RunSQL(
            "CREATE INDEX  allergy_name_idx ON panic_allergy (name);",
            reverse_sql="DROP INDEX IF EXISTS allergy_name_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  allergy_severity_idx ON panic_allergy (severity_level);",
            reverse_sql="DROP INDEX IF EXISTS allergy_severity_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  allergy_emergency_idx ON panic_allergy (requires_immediate_attention);",
            reverse_sql="DROP INDEX IF EXISTS allergy_emergency_idx;"
        ),
        
        # Add indexes for EmergencyAuditLog
        migrations.RunSQL(
            "CREATE INDEX  emergency_audit_action_idx ON panic_emergency_audit_log (action_type, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_audit_action_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_audit_user_idx ON panic_emergency_audit_log (user_id, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_audit_user_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_audit_severity_idx ON panic_emergency_audit_log (severity, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_audit_severity_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_audit_content_idx ON panic_emergency_audit_log (content_type_id, object_id);",
            reverse_sql="DROP INDEX IF EXISTS emergency_audit_content_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_audit_ip_idx ON panic_emergency_audit_log (ip_address, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_audit_ip_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX  emergency_audit_session_idx ON panic_emergency_audit_log (session_id, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_audit_session_idx;"
        ),
        
        # Add constraints
        migrations.RunSQL(
            "ALTER TABLE panic_emergency_location ADD CONSTRAINT emergency_location_accuracy_range CHECK (accuracy >= 0 AND accuracy <= 10000);",
            reverse_sql="ALTER TABLE panic_emergency_location DROP CONSTRAINT IF EXISTS emergency_location_accuracy_range;"
        ),
        migrations.RunSQL(
            "ALTER TABLE panic_emergency_location ADD CONSTRAINT emergency_location_battery_range CHECK (battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100));",
            reverse_sql="ALTER TABLE panic_emergency_location DROP CONSTRAINT IF EXISTS emergency_location_battery_range;"
        ),
        migrations.RunSQL(
            "ALTER TABLE panic_emergency_zone ADD CONSTRAINT emergency_zone_priority_positive CHECK (priority > 0);",
            reverse_sql="ALTER TABLE panic_emergency_zone DROP CONSTRAINT IF EXISTS emergency_zone_priority_positive;"
        ),
        migrations.RunSQL(
            "ALTER TABLE panic_emergency_medical ADD CONSTRAINT emergency_medical_consent_expiry_valid CHECK (consent_expires_at IS NULL OR consent_given_at IS NULL OR consent_expires_at > consent_given_at);",
            reverse_sql="ALTER TABLE panic_emergency_medical DROP CONSTRAINT IF EXISTS emergency_medical_consent_expiry_valid;"
        ),
    ]
