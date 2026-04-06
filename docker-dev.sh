#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="mvs"
DEFAULT_SERVICE="app"

compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "Error: docker compose is not installed." >&2
    exit 1
  fi
}

wait_for_docker() {
  local retries=60
  local sleep_s=2

  echo "Waiting for Docker engine to become ready..."
  for ((i=1; i<=retries; i++)); do
    if docker version >/dev/null 2>&1; then
      echo "Docker engine is ready."
      return 0
    fi
    sleep "$sleep_s"
  done

  echo "Error: Docker engine did not become ready in time." >&2
  echo "Tip: Start Docker Desktop and ensure Linux containers mode is enabled." >&2
  return 1
}

build() {
  wait_for_docker
  echo "Building images for project: ${PROJECT_NAME}"
  compose build
}

up() {
  wait_for_docker
  echo "Starting containers in detached mode..."
  compose up --build -d
  compose ps
}

status() {
  wait_for_docker
  compose ps
}

logs() {
  wait_for_docker
  compose logs -f --tail=200
}

shell() {
  wait_for_docker
  local service="${1:-$DEFAULT_SERVICE}"
  echo "Opening shell in service: ${service}"
  compose exec "$service" bash
}

down() {
  wait_for_docker
  echo "Stopping containers..."
  compose down
}

usage() {
  cat <<'EOF'
Usage: ./docker-dev.sh <command> [args]

Commands:
  build               Build Docker images
  up                  Build (if needed) and start containers in detached mode
  status              Show running compose services
  logs                Follow compose logs
  shell [service]     Open bash shell in a running service (default: app)
  down                Stop and remove compose services

Examples:
  ./docker-dev.sh up
  ./docker-dev.sh shell app
  ./docker-dev.sh logs
EOF
}

main() {
  local cmd="${1:-help}"
  shift || true

  case "$cmd" in
    build) build "$@" ;;
    up) up "$@" ;;
    status) status "$@" ;;
    logs) logs "$@" ;;
    shell) shell "$@" ;;
    down) down "$@" ;;
    help|-h|--help) usage ;;
    *)
      echo "Unknown command: $cmd" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
