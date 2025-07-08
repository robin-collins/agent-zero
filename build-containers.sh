#!/bin/bash

# Agent Zero Container Build Script
# This script builds both base and run containers for Agent Zero
# Compatible with GitHub Actions workflow and local development

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_REGISTRY="ghcr.io"
DEFAULT_REPOSITORY="agent-zero"
DEFAULT_BRANCH="main"
DEFAULT_PLATFORMS="linux/amd64,linux/arm64"
BUILD_BASE=true
BUILD_RUN=true
PUSH_IMAGES=false
LOCAL_BUILD=false
VERBOSE=false
CLEAN_BUILD=false
BUILD_ARGS=""

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

# Function to print help
print_help() {
    cat << EOF
Agent Zero Container Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    -r, --registry REGISTRY     Container registry (default: ghcr.io)
    -R, --repository REPO       Repository name (default: agent-zero)
    -b, --branch BRANCH         Git branch to build from (default: main)
    -p, --platforms PLATFORMS   Target platforms (default: linux/amd64,linux/arm64)
    --base-only                 Build only base image
    --run-only                  Build only run image
    --push                      Push images to registry
    --local                     Build for local platform only
    --clean                     Clean build (no cache)
    --verbose                   Verbose output
    --build-arg KEY=VALUE       Add build argument
    -h, --help                  Show this help message

EXAMPLES:
    # Build both images locally
    $0 --local

    # Build and push both images
    $0 --push

    # Build only base image for local development
    $0 --base-only --local

    # Build with custom registry and repository
    $0 --registry my-registry.com --repository my-repo --push

    # Build with custom build arguments
    $0 --build-arg CACHE_DATE=\$(date +%s) --build-arg BRANCH=feature-branch

    # Clean build for production
    $0 --clean --push

ENVIRONMENT VARIABLES:
    REGISTRY        Override default registry
    REPOSITORY      Override default repository
    BRANCH          Override default branch
    PLATFORMS       Override default platforms
    GITHUB_TOKEN    GitHub token for registry authentication
    DOCKER_USERNAME Docker username for registry authentication
    DOCKER_PASSWORD Docker password for registry authentication

EOF
}

# Function to validate prerequisites
validate_prerequisites() {
    print_status "Validating prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        exit 1
    fi
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we're in the correct directory
    if [[ ! -f "docker/base/Dockerfile" ]] || [[ ! -f "docker/run/Dockerfile" ]]; then
        print_error "Must be run from the Agent Zero root directory"
        print_error "Expected directory structure: docker/base/Dockerfile and docker/run/Dockerfile"
        exit 1
    fi
    
    # Check if buildx is available for multi-platform builds
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        if ! docker buildx version &> /dev/null; then
            print_warning "Docker buildx not available, falling back to local build"
            LOCAL_BUILD=true
        fi
    fi
    
    print_success "Prerequisites validated"
}

# Function to setup Docker buildx
setup_buildx() {
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        print_status "Setting up Docker buildx..."
        
        # Create and use a new builder instance
        docker buildx create --name agent-zero-builder --use --bootstrap || true
        
        # Enable QEMU for multi-platform builds
        if command -v docker-run &> /dev/null; then
            docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true
        fi
        
        print_success "Docker buildx setup completed"
    fi
}

# Function to authenticate with registry
authenticate_registry() {
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        print_status "Authenticating with registry: $REGISTRY"
        
        if [[ -n "$GITHUB_TOKEN" ]]; then
            echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$GITHUB_ACTOR" --password-stdin
        elif [[ -n "$DOCKER_USERNAME" ]] && [[ -n "$DOCKER_PASSWORD" ]]; then
            echo "$DOCKER_PASSWORD" | docker login "$REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
        else
            print_warning "No authentication credentials provided"
            print_warning "You may need to run 'docker login $REGISTRY' manually"
        fi
    fi
}

# Function to get current git information
get_git_info() {
    # Get current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    
    # Get current commit hash
    CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # Get current timestamp
    CURRENT_DATE=$(date +%s)
    
    # Use provided branch or current branch
    if [[ -z "$BRANCH" ]]; then
        BRANCH="$CURRENT_BRANCH"
    fi
    
    print_status "Git info - Branch: $BRANCH, Commit: $CURRENT_COMMIT"
}

# Function to generate image tags
generate_tags() {
    local image_name="$1"
    local base_tag="$REGISTRY/$REPOSITORY-$image_name"
    
    # Always include branch-specific tag
    TAGS="$base_tag:$BRANCH"
    
    # Add commit-specific tag
    if [[ "$CURRENT_COMMIT" != "unknown" ]]; then
        TAGS="$TAGS,$base_tag:$BRANCH-$CURRENT_COMMIT"
    fi
    
    # Add latest tag if building from main branch
    if [[ "$BRANCH" == "main" ]]; then
        TAGS="$TAGS,$base_tag:latest"
    fi
    
    echo "$TAGS"
}

