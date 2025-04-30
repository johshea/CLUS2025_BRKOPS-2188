#!/bin/bash

set -euo pipefail

# Configuration
API_KEY="${MERAKI_API_KEY:?Set MERAKI_API_KEY in env}"
BASE_URL="https://api.meraki.com/api/v1"
HEADERS=(
  -H "Content-Type: application/json"
  -H "Accept: application/json"
  -H "X-Cisco-Meraki-API-Key: ${API_KEY}"
)

# Step 1: Get the organization
echo "🔍 Fetching organization ID..."
org_id=$(curl -s "${HEADERS[@]}" "$BASE_URL/organizations" | jq -r '.[0].id')
echo "✅ Found organization: $org_id"

# Import the organization (requires manually defining a placeholder in your main.tf)
echo "📦 Importing organization..."
terraform import meraki_organization.example "$org_id"

# Step 2: Get networks
echo "🔍 Fetching networks..."
networks=$(curl -s "${HEADERS[@]}" "$BASE_URL/organizations/$org_id/networks")

echo "📦 Importing networks..."
for row in $(echo "$networks" | jq -r '.[] | @base64'); do
  _jq() {
    echo "$row" | base64 --decode | jq -r "$1"
  }

  net_id=$(_jq '.id')
  net_name=$(_jq '.name' | tr -cd '[:alnum:]_-' | tr ' ' '_')

  echo "  → Importing network $net_name ($net_id)"
  terraform import "meraki_network.${net_name}" "$net_id"
done

# Step 3: Get devices
echo "🔌 Fetching and importing devices..."
devices=$(curl -s "${HEADERS[@]}" "$BASE_URL/organizations/$org_id/devices")
for row in $(echo "$devices" | jq -r '.[] | @base64'); do
  _jq() {
    echo "$row" | base64 --decode | jq -r "$1"
  }

  serial=$(_jq '.serial')
  name=$(_jq '.name' | tr -cd '[:alnum:]_-' | tr ' ' '_')
  resource_name=${name:-device_$serial}

  echo "  → Importing device $resource_name ($serial)"
  terraform import "meraki_device.${resource_name}" "$serial"
done

# Step 4: Import appliance uplink settings per network
echo "🌐 Importing appliance uplinks..."
for net_id in $(echo "$networks" | jq -r '.[].id'); do
  resource_name="uplinks_${net_id}"
  echo "  → Importing appliance uplinks for $net_id"
  terraform import "meraki_appliance_uplinks_settings.${resource_name}" "$net_id"
done

# Step 5: Import SSIDs per network (0-14)
echo "📶 Importing SSIDs..."
for net_id in $(echo "$networks" | jq -r '.[].id'); do
  for i in {0..14}; do
    resource_name="ssid_${net_id}_${i}"
    echo "  → Importing SSID $i for network $net_id"
    terraform import "meraki_ssid.${resource_name}" "$net_id:$i" || echo "    (skipped – not defined)"
  done
done

echo "✅ All imports completed."
