#!/usr/bin/env sh
set -eu

curl -fsS "${API_HEALTH_URL:-http://localhost:8000/health}"

