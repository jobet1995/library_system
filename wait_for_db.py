import time
import os
import sys
import psycopg2
from django.db import connections
from django.db.utils import OperationalError

def wait_for_db():
    """Wait for PostgreSQL to be available."""
    max_retries = 30
    retry_delay = 2  # seconds

    for i in range(max_retries):
        try:
            # Try to connect to the database
            conn = psycopg2.connect(
                dbname=os.environ.get('DB_NAME', 'library_db'),
                user=os.environ.get('DB_USER', 'library_user'),
                password=os.environ.get('DB_PASSWORD', 'library_password'),
                host=os.environ.get('DB_HOST', 'db'),
                port=os.environ.get('DB_PORT', '5432')
            )
            conn.close()
            print('Database is available!')
            return True
        except psycopg2.OperationalError as e:
            if i == max_retries - 1:
                print('Database connection failed after maximum retries')
                print(f'Error: {e}')
                return False
            print(f'Waiting for database... (attempt {i + 1}/{max_retries})')
            time.sleep(retry_delay)

if __name__ == '__main__':
    if not wait_for_db():
        sys.exit(1)
    sys.exit(0)
