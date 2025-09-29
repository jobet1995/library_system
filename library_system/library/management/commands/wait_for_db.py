import time
import os
import psycopg2
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        max_retries = 30
        retry_delay = 2  # seconds

        db_params = {
            'dbname': os.environ.get('POSTGRES_DB', os.environ.get('DB_NAME', 'library_db')),
            'user': os.environ.get('POSTGRES_USER', os.environ.get('DB_USER', 'library_user')),
            'password': os.environ.get('POSTGRES_PASSWORD', os.environ.get('DB_PASSWORD', 'library_password')),
            'host': os.environ.get('POSTGRES_HOST', os.environ.get('DB_HOST', 'db')),
            'port': os.environ.get('POSTGRES_PORT', os.environ.get('DB_PORT', '5432')),
            'connect_timeout': 5
        }

        for i in range(max_retries):
            try:
                self.stdout.write(f"Attempting to connect to database: host={db_params['host']}, dbname={db_params['dbname']}, user={db_params['user']}")
                conn = psycopg2.connect(**db_params)
                conn.close()
                self.stdout.write(self.style.SUCCESS('Database is available!'))
                return
            except psycopg2.OperationalError as e:
                if i == max_retries - 1:
                    self.stdout.write(self.style.ERROR('Database connection failed after maximum retries'))
                    self.stdout.write(self.style.ERROR(f'Error: {e}'))
                    self.stdout.write(self.style.ERROR(f'Connection parameters: {db_params}'))
                    raise
                self.stdout.write(f'Database unavailable, waiting {retry_delay} second(s)... (attempt {i + 1}/{max_retries})')
                time.sleep(retry_delay)
