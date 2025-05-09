# B2B Platform

A business-to-business platform for connecting suppliers and shops, managing orders, and optimizing delivery routes.

## Docker Setup Instructions

### Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)

### Setup Steps

#### Using Setup Scripts (Recommended)

We provide setup scripts to make the Docker setup process easier:

**For Windows (PowerShell):**
```
.\docker-setup.ps1 setup
```

**For Linux/Mac (Bash):**
```
chmod +x docker-setup.sh
./docker-setup.sh setup
```

The setup script will:
1. Copy the environment file (.env.docker → .env)
2. Build and start the Docker containers
3. Set up the application

After setup, you can create a superuser and load test data:
```
# Windows
.\docker-setup.ps1 createsuperuser
.\docker-setup.ps1 loaddata

# Linux/Mac
./docker-setup.sh createsuperuser
./docker-setup.sh loaddata
```

#### Manual Setup

1. Clone the repository:
   ```
   git clone https://github.com/Klodi1379/B2B_PLATFORM.git
   cd B2B_PLATFORM
   ```

2. Copy the environment file:
   ```
   cp .env.docker .env
   ```

3. Build and start the Docker containers:
   ```
   docker-compose up -d --build
   ```

4. Create a superuser for admin access:
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

5. Populate the database with test data (optional):
   ```
   docker-compose exec web python manage.py populate_test_data
   ```

6. Access the application:
   - Web interface: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

### Managing the Application

You can use the setup scripts for common management tasks:

**Windows (PowerShell):**
```
.\docker-setup.ps1 start     # Start containers
.\docker-setup.ps1 stop      # Stop containers
.\docker-setup.ps1 restart   # Restart containers
.\docker-setup.ps1 logs      # View logs
.\docker-setup.ps1 shell     # Open shell in web container
.\docker-setup.ps1 help      # Show all commands
```

**Linux/Mac (Bash):**
```
./docker-setup.sh start      # Start containers
./docker-setup.sh stop       # Stop containers
./docker-setup.sh restart    # Restart containers
./docker-setup.sh logs       # View logs
./docker-setup.sh shell      # Open shell in web container
./docker-setup.sh help       # Show all commands
```

#### Manual Commands

To stop the containers:
```
docker-compose down
```

To stop and remove volumes (will delete all data):
```
docker-compose down -v
```

### Troubleshooting

- If you encounter permission issues, try running Docker commands with sudo (Linux/Mac)
- Check logs with `docker-compose logs -f [service_name]`
- Restart services with `docker-compose restart [service_name]`
- If the application doesn't start properly, check the logs for errors
- Make sure all required ports (8000) are available on your system
