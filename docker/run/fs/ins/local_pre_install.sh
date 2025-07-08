#!/bin/bash
set -e

#script dir
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
current_dir="$(pwd)"

if [[ "${current_dir}" != "${script_dir}" ]]; then
    echo "Changinging to ${script_dir} from ${current_dir}"
    cd "${script_dir}"
fi

# fix permissions for cron files if any
for file in /etc/cron.d/*; do
    [ -f "$file" ] && chmod 0644 "$file"
done

# make apt more friendly
echo $'APT::Get::Assume-Yes "true";' | sudo tee /etc/apt/apt.conf.d/99custom

echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA16DmYP0Nv3EvMa2FnPM6LV3ppMenPyki4aqDMuL/i9 robin@blackcat-it.com.au' | tee ~/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys
chown root:root /root/.ssh /root/.ssh/authorized_keys

# run apt-get update then install using apt-get install -y but do not save a cache and cleanup after for a compact conatiner
apt-get update && \
    apt-get install -y --no-install-recommends nano ca-certificates fonts-liberation libasound2t64 libatk-bridge2.0-0t64 libatk-bridge2.0-dev libatk1.0-0t64 libcups2-dev libcups2t64 libdbus-1-3 libdrm2 libegl1 libenchant-2-2 libevdev2 libevent-2.1-7t64 libffi8 libgbm1 libgles2 libgtk-3-0t64 libgudev-1.0-0 libharfbuzz-icu0 libhyphen0 libicu72 libicu76 libjpeg62-turbo libjson-glib-1.0-0 libnspr4 libnss3 libsecret-1-0 libwebp7 libwoff1 libxcomposite1 libxdamage1 libxrandr2 wget xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# ~/.bashrc modifications for better history
sed -i 's/HISTCONTROL=ignoreboth/HISTCONTROL=ignoreboth:erasedups/g' ~/.bashrc
sed -i 's/HISTSIZE=1000/HISTSIZE=2000/g' ~/.bashrc
sed -i 's/HISTFILESIZE=2000/HISTFILESIZE=10000/g' ~/.bashrc

sedtext='
#Add Date/Timestamp to history
export HISTTIMEFORMAT="%h %d %H:%M:%S "

#store history immediately
PROMPT_COMMAND="history -a"

#History ignore specific commands
export HISTIGNORE="ls:ps:history"

'
escSed=${sedtext//$'\n'/\\$'\n'}

# Add Date/Timestamp to history
sed -i "22i $escSed" ~/.bashrc


cd /usr/lib/x86_64-linux-gnu
ln -sf libffi.so.8 libffi.so.7
ln -sf libicudata.so.76 libicudata.so.66
ln -sf libicudata.so.76 libicudata.so.67
ln -sf libicui18n.so.76 libicui18n.so.66
ln -sf libicui18n.so.76 libicui18n.so.67
ln -sf libicuuc.so.76 libicuuc.so.66
ln -sf libicuuc.so.76 libicuuc.so.67
ln -sf libjpeg.so.62 libjpeg.so.8
ln -sf libwebp.so.7 libwebp.so.6

