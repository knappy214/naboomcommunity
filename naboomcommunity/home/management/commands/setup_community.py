from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from home.utils import create_default_groups_and_roles
from home.models import UserGroup, UserRole


class Command(BaseCommand):
    """
    Django management command to set up the initial community structure.
    Creates default user groups, roles, and optionally a superuser.
    """
    
    help = 'Set up initial community structure with default groups and roles'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser account',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for superuser (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@naboomcommunity.co.za',
            help='Email for superuser (default: admin@naboomcommunity.co.za)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for superuser (default: admin123)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Naboom Community structure...')
        )
        
        # Create default groups and roles
        self.stdout.write('Creating default groups and roles...')
        try:
            created_data = create_default_groups_and_roles()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {len(created_data["roles"])} roles and '
                    f'{len(created_data["groups"])} groups'
                )
            )
            
            # Display created roles
            self.stdout.write('\nCreated Roles:')
            for role_name, role in created_data['roles'].items():
                self.stdout.write(f'  - {role_name}: {role.description}')
            
            # Display created groups
            self.stdout.write('\nCreated Groups:')
            for group_name, group in created_data['groups'].items():
                self.stdout.write(f'  - {group_name}: {group.description}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating groups and roles: {e}')
            )
            return
        
        # Create superuser if requested
        if options['create_superuser']:
            self.stdout.write('\nCreating superuser...')
            try:
                if User.objects.filter(username=options['username']).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'User "{options["username"]}" already exists. Skipping superuser creation.'
                        )
                    )
                else:
                    superuser = User.objects.create_superuser(
                        username=options['username'],
                        email=options['email'],
                        password=options['password']
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Superuser "{superuser.username}" created successfully!'
                        )
                    )
                    self.stdout.write(
                        f'  Username: {superuser.username}'
                    )
                    self.stdout.write(
                        f'  Email: {superuser.email}'
                    )
                    self.stdout.write(
                        f'  Password: {options["password"]}'
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating superuser: {e}')
                )
        
        # Display summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS('Community setup completed successfully!')
        )
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run migrations: python manage.py migrate')
        self.stdout.write('2. Create a superuser: python manage.py createsuperuser')
        self.stdout.write('3. Access admin at: /admin/')
        self.stdout.write('4. Start adding community members!')
        self.stdout.write('='*50)
