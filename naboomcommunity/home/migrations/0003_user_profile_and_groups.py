from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('home', '0002_create_homepage'),
    ]

    operations = [
        # Create UserProfile model
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, help_text='Contact phone number', max_length=20)),
                ('date_of_birth', models.DateField(blank=True, help_text="User's date of birth", null=True)),
                ('gender', models.CharField(blank=True, help_text="User's gender identity", max_length=20)),
                ('address', models.TextField(blank=True, help_text='Full residential address')),
                ('city', models.CharField(blank=True, help_text='City of residence', max_length=100)),
                ('province', models.CharField(blank=True, help_text='Province/State of residence', max_length=100)),
                ('postal_code', models.CharField(blank=True, help_text='Postal/ZIP code', max_length=20)),
                ('allergies', models.TextField(blank=True, help_text='Known allergies and sensitivities')),
                ('medical_conditions', models.TextField(blank=True, help_text='Current medical conditions')),
                ('current_medications', models.TextField(blank=True, help_text='Currently prescribed medications')),
                ('emergency_contact_name', models.CharField(blank=True, help_text="Emergency contact person's name", max_length=255)),
                ('emergency_contact_phone', models.CharField(blank=True, help_text='Emergency contact phone number', max_length=20)),
                ('emergency_contact_relationship', models.CharField(blank=True, help_text='Relationship to emergency contact', max_length=100)),
                ('preferred_language', models.CharField(choices=[('en', 'English'), ('af', 'Afrikaans')], default='en', help_text='Preferred language for communications', max_length=10)),
                ('timezone', models.CharField(default='UTC', help_text="User's timezone", max_length=50)),
                ('email_notifications', models.BooleanField(default=True, help_text='Receive email notifications')),
                ('sms_notifications', models.BooleanField(default=False, help_text='Receive SMS notifications')),
                ('mfa_enabled', models.BooleanField(default=False, help_text='Multi-factor authentication enabled')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
                'db_table': 'user_profile',
            },
        ),
        
        # Create UserGroup model
        migrations.CreateModel(
            name='UserGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the user group', max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text="Description of the group's purpose")),
                ('is_active', models.BooleanField(default=True, help_text='Whether the group is currently active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'user_group',
                'ordering': ['name'],
            },
        ),
        
        # Create UserRole model
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the role', max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text="Description of the role's responsibilities")),
                ('permissions', models.JSONField(default=dict, help_text='JSON object defining role permissions')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the role is currently active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'user_role',
                'ordering': ['name'],
            },
        ),
        
        # Create UserGroupMembership model
        migrations.CreateModel(
            name='UserGroupMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True, help_text='When the user joined the group')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the membership is currently active')),
                ('notes', models.TextField(blank=True, help_text='Additional notes about the membership')),
                ('group', models.ForeignKey(help_text='Group the user belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='members', to='home.usergroup')),
                ('role', models.ForeignKey(help_text='Role the user has in the group', on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='home.userrole')),
                ('user', models.ForeignKey(help_text='User who is a member of the group', on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to='auth.user')),
            ],
            options={
                'db_table': 'user_group_membership',
                'unique_together': {('user', 'group')},
                'ordering': ['-joined_at'],
            },
        ),
    ]
