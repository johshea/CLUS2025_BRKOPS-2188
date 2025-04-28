#!/bin/bash

API_KEY="$MERAKI_DASHBOARD_API_KEY"
ORG_ID="$1"

if [ -z "$ORG_ID" ]; then
  echo "Usage: ./fetch_meraki_inventory.sh <ORG_ID>"
  exit 1
fi

BASE_URL="https://api.meraki.com/api/v1"

mkdir -p fetched_inventory

echo "Fetching networks..."
curl -s -H "X-Cisco-Meraki-API-Key: $API_KEY" "$BASE_URL/organizations/$ORG_ID/networks" | jq '.' > fetched_inventory/networks.json

echo "Fetching devices..."
curl -s -H "X-Cisco-Meraki-API-Key: $API_KEY" "$BASE_URL/organizations/$ORG_ID/devices" | jq '.' > fetched_inventory/devices.json

jq -r '.[] | select(.model | startswith("MS")) | .serial' fetched_inventory/devices.json | while read SERIAL; do
  echo "Fetching ports for $SERIAL..."
  curl -s -H "X-Cisco-Meraki-API-Key: $API_KEY" "$BASE_URL/devices/$SERIAL/switchPorts" | jq '.' > "fetched_inventory/${SERIAL}_ports.json"
done

echo "✅ Inventory fetch complete."
