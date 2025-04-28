#!/bin/bash

# Set your variables
MERAKI_API_KEY="your_api_key_here"
ORG_ID="your_org_id_here"

# Export for Terraform provider
export MERAKI_API_KEY

# Fetch all networks in the org
echo "Fetching networks..."
NETWORKS=$(curl -s -H "X-Cisco-Meraki-API-Key: $MERAKI_API_KEY" \
  https://api.meraki.com/api/v1/organizations/$ORG_ID/networks)

# Import each network
echo "$NETWORKS" | jq -c '.[]' | while read -r network; do
  NETWORK_ID=$(echo "$network" | jq -r '.id')
  NETWORK_NAME=$(echo "$network" | jq -r '.name' | tr ' ' '_' | tr -cd '[:alnum:]_')

  echo "Importing network: $NETWORK_NAME ($NETWORK_ID)"
  terraform import "meraki_network.${NETWORK_NAME}" "$NETWORK_ID"

  # Fetch devices for this network
  DEVICES=$(curl -s -H "X-Cisco-Meraki-API-Key: $MERAKI_API_KEY" \
    https://api.meraki.com/api/v1/networks/$NETWORK_ID/devices)

  echo "$DEVICES" | jq -c '.[]' | while read -r device; do
    DEVICE_SERIAL=$(echo "$device" | jq -r '.serial')
    DEVICE_NAME=$(echo "$device" | jq -r '.name // .serial' | tr ' ' '_' | tr -cd '[:alnum:]_')

    echo "Importing device: $DEVICE_NAME ($DEVICE_SERIAL)"
    terraform import "meraki_device_switch.${DEVICE_NAME}" "$DEVICE_SERIAL"
  done

  # Fetch VLANs for this network
  VLANS=$(curl -s -H "X-Cisco-Meraki-API-Key: $MERAKI_API_KEY" \
    https://api.meraki.com/api/v1/networks/$NETWORK_ID/vlans)

  echo "$VLANS" | jq -c '.[]' | while read -r vlan; do
    VLAN_ID=$(echo "$vlan" | jq -r '.id')
    VLAN_NAME=$(echo "$vlan" | jq -r '.name // .id' | tr ' ' '_' | tr -cd '[:alnum:]_')

    echo "Importing VLAN: $VLAN_NAME ($VLAN_ID)"
    terraform import "meraki_vlan.${VLAN_NAME}" "${NETWORK_ID}/${VLAN_ID}"
  done

done

echo "✅ Import complete."