# Function to build base image
build_base_image() {
    print_status "Building base image..."
    
    local tags=$(generate_tags "base")
    local build_cmd="docker"
    
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        build_cmd="docker buildx"
    fi
    
    # Prepare build arguments
    local build_args="--build-arg CACHE_DATE=$CURRENT_DATE"
    if [[ -n "$BUILD_ARGS" ]]; then
        build_args="$build_args $BUILD_ARGS"
    fi
    
    # Prepare cache arguments
    local cache_args=""
    if [[ "$CLEAN_BUILD" == "false" ]]; then
        cache_args="--cache-from type=local,src=/tmp/.buildx-cache-base --cache-to type=local,dest=/tmp/.buildx-cache-base"
    fi
    
    # Build command
    local cmd="$build_cmd build"
    cmd="$cmd --context docker/base"
    cmd="$cmd --file docker/base/Dockerfile"
    cmd="$cmd --tag $tags"
    cmd="$cmd $build_args"
    
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        cmd="$cmd --platform $PLATFORMS"
    fi
    
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        cmd="$cmd --push"
    else
        cmd="$cmd --load"
    fi
    
    if [[ "$CLEAN_BUILD" == "false" ]] && [[ "$LOCAL_BUILD" == "false" ]]; then
        cmd="$cmd $cache_args"
    fi
    
    # Execute build
    print_status "Executing: $cmd"
    eval "$cmd"
    
    print_success "Base image built successfully"
    return 0
}

# Function to build run image
build_run_image() {
    print_status "Building run image..."
    
    local tags=$(generate_tags "run")
    local build_cmd="docker"
    
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        build_cmd="docker buildx"
    fi
    
    # Prepare build arguments
    local build_args="--build-arg BRANCH=$BRANCH --build-arg CACHE_DATE=$CURRENT_DATE"
    if [[ -n "$BUILD_ARGS" ]]; then
        build_args="$build_args $BUILD_ARGS"
    fi
    
    # Prepare cache arguments
    local cache_args=""
    if [[ "$CLEAN_BUILD" == "false" ]]; then
        cache_args="--cache-from type=local,src=/tmp/.buildx-cache-run --cache-to type=local,dest=/tmp/.buildx-cache-run"
    fi
    
    # Build command
    local cmd="$build_cmd build"
    cmd="$cmd --context docker/run"
    cmd="$cmd --file docker/run/Dockerfile"
    cmd="$cmd --tag $tags"
    cmd="$cmd $build_args"
    
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        cmd="$cmd --platform $PLATFORMS"
    fi
    
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        cmd="$cmd --push"
    else
        cmd="$cmd --load"
    fi
    
    if [[ "$CLEAN_BUILD" == "false" ]] && [[ "$LOCAL_BUILD" == "false" ]]; then
        cmd="$cmd $cache_args"
    fi
    
    # Execute build
    print_status "Executing: $cmd"
    eval "$cmd"
    
    print_success "Run image built successfully"
    return 0
}

# Function to cleanup buildx
cleanup_buildx() {
    if [[ "$LOCAL_BUILD" == "false" ]]; then
        print_status "Cleaning up buildx..."
        docker buildx rm agent-zero-builder || true
    fi
}

# Function to show build summary
show_summary() {
    print_status "Build Summary:"
    echo "  Registry: $REGISTRY"
    echo "  Repository: $REPOSITORY"
    echo "  Branch: $BRANCH"
    echo "  Commit: $CURRENT_COMMIT"
    echo "  Platforms: $PLATFORMS"
    echo "  Base image: $BUILD_BASE"
    echo "  Run image: $BUILD_RUN"
    echo "  Push images: $PUSH_IMAGES"
    echo "  Local build: $LOCAL_BUILD"
    echo "  Clean build: $CLEAN_BUILD"
    
    if [[ "$BUILD_BASE" == "true" ]]; then
        echo "  Base image tags: $(generate_tags 'base')"
    fi
    
    if [[ "$BUILD_RUN" == "true" ]]; then
        echo "  Run image tags: $(generate_tags 'run')"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -R|--repository)
            REPOSITORY="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -p|--platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --base-only)
            BUILD_BASE=true
            BUILD_RUN=false
            shift
            ;;
        --run-only)
            BUILD_BASE=false
            BUILD_RUN=true
            shift
            ;;
        --push)
            PUSH_IMAGES=true
            shift
            ;;
        --local)
            LOCAL_BUILD=true
            PLATFORMS="linux/$(uname -m)"
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            set -x
            shift
            ;;
        --build-arg)
            BUILD_ARGS="$BUILD_ARGS --build-arg $2"
            shift 2
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

# Set defaults from environment variables
REGISTRY="${REGISTRY:-$DEFAULT_REGISTRY}"
REPOSITORY="${REPOSITORY:-$DEFAULT_REPOSITORY}"
BRANCH="${BRANCH:-$DEFAULT_BRANCH}"
PLATFORMS="${PLATFORMS:-$DEFAULT_PLATFORMS}"

# Main execution
main() {
    print_status "Starting Agent Zero container build process..."
    
    # Validate prerequisites
    validate_prerequisites
    
    # Get git information
    get_git_info
    
    # Show build summary
    show_summary
    
    # Setup buildx if needed
    setup_buildx
    
    # Authenticate with registry if pushing
    authenticate_registry
    
    # Build base image if requested
    if [[ "$BUILD_BASE" == "true" ]]; then
        build_base_image
    fi
    
    # Build run image if requested
    if [[ "$BUILD_RUN" == "true" ]]; then
        build_run_image
    fi
    
    # Cleanup
    cleanup_buildx
    
    print_success "All builds completed successfully!"
    
    if [[ "$PUSH_IMAGES" == "true" ]]; then
        print_success "Images pushed to registry: $REGISTRY"
    else
        print_success "Images built locally and tagged appropriately"
    fi
    
    # Show final tags
    if [[ "$BUILD_BASE" == "true" ]]; then
        print_success "Base image tags: $(generate_tags 'base')"
    fi
    
    if [[ "$BUILD_RUN" == "true" ]]; then
        print_success "Run image tags: $(generate_tags 'run')"
    fi
}

# Error handling
trap 'print_error "Build failed at line $LINENO"; cleanup_buildx; exit 1' ERR

# Run main function
main "$@"