"""
Emergency Authentication and Permissions Migration
Creates emergency-specific authentication and permissions system.
"""

from django.db import migrations, models
import django.core.validators
import uuid


class Migration(migrations.Migration):
    """
    Emergency Authentication and Permissions Migration
    
    Creates the emergency authentication and permissions models:
    - EmergencyPermission: Custom emergency response permissions
    - EmergencyUserPermission: User-specific emergency permissions
    - EmergencyRole: Emergency response roles
    - EmergencyUserRole: User roles in emergency system
    - EmergencyAccessLog: Access attempt logging
    """
    
    dependencies = [
        ('panic', '0004_emergency_foundation'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        # Create EmergencyPermission model
        migrations.CreateModel(
            name='EmergencyPermission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('permission_type', models.CharField(choices=[('panic_activate', 'Activate Panic Button'), ('location_access', 'Access Location Data'), ('medical_access', 'Access Medical Data'), ('notification_send', 'Send Notifications'), ('responder_assign', 'Assign Responders'), ('audit_view', 'View Audit Logs'), ('admin_override', 'Admin Override'), ('offline_sync', 'Offline Data Sync'), ('websocket_connect', 'WebSocket Connection'), ('external_api', 'External API Access')], max_length=50)),
                ('scope_level', models.CharField(choices=[('own', 'Own Data Only'), ('family', 'Family Members'), ('neighborhood', 'Neighborhood'), ('zone', 'Emergency Zone'), ('global', 'Global Access')], default='own', max_length=20)),
                ('requires_consent', models.BooleanField(default=True)),
                ('requires_verification', models.BooleanField(default=False)),
                ('emergency_only', models.BooleanField(default=False)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Permission',
                'verbose_name_plural': 'Emergency Permissions',
                'db_table': 'panic_emergency_permission',
                'ordering': ['permission_type', 'scope_level'],
            },
        ),
        
        # Create EmergencyUserPermission model
        migrations.CreateModel(
            name='EmergencyUserPermission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('override_consent', models.BooleanField(default=False)),
                ('override_verification', models.BooleanField(default=False)),
                ('emergency_override', models.BooleanField(default=False)),
                ('context_data', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='granted_permissions', to='auth.user')),
                ('permission', models.ForeignKey(on_delete=models.CASCADE, to='panic.emergencypermission')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='emergency_permissions', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency User Permission',
                'verbose_name_plural': 'Emergency User Permissions',
                'db_table': 'panic_emergency_user_permission',
            },
        ),
        
        # Create EmergencyRole model
        migrations.CreateModel(
            name='EmergencyRole',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('role_type', models.CharField(choices=[('citizen', 'Citizen'), ('responder', 'Emergency Responder'), ('coordinator', 'Emergency Coordinator'), ('admin', 'Emergency Administrator'), ('medical', 'Medical Professional'), ('security', 'Security Personnel'), ('family', 'Family Member')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('is_default', models.BooleanField(default=False)),
                ('requires_verification', models.BooleanField(default=False)),
                ('emergency_priority', models.IntegerField(default=1, help_text='Priority level (1=highest)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Role',
                'verbose_name_plural': 'Emergency Roles',
                'db_table': 'panic_emergency_role',
                'ordering': ['emergency_priority', 'name'],
            },
        ),
        
        # Create EmergencyUserRole model
        migrations.CreateModel(
            name='EmergencyUserRole',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('context_data', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='assigned_roles', to='auth.user')),
                ('role', models.ForeignKey(on_delete=models.CASCADE, to='panic.emergencyrole')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='emergency_roles', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency User Role',
                'verbose_name_plural': 'Emergency User Roles',
                'db_table': 'panic_emergency_user_role',
            },
        ),
        
        # Create EmergencyAccessLog model
        migrations.CreateModel(
            name='EmergencyAccessLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('access_type', models.CharField(choices=[('granted', 'Access Granted'), ('denied', 'Access Denied'), ('expired', 'Permission Expired'), ('insufficient', 'Insufficient Permissions'), ('consent_required', 'Consent Required'), ('verification_required', 'Verification Required')], max_length=20)),
                ('resource_type', models.CharField(max_length=100)),
                ('resource_id', models.UUIDField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('session_id', models.CharField(blank=True, max_length=255)),
                ('context_data', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('permission', models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to='panic.emergencypermission')),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='emergency_access_logs', to='auth.user')),
            ],
            options={
                'verbose_name': 'Emergency Access Log',
                'verbose_name_plural': 'Emergency Access Logs',
                'db_table': 'panic_emergency_access_log',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add many-to-many relationship for EmergencyRole permissions
        migrations.AddField(
            model_name='emergencyrole',
            name='permissions',
            field=models.ManyToManyField(blank=True, related_name='roles', to='panic.emergencypermission'),
        ),
        
        # Add constraints
        migrations.AddConstraint(
            model_name='emergencyuserpermission',
            constraint=models.UniqueConstraint(fields=['user', 'permission'], name='emergency_user_permission_unique'),
        ),
        migrations.AddConstraint(
            model_name='emergencyuserrole',
            constraint=models.UniqueConstraint(fields=['user', 'role'], name='emergency_user_role_unique'),
        ),
        migrations.AddConstraint(
            model_name='emergencyrole',
            constraint=models.CheckConstraint(check=models.Q(('emergency_priority__gt', 0)), name='emergency_role_priority_positive'),
        ),
        
        # Add indexes
        migrations.RunSQL(
            "CREATE INDEX emergency_permission_type_active_idx ON panic_emergency_permission (permission_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_permission_type_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_permission_scope_idx ON panic_emergency_permission (scope_level);",
            reverse_sql="DROP INDEX IF EXISTS emergency_permission_scope_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_permission_validity_idx ON panic_emergency_permission (valid_until);",
            reverse_sql="DROP INDEX IF EXISTS emergency_permission_validity_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_permission_user_perm_idx ON panic_emergency_user_permission (user_id, permission_id);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_permission_user_perm_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_permission_user_active_idx ON panic_emergency_user_permission (user_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_permission_user_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_permission_expiry_idx ON panic_emergency_user_permission (expires_at);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_permission_expiry_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_permission_perm_active_idx ON panic_emergency_user_permission (permission_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_permission_perm_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_role_type_idx ON panic_emergency_role (role_type);",
            reverse_sql="DROP INDEX IF EXISTS emergency_role_type_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_role_default_idx ON panic_emergency_role (is_default);",
            reverse_sql="DROP INDEX IF EXISTS emergency_role_default_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_role_priority_idx ON panic_emergency_role (emergency_priority);",
            reverse_sql="DROP INDEX IF EXISTS emergency_role_priority_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_role_user_role_idx ON panic_emergency_user_role (user_id, role_id);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_role_user_role_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_role_user_active_idx ON panic_emergency_user_role (user_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_role_user_active_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_user_role_expiry_idx ON panic_emergency_user_role (expires_at);",
            reverse_sql="DROP INDEX IF EXISTS emergency_user_role_expiry_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_access_log_user_timestamp_idx ON panic_emergency_access_log (user_id, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_access_log_user_timestamp_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_access_log_type_timestamp_idx ON panic_emergency_access_log (access_type, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_access_log_type_timestamp_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_access_log_resource_idx ON panic_emergency_access_log (resource_type, resource_id);",
            reverse_sql="DROP INDEX IF EXISTS emergency_access_log_resource_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX emergency_access_log_ip_timestamp_idx ON panic_emergency_access_log (ip_address, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS emergency_access_log_ip_timestamp_idx;"
        ),
    ]
