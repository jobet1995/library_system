"""
Management command to clear all library-related caches.
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from library_settings.utils import clear_all_caches


class Command(BaseCommand):
    help = 'Clear all library-related caches'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about the caches being cleared'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write('Clearing library caches...')
            self.stdout.write('  - Library settings cache')
            self.stdout.write('  - Library branches cache')
            self.stdout.write('  - Fine rates cache')
            self.stdout.write('  - Notification templates cache')
            self.stdout.write('  - All library caches')
        
        clear_all_caches()
        
        if verbose:
            self.stdout.write('\n' + self.style.SUCCESS('Successfully cleared all library caches'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully cleared all library caches'))
