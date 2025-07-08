#!/bin/bash

# Agent Zero Quick Start Script
# Build and run Agent Zero for local development in one command

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_help() {
    cat << EOF
Agent Zero Quick Start Script

Usage: $0 [OPTIONS]

OPTIONS:
    --build-only        Build images but don't run
    --run-only          Run existing image without building
    --port PORT         Port to run on (default: 50001)
    --clean             Clean build
    --verbose           Verbose output
    -h, --help          Show this help

EXAMPLES:
    # Build and run (default)
    $0

    # Build only
    $0 --build-only

    # Run on different port
    $0 --port 8080

    # Clean build and run
    $0 --clean

EOF
}

# Default settings
BUILD=true
RUN=true
PORT=50001
CLEAN_FLAG=""
VERBOSE_FLAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD=true
            RUN=false
            shift
            ;;
        --run-only)
            BUILD=false
            RUN=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --clean)
            CLEAN_FLAG="--clean"
            shift
            ;;
        --verbose)
            VERBOSE_FLAG="--verbose"
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Agent Zero Quick Start"
    
    # Build if requested
    if [[ "$BUILD" == "true" ]]; then
        print_status "Building Agent Zero containers..."
        ./build-local.sh $CLEAN_FLAG $VERBOSE_FLAG
    fi
    
    # Run if requested
    if [[ "$RUN" == "true" ]]; then
        print_status "Starting Agent Zero on port $PORT..."
        
        # Stop any existing container
        docker stop agent-zero-dev 2>/dev/null || true
        docker rm agent-zero-dev 2>/dev/null || true
        
        # Get the current branch for the image tag
        BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "local")
        IMAGE_TAG="localhost:5000/agent-zero-run:$BRANCH"
        
        # Create work directory if it doesn't exist
        mkdir -p work_dir
        
        # Run the container
        docker run -d \
            --name agent-zero-dev \
            -p "$PORT:80" \
            -v "$(pwd)/work_dir:/a0/work_dir" \
            -v "$(pwd)/logs:/a0/logs" \
            -e ENVIRONMENT=development \
            "$IMAGE_TAG"
        
        # Wait a moment for startup
        sleep 3
        
        # Check if container is running
        if docker ps | grep -q agent-zero-dev; then
            print_success "Agent Zero is running!"
            print_success "Access at: http://localhost:$PORT"
            print_status "Container name: agent-zero-dev"
            print_status "Logs: docker logs -f agent-zero-dev"
            print_status "Stop: docker stop agent-zero-dev"
        else
            print_error "Failed to start Agent Zero"
            print_error "Check logs: docker logs agent-zero-dev"
            exit 1
        fi
    fi
}

# Error handling
trap 'print_error "Quick start failed at line $LINENO"; exit 1' ERR

# Run main
main "$@"