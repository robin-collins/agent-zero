#!/bin/bash
set -e

# activate venv
. "/ins/setup_venv.sh" "$@"

# install playwright if not installed (should be from requirements.txt)
uv pip install playwright

# set PW installation path to /a0/tmp/playwright
export PLAYWRIGHT_BROWSERS_PATH=/a0/tmp/playwright

# install chromium with dependencies
apt-get update
# apt-get install -y fonts-unifont
apt-get install -y libnss3 libnspr4 libxcomposite1 libxdamage1
playwright install chromium --only-shell
