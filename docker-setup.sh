#!/bin/bash

# Docker setup script for Linux/Mac

# Function to display help
show_help() {
    echo -e "\e[32mB2B Platform Docker Setup Script\e[0m"
    echo -e "\e[32m--------------------------------\e[0m"
    echo "Available commands:"
    echo "  setup     - Initial setup (copy env file, build and start containers)"
    echo "  start     - Start all containers"
    echo "  stop      - Stop all containers"
    echo "  restart   - Restart all containers"
    echo "  build     - Rebuild all containers"
    echo "  logs      - Show logs from all containers"
    echo "  shell     - Open a shell in the web container"
    echo "  createsuperuser - Create a Django superuser"
    echo "  loaddata  - Load test data into the database"
    echo "  help      - Show this help message"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "\e[31mDocker is not installed or not in PATH. Please install Docker.\e[0m"
        return 1
    fi
    return 0
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo -e "\e[31mDocker Compose is not installed or not in PATH.\e[0m"
        return 1
    fi
    return 0
}

# Function to setup the environment
initialize_environment() {
    if [ ! -f .env ]; then
        echo -e "\e[33mCopying .env.docker to .env...\e[0m"
        cp .env.docker .env
        echo -e "\e[32mEnvironment file created.\e[0m"
    else
        echo -e "\e[33m.env file already exists.\e[0m"
    fi
}

# Main script logic
if ! check_docker || ! check_docker_compose; then
    exit 1
fi

# Process command line arguments
command=$1

case $command in
    setup)
        initialize_environment
        echo -e "\e[33mBuilding and starting containers...\e[0m"
        docker-compose up -d --build
        echo -e "\e[32mSetup complete! The application is now running at http://localhost:8000\e[0m"
        ;;
    start)
        echo -e "\e[33mStarting containers...\e[0m"
        docker-compose up -d
        echo -e "\e[32mContainers started. The application is now running at http://localhost:8000\e[0m"
        ;;
    stop)
        echo -e "\e[33mStopping containers...\e[0m"
        docker-compose down
        echo -e "\e[32mContainers stopped.\e[0m"
        ;;
    restart)
        echo -e "\e[33mRestarting containers...\e[0m"
        docker-compose restart
        echo -e "\e[32mContainers restarted.\e[0m"
        ;;
    build)
        echo -e "\e[33mRebuilding containers...\e[0m"
        docker-compose up -d --build
        echo -e "\e[32mContainers rebuilt and started.\e[0m"
        ;;
    logs)
        docker-compose logs -f
        ;;
    shell)
        echo -e "\e[33mOpening shell in web container...\e[0m"
        docker-compose exec web /bin/bash
        ;;
    createsuperuser)
        echo -e "\e[33mCreating superuser...\e[0m"
        docker-compose exec web python manage.py createsuperuser
        ;;
    loaddata)
        echo -e "\e[33mLoading test data...\e[0m"
        docker-compose exec web python manage.py populate_test_data
        echo -e "\e[32mTest data loaded.\e[0m"
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "\e[31mUnknown command: $command\e[0m"
        show_help
        ;;
esac
