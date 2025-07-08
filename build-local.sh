#!/bin/bash

# Agent Zero Local Development Build Script
# Simplified script for local testing and development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGISTRY="local"
REPOSITORY="agent-zero"
BRANCH="local"
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
PLATFORM="linux/$(uname -m)"
BUILD_BASE=true
BUILD_RUN=true
VERBOSE=false
CLEAN=false
TAG_SUFFIX=""

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

print_help() {
    cat << EOF
Agent Zero Local Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    --base-only         Build only base image
    --run-only          Build only run image
    --clean             Clean build (no cache)
    --verbose           Verbose output
    --tag-suffix SUFFIX Add suffix to image tags
    -h, --help          Show this help

EXAMPLES:
    # Build both images for local testing
    $0

    # Build only base image
    $0 --base-only

    # Clean build with verbose output
    $0 --clean --verbose

    # Build with custom tag suffix
    $0 --tag-suffix "-dev"

QUICK START:
    # 1. Build images
    $0

    # 2. Run Agent Zero
    docker run -p 50001:80 local/agent-zero-run:latest

    # 3. Access at http://localhost:50001

EOF
}

# Validate we're in the right directory
validate_directory() {
    if [[ ! -f "docker/base/Dockerfile" ]] || [[ ! -f "docker/run/Dockerfile" ]]; then
        print_error "Must be run from Agent Zero root directory"
        print_error "Expected: docker/base/Dockerfile and docker/run/Dockerfile"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker not running"
        exit 1
    fi

    print_success "Prerequisites OK"
}

# Generate image tags
generate_tags() {
    local image_type="$1"
    local base_tag="$REGISTRY-$REPOSITORY-$image_type"

    echo "$base_tag:latest$TAG_SUFFIX"
}

# Build base image
build_base() {
    print_status "Building base image..."

    local tag=$(generate_tags "base")
    local cache_args=""

    if [[ "$CLEAN" == "false" ]]; then
        cache_args="--cache-from $tag"
    fi

    local cmd="docker build"
    cmd="$cmd --file docker/base/Dockerfile"
    cmd="$cmd --tag $tag"
    cmd="$cmd --build-arg CACHE_DATE=$(date +%s)"
    cmd="$cmd $cache_args"
    cmd="$cmd docker/base"

    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --progress=plain"
    fi

    print_status "Executing: $cmd"
    eval "$cmd"

    print_success "Base image built: $tag"
}

# Build run image
build_run() {
    print_status "Building run image..."

    local tag=$(generate_tags "run")
    local cache_args=""

    if [[ "$CLEAN" == "false" ]]; then
        cache_args="--cache-from $tag"
    fi

    local cmd="docker build"
    cmd="$cmd --file docker/run/Dockerfile.local"
    cmd="$cmd --tag $tag"
    cmd="$cmd --build-arg BRANCH=$BRANCH"
    cmd="$cmd --build-arg CACHE_DATE=$(date +%s)"
    cmd="$cmd $cache_args"
    cmd="$cmd ."

    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --progress=plain"
    fi

    print_status "Executing: $cmd"
    eval "$cmd"

    print_success "Run image built: $tag"
}

# Show usage instructions
show_usage() {
    print_success "Build completed!"
    echo
    print_status "Quick start commands:"

    if [[ "$BUILD_RUN" == "true" ]]; then
        local run_tag=$(generate_tags "run")
        echo "  # Run Agent Zero:"
        echo "  docker run -p 50001:80 $run_tag"
        echo
        echo "  # Run with volume mount:"
        echo "  docker run -p 50001:80 -v \$(pwd)/work_dir:/a0/work_dir $run_tag"
        echo
        echo "  # Access at: http://localhost:50001"
        echo
    fi

    if [[ "$BUILD_BASE" == "true" ]]; then
        local base_tag=$(generate_tags "base")
        echo "  # Base image for development:"
        echo "  docker run -it $base_tag /bin/bash"
        echo
    fi

    print_status "Available images:"
    docker images | grep "$REGISTRY-$REPOSITORY" | head -10
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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
        --clean)
            CLEAN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --tag-suffix)
            TAG_SUFFIX="$2"
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

# Main execution
main() {
    print_status "Agent Zero Local Build"
    print_status "Branch: $BRANCH, Commit: $COMMIT, Platform: $PLATFORM"

    validate_directory
    check_prerequisites

    # Build images
    if [[ "$BUILD_BASE" == "true" ]]; then
        build_base
    fi

    if [[ "$BUILD_RUN" == "true" ]]; then
        build_run
    fi

    show_usage
}

# Error handling
trap 'print_error "Build failed at line $LINENO"; exit 1' ERR

# Run main
main "$@"