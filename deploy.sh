#!/usr/bin/env bash
set -euo pipefail

# deploy.sh - helper to stop an old deployment, copy backend .env, and start the new one
# Usage:
#   sudo ./deploy.sh --old-env /path/to/old/repo/backend/.env --repo /path/to/new/repo
# Environment variables (optional): OLD_ENV, REPO_DIR, SERVICE_NAME

print_usage() {
  cat <<EOF
Usage: sudo $0 --old-env /path/to/old/backend/.env --repo /path/to/new/repo [--service name]
Options:
  --old-env   Path to existing backend/.env to copy from
  --repo      Path to new repository root (where docker-compose.yml lives)
  --service   Optional systemd service name to stop
EOF
}

OLD_ENV=${OLD_ENV:-}
REPO_DIR=${REPO_DIR:-}
SERVICE_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --old-env)
      OLD_ENV="$2"; shift 2;;
    --repo)
      REPO_DIR="$2"; shift 2;;
    --service)
      SERVICE_NAME="$2"; shift 2;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown arg: $1"; print_usage; exit 1;;
  esac
done

if [[ -z "$OLD_ENV" || -z "$REPO_DIR" ]]; then
  echo "Missing required args." >&2
  print_usage
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (or via sudo)." >&2
  exit 1
fi

echo "Stopping likely old deployments..."

# Stop docker containers if docker exists
if command -v docker &> /dev/null; then
  echo "Stopping all docker containers (if any)..."
  docker ps -q | xargs -r docker stop || true
  docker ps -aq | xargs -r docker rm || true
fi

# Stop pm2 processes if pm2 exists
if command -v pm2 &> /dev/null; then
  echo "Stopping pm2 processes..."
  pm2 stop all || true
  pm2 delete all || true
fi

# Stop a systemd service if provided
if [[ -n "$SERVICE_NAME" ]]; then
  echo "Stopping systemd service $SERVICE_NAME if exists..."
  systemctl stop "$SERVICE_NAME" || true
  systemctl disable "$SERVICE_NAME" || true
fi

echo "Copying .env from $OLD_ENV to $REPO_DIR/backend/.env"
mkdir -p "$REPO_DIR/backend"
cp -f "$OLD_ENV" "$REPO_DIR/backend/.env"
chmod 600 "$REPO_DIR/backend/.env"

echo "Ensuring Docker and docker compose are installed..."
if ! command -v docker &> /dev/null; then
  echo "Installing docker..."
  apt-get update
  apt-get install -y ca-certificates curl gnupg lsb-release
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
fi

echo "Switching to repo: $REPO_DIR"
cd "$REPO_DIR"

if [[ -d .git ]]; then
  git fetch origin
  git checkout final || git checkout -b final
  git reset --hard origin/final || true
fi

echo "Bringing up docker compose services..."
if command -v docker &> /dev/null; then
  docker compose pull || true
  docker compose up -d --build
  echo "Done. Use 'docker compose ps' and 'docker compose logs -f' to inspect services."
else
  echo "Docker not available after install attempt. Check the logs." >&2
  exit 1
fi

exit 0
