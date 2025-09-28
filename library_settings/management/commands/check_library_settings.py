"""
Management command to check the current library settings and their status.
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from library_settings.models import (
    LibrarySettings, LibraryBranch, LibraryPolicy, 
    FineRate, NotificationTemplate
)
from library_settings.utils import get_active_settings


class Command(BaseCommand):
    help = 'Check the current library settings and their status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Library Settings Status'))
        self.stdout.write('=' * 50 + '\n')
        
        # Check branches
        self.stdout.write(self.style.MIGRATE_LABEL('Library Branches:'))
        branches = LibraryBranch.objects.all()
        if not branches.exists():
            self.stdout.write(self.style.WARNING('  No library branches found'))
        else:
            for branch in branches:
                status = self.style.SUCCESS('ACTIVE') if branch.is_active else self.style.ERROR('INACTIVE')
                self.stdout.write(f'  {branch.name} ({branch.code}) - {status}')
        
        # Check policies
        self.stdout.write('\n' + self.style.MIGRATE_LABEL('Library Policies:'))
        policies = LibraryPolicy.objects.all()
        if not policies.exists():
            self.stdout.write(self.style.WARNING('  No library policies found'))
        else:
            for policy in policies:
                status = self.style.SUCCESS('ACTIVE') if policy.is_active else self.style.ERROR('INACTIVE')
                self.stdout.write(f'  {policy.name} - {status}')
                self.stdout.write(f'    Type: {policy.policy_type}, ' \
                               f'Description: {policy.description}')
        
        # Check fine rates
        self.stdout.write('\n' + self.style.MIGRATE_LABEL('Fine Rates:'))
        fine_rates = FineRate.objects.all()
        if not fine_rates.exists():
            self.stdout.write(self.style.WARNING('  No fine rates found'))
        else:
            for rate in fine_rates:
                status = self.style.SUCCESS('ACTIVE') if rate.is_active else self.style.ERROR('INACTIVE')
                self.stdout.write(f'  {rate.name} - {rate.get_violation_type_display()}: ${rate.rate}/{rate.rate_type} - {status}')
                if rate.max_fine is not None:
                    self.stdout.write(f'    Max Fine: ${rate.max_fine}')
        
        # Check notification templates
        self.stdout.write('\n' + self.style.MIGRATE_LABEL('Notification Templates:'))
        templates = NotificationTemplate.objects.all()
        if not templates.exists():
            self.stdout.write(self.style.WARNING('  No notification templates found'))
        else:
            for template in templates:
                status = self.style.SUCCESS('ACTIVE') if template.is_active else self.style.ERROR('INACTIVE')
                self.stdout.write(f'  {template.name} - {status}')
                self.stdout.write(f'    Type: {template.notification_type}, Subject: {template.subject}')
        
        # Check active settings
        self.stdout.write('\n' + self.style.MIGRATE_LABEL('Active Settings:'))
        active_settings = get_active_settings()
        if not active_settings:
            self.stdout.write(self.style.ERROR('  No active library settings found'))
        else:
            self.stdout.write(f'  Branch: {active_settings.branch_name or "Not specified"}')
            self.stdout.write(f'  Address: {active_settings.branch_address or "Not specified"}')
            self.stdout.write(f'  Max Borrow Days: {active_settings.max_borrow_days}')
            self.stdout.write(f'  Fine Per Day: ${active_settings.fine_per_day}')
            self.stdout.write(f'  Max Renewals: {active_settings.max_renewals}')
            self.stdout.write(f'  Allow Reservation: {"Yes" if active_settings.allow_reservation else "No"}')
        
        # Check required settings
        self.stdout.write('\n' + self.style.MIGRATE_LABEL('Configuration Check:'))
        self._check_required_settings()
    
    def _check_required_settings(self):
        """Check if all required settings are properly configured."""
        issues = []
        
        # Check if there's at least one active branch
        if not LibraryBranch.objects.filter(is_active=True).exists():
            issues.append('No active library branch found')
        
        # Check if there's at least one active policy
        if not LibraryPolicy.objects.filter(is_active=True).exists():
            issues.append('No active library policy found')
        
        # Check if there are fine rates defined
        if not FineRate.objects.filter(is_active=True).exists():
            issues.append('No active fine rates found')
        
        # Check if there are notification templates defined
        if not NotificationTemplate.objects.filter(is_active=True).exists():
            issues.append('No active notification templates found')
        
        # Check if there are any library settings
        if not LibrarySettings.objects.exists():
            issues.append('No library settings found')
        
        if issues:
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  ✗ {issue}'))
            self.stdout.write('\n' + self.style.WARNING('Run `python manage.py init_library_settings` to set up default settings'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All required settings are properly configured'))
        
        return not bool(issues)
