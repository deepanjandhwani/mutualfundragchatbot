#!/usr/bin/env bash
# Build frontend for Vercel: inject API_BASE_URL into config and copy to public/.
# Set API_BASE_URL in Vercel project Environment Variables to your backend URL (e.g. https://mutualfundrag-backend.onrender.com).

set -e
API_BASE_URL="${API_BASE_URL:-}"
# Escape for use inside double quotes in JS
ESCAPED=$(echo "$API_BASE_URL" | sed 's/\\/\\\\/g; s/"/\\"/g')
mkdir -p public
echo "const API_BASE_URL = \"$ESCAPED\";" > phase5_frontend/config.js
cp -r phase5_frontend/. public/
echo "Built public/ with API_BASE_URL=${API_BASE_URL:-(empty)}"
