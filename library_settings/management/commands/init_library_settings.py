"""
Management command to initialize library settings with default values.
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from library_settings.models import LibrarySettings, LibraryBranch, LibraryPolicy, FineRate, NotificationTemplate
from library_settings.utils import clear_all_caches


class Command(BaseCommand):
    help = 'Initialize library settings with default values'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing library settings...'))
        
        # Create default branch if none exists
        branch, created = LibraryBranch.objects.get_or_create(
            name='Main Branch',
            defaults={
                'code': 'MAIN',
                'address': '123 Library St, City, Country',
                'phone': '+1234567890',
                'email': 'info@library.example.com',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created default library branch'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing library branch'))
        
        # Create borrowing policy
        borrowing_policy, created = LibraryPolicy.objects.get_or_create(
            name='Standard Borrowing',
            policy_type='borrowing',
            defaults={
                'description': 'Standard borrowing policy with 2-week loan period',
                'is_active': True,
            }
        )
        
        # Create reservation policy
        reservation_policy, created = LibraryPolicy.objects.get_or_create(
            name='Book Reservation',
            policy_type='reservation',
            defaults={
                'description': 'Policy for reserving books that are currently checked out',
                'is_active': True,
            }
        )
        
        # Create membership policy
        membership_policy, created = LibraryPolicy.objects.get_or_create(
            name='Membership Terms',
            policy_type='membership',
            defaults={
                'description': 'Terms and conditions for library membership',
                'is_active': True,
            }
        )
        
        # Create fines policy
        fines_policy, created = LibraryPolicy.objects.get_or_create(
            name='Fines and Fees',
            policy_type='fines',
            defaults={
                'description': 'Policy regarding late returns, lost items, and other fines',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created default library policies'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing library policies'))
        
        # Create default fine rates
        fine_rates = [
            {
                'name': 'Overdue Book',
                'violation_type': 'overdue', 
                'rate': 0.50,
                'rate_type': 'daily',
                'max_fine': 25.00,
                'is_active': True
            },
            {
                'name': 'Damaged Book',
                'violation_type': 'damaged', 
                'rate': 10.00,
                'rate_type': 'fixed',
                'max_fine': None,
                'is_active': True
            },
            {
                'name': 'Lost Book',
                'violation_type': 'lost', 
                'rate': 25.00,
                'rate_type': 'fixed',
                'max_fine': None,
                'is_active': True
            },
            {
                'name': 'Overdue Media',
                'violation_type': 'overdue', 
                'rate': 1.00,
                'rate_type': 'daily',
                'max_fine': 50.00,
                'is_active': True
            },
        ]
        
        created_count = 0
        for rate_data in fine_rates:
            _, created = FineRate.objects.get_or_create(
                violation_type=rate_data['violation_type'],
                defaults=rate_data
            )
            if created:
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} fine rates'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing fine rates'))
        
        # Create notification templates
        templates = [
            {
                'name': 'Checkout Confirmation',
                'notification_type': 'checkout',
                'subject': 'Book Checkout Confirmation',
                'body': 'Hello {{user.first_name}},\n\nYou have successfully checked out the following book(s):\n{% for book in books %}- {{book.title}} (Due: {{book.due_date|date:"F j, Y"}})\n{% endfor %}\n\nThank you for using our library!',
                'is_active': True
            },
            {
                'name': 'Due Date Reminder',
                'notification_type': 'due_soon',
                'subject': 'Upcoming Book Due Date',
                'body': 'Hello {{user.first_name}},\n\nThe following book(s) are due soon:\n{% for book in books %}- {{book.title}} (Due: {{book.due_date|date:"F j, Y"}})\n{% endfor %}\n\nPlease return or renew them to avoid late fees.',
                'is_active': True
            },
            {
                'name': 'Overdue Notice',
                'notification_type': 'overdue',
                'subject': 'Overdue Book Notice',
                'body': 'Hello {{user.first_name}},\n\nThe following book(s) are overdue:\n{% for book in books %}- {{book.title}} (Due: {{book.due_date|date:"F j, Y"}})\n{% endfor %}\n\nPlease return them as soon as possible to avoid additional fines.',
                'is_active': True
            },
            {
                'name': 'Welcome Email',
                'notification_type': 'welcome',
                'subject': 'Welcome to Our Library!',
                'body': 'Hello {{user.first_name}},\n\nWelcome to our library! We\'re excited to have you as a member.\n\nYour membership details:\n- Member ID: {{user.member_id}}\n- Membership Type: {{user.membership_type}}\n- Expiration Date: {{user.membership_expiry|date:"F j, Y"}}\n\nIf you have any questions, please don\'t hesitate to contact us.',
                'is_active': True
            },
        ]
        
        created_count = 0
        for template_data in templates:
            _, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                notification_type=template_data['notification_type'],
                defaults={
                    'subject': template_data['subject'],
                    'body': template_data['body'],
                    'is_active': template_data.get('is_active', True)
                }
            )
            if created:
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} notification templates'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing notification templates'))
        
        # Create or update library settings
        settings_obj, created = LibrarySettings.objects.get_or_create(
            branch_name=branch.name,
            defaults={
                'branch_address': branch.address,
                'max_borrow_days': 14,
                'fine_per_day': 0.50,
                'max_renewals': 2,
                'allow_reservation': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created library settings'))
        else:
            self.stdout.write(self.style.SUCCESS('Using existing library settings'))
        
        # Clear all caches
        clear_all_caches()
        self.stdout.write(self.style.SUCCESS('Successfully initialized library settings'))
