#!/bin/bash
# Runs once on first boot. Installs Docker + Compose, clones the repo,
# and starts the full stack. Logs to /var/log/user-data.log for debugging
# if something goes wrong (SSH in and check that file first).
set -e
exec > >(tee /var/log/user-data.log) 2>&1

echo "=== Updating packages ==="
apt-get update -y

echo "=== Installing Docker ==="
apt-get install -y ca-certificates curl gnupg git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "=== Enabling Docker ==="
systemctl enable docker
systemctl start docker

echo "=== Cloning repository ==="
cd /home/ubuntu
git clone ${repo_url} app
cd app

echo "=== Starting application stack ==="
docker compose up -d --build

echo "=== Done. Application should be reachable shortly. ==="
