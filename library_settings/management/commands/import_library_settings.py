"""
Management command to import library settings from a JSON file.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from library_settings.models import (
    LibrarySettings, LibraryBranch, LibraryPolicy, 
    FineRate, NotificationTemplate
)
from library_settings.utils import clear_all_caches


class Command(BaseCommand):
    help = 'Import library settings from a JSON file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'input_file', 
            type=str,
            help='Input JSON file path containing the settings to import'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing records instead of skipping them'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the import without making any changes'
        )

    def handle(self, *args, **options):
        input_file = Path(options['input_file'])
        update = options['update']
        dry_run = options['dry_run']
        
        if not input_file.exists():
            raise CommandError(f'Input file not found: {input_file}')
        
        self.stdout.write(f'Importing library settings from {input_file}...')
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON file: {e}')
        
        stats = {
            'branches': {'created': 0, 'updated': 0, 'skipped': 0},
            'policies': {'created': 0, 'updated': 0, 'skipped': 0},
            'fine_rates': {'created': 0, 'updated': 0, 'skipped': 0},
            'templates': {'created': 0, 'updated': 0, 'skipped': 0},
            'settings': {'created': 0, 'updated': 0, 'skipped': 0},
        }
        
        try:
            with transaction.atomic():
                # Import branches
                for branch_data in import_data.get('branches', []):
                    code = branch_data.get('code')
                    if not code:
                        self.stderr.write(self.style.WARNING('Skipping branch without code'))
                        continue
                        
                    branch, created = self._import_branch(branch_data, update, dry_run)
                    if created:
                        stats['branches']['created'] += 1
                    elif branch:
                        stats['branches']['updated'] += 1
                    else:
                        stats['branches']['skipped'] += 1
                
                # Import policies
                for policy_data in import_data.get('policies', []):
                    name = policy_data.get('name')
                    if not name:
                        self.stderr.write(self.style.WARNING('Skipping policy without name'))
                        continue
                        
                    policy, created = self._import_policy(policy_data, update, dry_run)
                    if created:
                        stats['policies']['created'] += 1
                    elif policy:
                        stats['policies']['updated'] += 1
                    else:
                        stats['policies']['skipped'] += 1
                
                # Import fine rates
                for rate_data in import_data.get('fine_rates', []):
                    violation_type = rate_data.get('violation_type')
                    if not violation_type:
                        self.stderr.write(self.style.WARNING('Skipping fine rate without violation type'))
                        continue
                        
                    rate, created = self._import_fine_rate(rate_data, update, dry_run)
                    if created:
                        stats['fine_rates']['created'] += 1
                    elif rate:
                        stats['fine_rates']['updated'] += 1
                    else:
                        stats['fine_rates']['skipped'] += 1
                
                # Import notification templates
                for template_data in import_data.get('notification_templates', []):
                    name = template_data.get('name')
                    if not name:
                        self.stderr.write(self.style.WARNING('Skipping template without name'))
                        continue
                        
                    template, created = self._import_template(template_data, update, dry_run)
                    if created:
                        stats['templates']['created'] += 1
                    elif template:
                        stats['templates']['updated'] += 1
                    else:
                        stats['templates']['skipped'] += 1
                
                # Import settings
                for setting_data in import_data.get('settings', []):
                    branch_code = setting_data.get('branch')
                    if not branch_code:
                        self.stderr.write(self.style.WARNING('Skipping setting without branch'))
                        continue
                        
                    setting, created = self._import_setting(setting_data, update, dry_run)
                    if created:
                        stats['settings']['created'] += 1
                    elif setting:
                        stats['settings']['updated'] += 1
                    else:
                        stats['settings']['skipped'] += 1
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('Dry run - no changes were made'))
                    transaction.set_rollback(True)
                else:
                    # Clear all caches after import
                    clear_all_caches()
        
        except Exception as e:
            raise CommandError(f'Error during import: {e}')
        
        # Print import statistics
        self.stdout.write(self.style.SUCCESS('\nImport Statistics:'))
        for model, counts in stats.items():
            self.stdout.write(f'\n{model.title()}:')
            for action, count in counts.items():
                self.stdout.write(f'  {action.title()}: {count}')
        
        self.stdout.write(self.style.SUCCESS('\nImport completed successfully'))
    
    def _import_branch(self, data, update, dry_run):
        code = data.get('code')
        try:
            branch = LibraryBranch.objects.get(code=code)
            if not update:
                return None, False
                
            if not dry_run:
                for field, value in data.items():
                    setattr(branch, field, value)
                branch.save()
            return branch, False
                
        except LibraryBranch.DoesNotExist:
            if not dry_run:
                branch = LibraryBranch.objects.create(**data)
                return branch, True
            return None, True
    
    def _import_policy(self, data, update, dry_run):
        name = data.get('name')
        try:
            policy = LibraryPolicy.objects.get(name=name)
            if not update:
                return None, False
                
            if not dry_run:
                for field, value in data.items():
                    setattr(policy, field, value)
                policy.save()
            return policy, False
                
        except LibraryPolicy.DoesNotExist:
            if not dry_run:
                policy = LibraryPolicy.objects.create(**data)
                return policy, True
            return None, True
    
    def _import_fine_rate(self, data, update, dry_run):
        violation_type = data.get('violation_type')
        try:
            rate = FineRate.objects.get(violation_type=violation_type)
            if not update:
                return None, False
                
            if not dry_run:
                for field, value in data.items():
                    setattr(rate, field, value)
                rate.save()
            return rate, False
                
        except FineRate.DoesNotExist:
            if not dry_run:
                rate = FineRate.objects.create(**data)
                return rate, True
            return None, True
    
    def _import_template(self, data, update, dry_run):
        name = data.get('name')
        try:
            template = NotificationTemplate.objects.get(name=name)
            if not update:
                return None, False
                
            if not dry_run:
                for field, value in data.items():
                    setattr(template, field, value)
                template.save()
            return template, False
                
        except NotificationTemplate.DoesNotExist:
            if not dry_run:
                template = NotificationTemplate.objects.create(**data)
                return template, True
            return None, True
    
    def _import_setting(self, data, update, dry_run):
        branch_code = data.pop('branch', None)
        policy_name = data.pop('policy', None)
        
        if not branch_code:
            return None, False
            
        try:
            branch = LibraryBranch.objects.get(code=branch_code)
            policy = LibraryPolicy.objects.get(name=policy_name) if policy_name else None
            
            try:
                setting = LibrarySettings.objects.get(branch=branch)
                if not update:
                    return None, False
                    
                if not dry_run:
                    setting.policy = policy
                    for field, value in data.items():
                        setattr(setting, field, value)
                    setting.save()
                return setting, False
                    
            except LibrarySettings.DoesNotExist:
                if not dry_run:
                    setting = LibrarySettings.objects.create(
                        branch=branch,
                        policy=policy,
                        **data
                    )
                    return setting, True
                return None, True
                
        except (LibraryBranch.DoesNotExist, LibraryPolicy.DoesNotExist) as e:
            self.stderr.write(self.style.WARNING(f'Skipping setting - {e}'))
            return None, False
