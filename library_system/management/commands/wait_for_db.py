import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import psycopg2
import os

class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        max_retries = 30
        retry_delay = 2  # seconds

        for i in range(max_retries):
            try:
                conn = psycopg2.connect(
                    dbname=os.environ.get('DB_NAME', 'library_db'),
                    user=os.environ.get('DB_USER', 'library_user'),
                    password=os.environ.get('DB_PASSWORD', 'library_password'),
                    host=os.environ.get('DB_HOST', 'db'),
                    port=os.environ.get('DB_PORT', '5432')
                )
                conn.close()
                self.stdout.write(self.style.SUCCESS('Database is available!'))
                return
            except psycopg2.OperationalError as e:
                if i == max_retries - 1:
                    self.stdout.write(self.style.ERROR('Database connection failed after maximum retries'))
                    self.stdout.write(self.style.ERROR(f'Error: {e}'))
                    raise
                self.stdout.write(f'Database unavailable, waiting {retry_delay} second(s)... (attempt {i + 1}/{max_retries})')
                time.sleep(retry_delay)
