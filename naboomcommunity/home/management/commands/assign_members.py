from django.core.management.base import BaseCommand
from home.utils import assign_existing_users_to_member_group


class Command(BaseCommand):
    """
    Django management command to assign existing users to the Member group.
    This is useful for migrating existing users to the new group system.
    """
    
    help = 'Assign existing users to the Member group with Member role'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Assigning existing users to Member group...')
        )
        
        try:
            assigned_count = assign_existing_users_to_member_group()
            
            if assigned_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully assigned {assigned_count} users to the Member group!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'No users were assigned. All users may already have group memberships.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error assigning users to Member group: {e}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('User assignment completed!')
        )
