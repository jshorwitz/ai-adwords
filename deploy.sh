#!/bin/bash
# AI AdWords Platform - Quick Deployment Script

set -e

echo "🚀 AI AdWords Platform Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_warning ".env file created from .env.example"
        print_warning "Please edit .env file with your settings before continuing"
        
        # Generate a secret key
        SECRET_KEY=$(openssl rand -base64 32)
        sed -i.bak "s/your-secret-key-change-in-production-minimum-32-characters/$SECRET_KEY/" .env
        
        print_success "Generated secure SECRET_KEY"
        print_warning "Please add your Google Ads API credentials to .env file"
        
        read -p "Press Enter to continue after editing .env file..."
    else
        print_success ".env file already exists"
    fi
}

# Build and start services
deploy_local() {
    print_status "Building and starting services..."
    
    # Pull latest images
    docker-compose pull
    
    # Build application
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    print_success "Services started successfully!"
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Application is healthy and ready!"
    else
        print_warning "Application might still be starting up..."
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec postgres pg_isready -U ads_user -d ai_adwords > /dev/null 2>&1; then
            print_success "PostgreSQL is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "PostgreSQL failed to start after $max_attempts attempts"
            exit 1
        fi
        
        print_status "Attempt $attempt/$max_attempts - PostgreSQL not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    # Initialize database tables and seed data
    docker-compose exec app python -m src.db_init
    
    print_success "Database initialized with tables and seed data"
}

# Test the deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Test health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ Health check passed"
    else
        print_error "❌ Health check failed"
        return 1
    fi
    
    # Test agent system
    if curl -f http://localhost:8000/agents/health > /dev/null 2>&1; then
        print_success "✅ Agent system healthy"
    else
        print_error "❌ Agent system unhealthy"
        return 1
    fi
    
    # Test agent list
    AGENT_COUNT=$(curl -s http://localhost:8000/agents/list | jq '. | length' 2>/dev/null || echo "0")
    if [ "$AGENT_COUNT" -gt "0" ]; then
        print_success "✅ $AGENT_COUNT agents registered"
    else
        print_warning "⚠️  No agents registered or API not responding"
    fi
    
    print_success "All tests passed!"
}

# Show final information
show_info() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "Your AI AdWords platform is running at:"
    echo "  🌐 Application: http://localhost:8000"
    echo "  📖 API Docs: http://localhost:8000/docs"
    echo "  🗄️  Database: localhost:5432"
    echo ""
    echo "Next steps:"
    echo "  1. Visit http://localhost:8000 to see the platform"
    echo "  2. Create an admin account at http://localhost:8000/auth/signup"
    echo "  3. Test the agent system with dry-run mode"
    echo "  4. Add your Google Ads API credentials to .env"
    echo ""
    echo "Useful commands:"
    echo "  docker-compose logs -f app    # View application logs"
    echo "  docker-compose logs -f postgres  # View database logs"
    echo "  docker-compose down           # Stop all services"
    echo "  docker-compose up -d          # Start services again"
    echo ""
}

# Main deployment function
main() {
    print_status "Starting AI AdWords Platform deployment..."
    
    # Parse command line arguments
    case "${1:-local}" in
        "local")
            print_status "Deploying locally with Docker..."
            check_docker
            setup_env
            deploy_local
            init_database
            test_deployment
            show_info
            ;;
        "test")
            print_status "Testing existing deployment..."
            test_deployment
            ;;
        "stop")
            print_status "Stopping services..."
            docker-compose down
            print_success "Services stopped"
            ;;
        "restart")
            print_status "Restarting services..."
            docker-compose down
            docker-compose up -d
            print_success "Services restarted"
            ;;
        "logs")
            docker-compose logs -f app
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  local (default)  Deploy locally with Docker"
            echo "  test            Test existing deployment"
            echo "  stop            Stop all services"
            echo "  restart         Restart all services"  
            echo "  logs            View application logs"
            echo "  help            Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended for Docker deployments"
fi

# Run main function
main "$@"
