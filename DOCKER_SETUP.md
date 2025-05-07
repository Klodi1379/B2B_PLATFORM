# Docker Setup for B2B Platform

This document provides detailed information about the Docker setup for the B2B Platform application.

## Files Created for Docker Setup

1. **Dockerfile** - Defines the container image for the application
2. **docker-compose.yml** - Orchestrates the multi-container setup
3. **docker-entrypoint.sh** - Script that runs when the container starts
4. **.dockerignore** - Specifies files to exclude from the Docker build
5. **.env.docker** - Template for environment variables
6. **docker-setup.ps1** - PowerShell script for Windows users
7. **docker-setup.sh** - Bash script for Linux/Mac users
8. **requirements.txt** - Python dependencies

## Architecture

The Docker setup consists of the following services:

1. **web** - Django application running with Gunicorn
2. **redis** - Message broker for Celery
3. **celery** - Background task worker
4. **celery-beat** - Scheduled task scheduler

## Configuration

The application is configured using environment variables defined in the `.env` file. A template is provided in `.env.docker`.

Key configuration options:
- `DEBUG` - Set to False in production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hostnames
- `SECRET_KEY` - Django secret key
- `CELERY_BROKER_URL` - Redis connection URL
- `GRAPHHOPPER_API_KEY`, `OPENROUTE_API_KEY`, `GOOGLE_MAPS_API_KEY` - API keys for route optimization

## Data Persistence

The following Docker volumes are used for data persistence:
- `static_volume` - Static files
- `media_volume` - User-uploaded media files
- `redis_data` - Redis data

## Health Checks

A health check endpoint is available at `/health/` that reports the status of:
- Database connection
- Redis connection
- Application information

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Quick Setup (Using Scripts)

For Windows (PowerShell):
```
.\docker-setup.ps1 setup
```

For Linux/Mac (Bash):
```
chmod +x docker-setup.sh
./docker-setup.sh setup
```

### Manual Setup

1. Clone the repository
2. Copy `.env.docker` to `.env`
3. Build and start containers: `docker-compose up -d --build`
4. Create superuser: `docker-compose exec web python manage.py createsuperuser`
5. Load test data: `docker-compose exec web python manage.py populate_test_data`

## Common Tasks

### Accessing the Application
- Web interface: http://localhost:8000
- Admin interface: http://localhost:8000/admin

### Container Management
- Start containers: `docker-compose up -d`
- Stop containers: `docker-compose down`
- View logs: `docker-compose logs -f`
- Restart containers: `docker-compose restart`
- Access shell: `docker-compose exec web /bin/bash`

### Database Management
- Run migrations: `docker-compose exec web python manage.py migrate`
- Create superuser: `docker-compose exec web python manage.py createsuperuser`
- Load test data: `docker-compose exec web python manage.py populate_test_data`

## Troubleshooting

### Common Issues

1. **Port conflicts**
   - Error: "Bind for 0.0.0.0:8000 failed: port is already in use"
   - Solution: Stop the service using port 8000 or change the port in docker-compose.yml

2. **Permission issues**
   - Error: "Permission denied" when running Docker commands
   - Solution: Use sudo (Linux/Mac) or run PowerShell as Administrator (Windows)

3. **Redis connection issues**
   - Error: "Error connecting to Redis"
   - Solution: Check that Redis service is running and CELERY_BROKER_URL is correct

4. **Static files not loading**
   - Error: 404 errors for CSS/JS files
   - Solution: Run `docker-compose exec web python manage.py collectstatic --noinput`

### Viewing Logs

To view logs for a specific service:
```
docker-compose logs -f [service_name]
```

Where [service_name] is one of: web, redis, celery, celery-beat

## Production Considerations

For production deployment, consider:

1. Using a production-grade database like PostgreSQL
2. Setting up HTTPS with a reverse proxy (Nginx)
3. Implementing proper backup strategies
4. Setting up monitoring and alerting
5. Using Docker Swarm or Kubernetes for orchestration
