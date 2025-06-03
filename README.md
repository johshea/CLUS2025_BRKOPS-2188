# Cisco Live 2025 IaC

## Installing Terraform
[Terraform Install Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

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
## Brownfield
- The entire brownfield scaffolding (terraform, modules, data ...) will be created the first time by running
  the import_meraki.py script found in the directory. To execute:
  ''''python3 import_meraki.py --api_key <yourApiKey> --org_name <yourOrgName>''''

- Once created you will have a fully functional terraform environment based on your actual data.
  - Terraform init is completed by the script
  - Terraform plan
  - Terraform apply
 
## Scripts
- `tfstate_to_yaml.py - converst a Json based Terraform state file to a yaml file for use in other platforms.

## Workspaces
- The entire brownfield scaffolding (terraform, modules, data ...) will be created the first time by running
  the import_meraki.py script found in the directory. To execute:
  ''''python3 import_meraki_workspace.py --api_key <<yourApiKey>> --org_name <<yourOrgName>> --output_dir ./''''

  - Once created you will have a fully functional terraform environment based on your actual data with each network found created as a  workspace.

  - Additionally the ***generate_imports.py*** script can be run to create the appropriate per network imports for syncing the supported data to your workspace state file.

