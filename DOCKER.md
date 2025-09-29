# Docker Setup for Library Management System

This document explains how to set up and run the Library Management System using Docker.

## Prerequisites

- Docker (v20.10.0 or higher)
- Docker Compose (v2.0.0 or higher)

## Getting Started

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd library_system
   ```

2. **Create a .env file** (optional, for local development):
   ```bash
   cp .env.example .env
   ```
   Then edit the .env file with your configuration.

## Running with Docker Compose

1. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

2. **Apply database migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create a superuser** (optional):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Access the application**:
   - Frontend: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## Common Commands

- **Start services in detached mode**:
  ```bash
  docker-compose up -d
  ```

- **View logs**:
  ```bash
  docker-compose logs -f
  ```

- **Run management commands**:
  ```bash
  docker-compose exec web python manage.py <command>
  ```

- **Run tests**:
  ```bash
  docker-compose exec web python manage.py test
  ```

- **Stop all services**:
  ```bash
  docker-compose down
  ```

- **Stop and remove all containers, networks, and volumes**:
  ```bash
  docker-compose down -v
  ```

## Development Workflow

1. The application code is mounted as a volume, so changes to your local files will be reflected in the container.
2. The development server will automatically reload when you make changes to Python files.
3. For production, you'll want to set `DEBUG=False` in your environment variables.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | 1 | Enable/disable debug mode |
| `SECRET_KEY` | (auto-generated) | Django secret key |
| `DB_NAME` | library_db | Database name |
| `DB_USER` | library_user | Database user |
| `DB_PASSWORD` | library_password | Database password |
| `DB_HOST` | db | Database host |
| `DB_PORT` | 5432 | Database port |

## Production Deployment

For production, you should:
1. Set `DEBUG=0`
2. Set a strong `SECRET_KEY`
3. Set proper database credentials
4. Set up a proper web server (Nginx, Apache) in front of Gunicorn
5. Set up proper SSL/TLS certificates
6. Configure proper logging
7. Set up backup and monitoring

## Troubleshooting

- If you get a port conflict, make sure no other services are using ports 8000, 5432, or 6379.
- If the database connection fails, make sure the PostgreSQL service is running and the credentials match.
- Check the logs with `docker-compose logs` for detailed error messages.
