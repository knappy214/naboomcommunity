from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from home.models import UserGroup, UserRole, UserGroupMembership

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up sample data for user groups and roles'

    def handle(self, *args, **options):
        """Create sample user groups and roles."""
        
        # Create sample user groups
        groups_data = [
            {
                'name': 'Members',
                'description': 'General community members',
                'is_active': True
            },
            {
                'name': 'Choir',
                'description': 'Community choir group',
                'is_active': True
            },
            {
                'name': 'Youth',
                'description': 'Youth group for ages 13-25',
                'is_active': True
            },
            {
                'name': 'Elders',
                'description': 'Elderly community members group',
                'is_active': True
            },
            {
                'name': 'Tech Support',
                'description': 'Technical support volunteers',
                'is_active': True
            },
            {
                'name': 'Event Organizers',
                'description': 'Community event organizers',
                'is_active': True
            }
        ]
        
        for group_data in groups_data:
            group, created = UserGroup.objects.get_or_create(
                name=group_data['name'],
                defaults=group_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Group already exists: {group.name}')
                )
        
        # Create sample user roles
        roles_data = [
            {
                'name': 'Member',
                'description': 'Basic member role',
                'permissions': {},
                'is_active': True
            },
            {
                'name': 'Leader',
                'description': 'Group leader role',
                'permissions': {
                    'can_manage_members': True,
                    'can_organize_events': True
                },
                'is_active': True
            },
            {
                'name': 'Moderator',
                'description': 'Group moderator role',
                'permissions': {
                    'can_moderate_content': True,
                    'can_manage_events': True
                },
                'is_active': True
            },
            {
                'name': 'Coordinator',
                'description': 'Event coordinator role',
                'permissions': {
                    'can_organize_events': True,
                    'can_manage_resources': True
                },
                'is_active': True
            }
        ]
        
        for role_data in roles_data:
            role, created = UserRole.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Role already exists: {role.name}')
                )
        
        # Create a sample user if none exists
        if not User.objects.exists():
            user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: {user.username}')
            )
        
        # Assign default role to all existing users
        default_group = UserGroup.objects.get(name='Members')
        default_role = UserRole.objects.get(name='Member')
        
        for user in User.objects.all():
            membership, created = UserGroupMembership.objects.get_or_create(
                user=user,
                group=default_group,
                defaults={'role': default_role}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned {user.username} to {default_group.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Sample data setup completed successfully!')
        )
