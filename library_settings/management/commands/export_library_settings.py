"""
Management command to export library settings to a JSON file.
"""
import json
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from library_settings.models import (
    LibrarySettings, LibraryBranch, LibraryPolicy, 
    FineRate, NotificationTemplate
)


class Command(BaseCommand):
    help = 'Export library settings to a JSON file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output', 
            type=str,
            default=None,
            help='Output file path (default: library_settings_export_<timestamp>.json)'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'library_settings_export_{timestamp}.json'
        
        self.stdout.write(f'Exporting library settings to {output_path}...')
        
        # Prepare data for export
        export_data = {
            'meta': {
                'exported_at': datetime.now().isoformat(),
                'version': '1.0',
            },
            'branches': [],
            'policies': [],
            'fine_rates': [],
            'notification_templates': [],
            'settings': [],
        }
        
        # Export branches
        for branch in LibraryBranch.objects.all():
            export_data['branches'].append({
                'name': branch.name,
                'code': branch.code,
                'address': branch.address,
                'phone': branch.phone,
                'email': branch.email,
                'opening_hours': branch.opening_hours,
                'is_active': branch.is_active,
            })
        
        # Export policies
        for policy in LibraryPolicy.objects.all():
            export_data['policies'].append({
                'name': policy.name,
                'policy_type': policy.policy_type,
                'description': policy.description,
                'is_active': policy.is_active,
                'created_at': policy.created_at.isoformat(),
                'updated_at': policy.updated_at.isoformat()
            })
        
        # Export fine rates
        for rate in FineRate.objects.all():
            export_data['fine_rates'].append({
                'name': rate.name,
                'violation_type': rate.violation_type,
                'rate': str(rate.rate),  # Convert Decimal to string
                'rate_type': rate.rate_type,
                'max_fine': str(rate.max_fine) if rate.max_fine is not None else None,
                'is_active': rate.is_active,
                'created_at': rate.created_at.isoformat(),
                'updated_at': rate.updated_at.isoformat()
            })
        
        # Export notification templates
        for template in NotificationTemplate.objects.all():
            export_data['notification_templates'].append({
                'name': template.name,
                'notification_type': template.notification_type,
                'subject': template.subject,
                'body': template.body,
                'is_active': template.is_active,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat()
            })
        
        # Export settings
        for setting in LibrarySettings.objects.all():
            export_data['settings'].append({
                'branch_name': setting.branch_name,
                'branch_address': setting.branch_address,
                'max_borrow_days': setting.max_borrow_days,
                'fine_per_day': str(setting.fine_per_day),
                'max_renewals': setting.max_renewals,
                'allow_reservation': setting.allow_reservation,
                'created_at': setting.created_at.isoformat(),
                'updated_at': setting.updated_at.isoformat()
            })
        
        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully exported settings to {output_path}'))
