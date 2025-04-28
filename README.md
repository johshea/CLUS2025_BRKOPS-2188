# Cisco Live 2025 IaC

## Overview
Manage an entire Cisco Meraki Organization with Terraform:
- Networks
- Devices
- SSIDs
- Firewall Rules
- Switch Ports
- VLANs
- Wireless Settings
- Traffic Shaping

## Setup
1. Configure your `terraform.tfvars`.
2. Run `terraform init`.
3. Use `import_configurations.sh` to import existing resources.
4. Apply with `terraform apply`.

## Scripts
- `import_configurations.sh`: imports org, networks, devices, etc.
- `fetch_meraki_inventory.sh`: fetches all devices/networks into JSONs.

## Examples
See `example_ssids.tfvars`, `example_firewall_rules.tfvars`, etc.
