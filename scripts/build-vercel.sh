#!/usr/bin/env bash
# Build frontend for Vercel: inject API_BASE_URL into config and copy to public/.
# Vercel env API_BASE_URL:
#   - https://YOUR-SERVICE.onrender.com — direct to Render (recommended; avoids proxy 502 on long cold starts)
#   - /api — same-origin; vercel.json rewrites /api/* to Render

set -e
API_BASE_URL="${API_BASE_URL:-/api}"
# Escape for use inside double quotes in JS
ESCAPED=$(echo "$API_BASE_URL" | sed 's/\\/\\\\/g; s/"/\\"/g')
mkdir -p public
echo "const API_BASE_URL = \"$ESCAPED\";" > phase5_frontend/config.js
cp -r phase5_frontend/. public/
echo "Built public/ with API_BASE_URL=${API_BASE_URL:-(empty)}"
