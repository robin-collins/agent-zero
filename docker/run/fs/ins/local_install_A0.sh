#!/bin/bash
set -e

# Exit immediately if a command exits with a non-zero status.
# set -e

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

echo "INFO: Using local copy of repository instead of cloning from branch $BRANCH."
# The files are expected to be copied into /git/agent-zero by the Dockerfile.

. "/ins/setup_venv.sh" "$@"

# moved to base image
# # Ensure the virtual environment and pip setup
# pip install --upgrade pip ipython requests
# # Install some packages in specific variants
# pip install torch --index-url https://download.pytorch.org/whl/cpu

echo ================================================================================================================
echo ================================================================================================================
cat /git/agent-zero/requirements.txt
echo ================================================================================================================
echo ================================================================================================================

# Install remaining A0 python packages
uv pip install -r /git/agent-zero/requirements.txt

