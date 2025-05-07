# Docker setup script for Windows PowerShell

# Function to display help
function Show-Help {
    Write-Host "B2B Platform Docker Setup Script" -ForegroundColor Green
    Write-Host "--------------------------------" -ForegroundColor Green
    Write-Host "Available commands:"
    Write-Host "  setup     - Initial setup (copy env file, build and start containers)"
    Write-Host "  start     - Start all containers"
    Write-Host "  stop      - Stop all containers"
    Write-Host "  restart   - Restart all containers"
    Write-Host "  build     - Rebuild all containers"
    Write-Host "  logs      - Show logs from all containers"
    Write-Host "  shell     - Open a shell in the web container"
    Write-Host "  createsuperuser - Create a Django superuser"
    Write-Host "  loaddata  - Load test data into the database"
    Write-Host "  help      - Show this help message"
}

# Function to check if Docker is installed
function Test-Docker {
    try {
        docker --version | Out-Null
        return $true
    }
    catch {
        Write-Host "Docker is not installed or not in PATH. Please install Docker Desktop." -ForegroundColor Red
        return $false
    }
}

# Function to check if Docker Compose is installed
function Test-DockerCompose {
    try {
        docker-compose --version | Out-Null
        return $true
    }
    catch {
        Write-Host "Docker Compose is not installed or not in PATH." -ForegroundColor Red
        return $false
    }
}

# Function to setup the environment
function Initialize-Environment {
    if (!(Test-Path .env)) {
        Write-Host "Copying .env.docker to .env..." -ForegroundColor Yellow
        Copy-Item .env.docker .env
        Write-Host "Environment file created." -ForegroundColor Green
    }
    else {
        Write-Host ".env file already exists." -ForegroundColor Yellow
    }
}

# Main script logic
if (!(Test-Docker) -or !(Test-DockerCompose)) {
    exit 1
}

# Process command line arguments
$command = $args[0]

switch ($command) {
    "setup" {
        Initialize-Environment
        Write-Host "Building and starting containers..." -ForegroundColor Yellow
        docker-compose up -d --build
        Write-Host "Setup complete! The application is now running at http://localhost:8000" -ForegroundColor Green
    }
    "start" {
        Write-Host "Starting containers..." -ForegroundColor Yellow
        docker-compose up -d
        Write-Host "Containers started. The application is now running at http://localhost:8000" -ForegroundColor Green
    }
    "stop" {
        Write-Host "Stopping containers..." -ForegroundColor Yellow
        docker-compose down
        Write-Host "Containers stopped." -ForegroundColor Green
    }
    "restart" {
        Write-Host "Restarting containers..." -ForegroundColor Yellow
        docker-compose restart
        Write-Host "Containers restarted." -ForegroundColor Green
    }
    "build" {
        Write-Host "Rebuilding containers..." -ForegroundColor Yellow
        docker-compose up -d --build
        Write-Host "Containers rebuilt and started." -ForegroundColor Green
    }
    "logs" {
        docker-compose logs -f
    }
    "shell" {
        Write-Host "Opening shell in web container..." -ForegroundColor Yellow
        docker-compose exec web /bin/bash
    }
    "createsuperuser" {
        Write-Host "Creating superuser..." -ForegroundColor Yellow
        docker-compose exec web python manage.py createsuperuser
    }
    "loaddata" {
        Write-Host "Loading test data..." -ForegroundColor Yellow
        docker-compose exec web python manage.py populate_test_data
        Write-Host "Test data loaded." -ForegroundColor Green
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $command" -ForegroundColor Red
        Show-Help
    }
}
