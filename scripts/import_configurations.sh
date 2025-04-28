#!/bin/bash

ORG_ID=$1

if [ -z "$ORG_ID" ]; then
  echo "Usage: ./import_configurations.sh <ORG_ID>"
  exit 1
fi

terraform init

echo "Importing organization..."
terraform import module.org.meraki_organization.this ${ORG_ID}

NETWORK_IDS=$(terraform console <<< 'join(" ", module.org.network_ids)')

for NETWORK_ID in ${NETWORK_IDS}; do
  echo "Importing network: ${NETWORK_ID}"
  terraform import "module.org.module.networks[\\\"${NETWORK_ID}\\\"].meraki_network.this" "${NETWORK_ID}"
done

DEVICE_IDS=$(terraform console <<< 'join(" ", module.org.device_ids)')

for DEVICE_ID in ${DEVICE_IDS}; do
  echo "Importing device: ${DEVICE_ID}"
  terraform import "module.org.module.devices[\\\"${DEVICE_ID}\\\"].meraki_device.this" "${DEVICE_ID}"
done

echo "✅ Import completed."
