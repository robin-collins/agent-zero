#!/bin/bash
set -e

#script dir
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
current_dir="$(pwd)"

echo "script dir: ${script_dir}"
echo "current dir: ${current_dir}"

cd "${script_dir}"
cp sshd_config /etc/ssh/sshd_config

cd "${current_dir}"

# Set up SSH
mkdir -p /var/run/sshd && \
    # echo 'root:toor' | chpasswd &&
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config