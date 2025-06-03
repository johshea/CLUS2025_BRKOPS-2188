#!/usr/bin/env python3
"""
Production-ready script to discover a Meraki organization via the Meraki SDK,
export network data to YAML, and scaffold a Terraform project with workspaces,
modules, and root configuration files for managing Meraki resources.

Prerequisites:
    - Python 3.7+
    - Install dependencies:
        pip install meraki pyyaml

Usage:
    python meraki_to_terraform.py --api_key <YOUR_MERAKI_API_KEY> --org_name "<YOUR_ORG_NAME>" \
        [--output_dir ./meraki_tf_project]

The script will:
    1. Connect to the Meraki Dashboard API.
    2. List all organizations accessible by the API key, match the provided org_name,
       and retrieve its org_id.
    3. List all networks in the matched organization.
    4. For each network:
         - Fetch SSIDs, MX firewall rules, webhook servers, alert settings,
           VLANs from MX firewalls, VLANs from switches.
         - Write each service’s data as a YAML file under data/<network_sanitized>/.
    5. Scaffold a Terraform project under the output directory:
         - Create root files: provider.tf, variables.tf, terraform.tfvars, and a dynamically generated main.tf.
         - Create modules/shared_modules/<service> for each service with Terraform modules
           that read the YAML and provision Meraki resources, each containing a provider.tf.
         - Create modules/<network_sanitized> for each network, invoking shared modules, each containing a provider.tf.
    6. Remove any existing Terraform lock file and .terraform directory.
    7. Initialize Terraform (using `terraform init -upgrade` to regenerate lock file).
    8. Create a Terraform workspace for each network (named after sanitized network name).

After running:
    cd <output_dir>
    terraform workspace select <sanitized_network_name>
    terraform apply -target=module.<sanitized_network_name>
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import meraki
import yaml

# ----------------------------- Helper Functions ----------------------------- #

def sanitize_name(name: str) -> str:
    """
    Sanitize network names into safe Terraform workspace/module identifiers:
    lowercase, alphanumeric and underscores only, no leading digits.
    """
    sanitized = re.sub(r"[^A-Za-z0-9_]+", "_", name).lower()
    if re.match(r"^\d", sanitized):
        sanitized = f"net_{sanitized}"
    return sanitized

def write_yaml(data, path: Path) -> None:
    """
    Write a Python object to a file as YAML.
    """
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def ensure_directory(path: Path) -> None:
    """
    Create directory if it does not exist.
    """
    path.mkdir(parents=True, exist_ok=True)

def run_subprocess(cmd, cwd=None):
    """
    Run a subprocess command; print stderr if it fails.
    """
    try:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(cmd)}' failed with exit code {e.returncode}", file=sys.stderr)
        print(e.stderr.decode(), file=sys.stderr)

# --------------------------- Terraform File Templates --------------------------- #

# Updated root provider with version 1.1.3-beta
ROOT_PROVIDER_TF = """terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}
"""

ROOT_VARIABLES_TF = """variable "meraki_api_key" {
  description = "Meraki Dashboard API key"
  type        = string
  sensitive   = true
}

# Map of workspace (sanitized network name) to Meraki network ID
variable "network_id_map" {
  description = "Mapping of Terraform workspace names to Meraki network IDs"
  type        = map(string)
}
"""

SHARED_MODULE_PROVIDER_TF = """provider "meraki" {
  api_key = var.meraki_api_key
}
"""

SHARED_MODULE_VARIABLES_TF = """variable "network_id" {
  description = "The Meraki network ID"
  type        = string
}

variable "yaml_file" {
  description = "Path to the YAML file containing data for this module"
  type        = string
}

variable "meraki_api_key" {
  description = "Meraki Dashboard API key"
  type        = string
  sensitive   = true
}
"""

SHARED_MODULE_SSIDS_MAIN_TF = """
terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}

locals {
  ssids = yamldecode(file(var.yaml_file))
}

resource "meraki_networks_wireless_ssids" "this" {
  for_each        = { for s in local.ssids : s.number => s }
  network_id      = var.network_id
  number          = each.value.number
  name            = each.value.name
  enabled         = each.value.enabled
  auth_mode       = lookup(each.value, "authMode", null)
  encryption_mode = lookup(each.value, "encryptionMode", null)
  psk             = lookup(each.value, "psk", null)
}
"""

SHARED_MODULE_FIREWALL_MAIN_TF = """
terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}

locals {
  rules = yamldecode(file(var.yaml_file))
}

resource "meraki_networks_appliance_firewall_l3_firewall_rules" "this" {
  network_id = var.network_id
  rules      = local.rules
}
"""

SHARED_MODULE_WEBHOOKS_MAIN_TF = """
terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}

locals {
  webhooks = yamldecode(file(var.yaml_file))
}

resource "meraki_networks_webhooks_http_servers" "this" {
  for_each        = { for w in local.webhooks : w.id => w }
  network_id      = var.network_id
  name            = each.value.name
  url             = each.value.url
  shared_secret    = lookup(each.value, "sharedSecret", null)
  payload_template = lookup(each.value, "payloadTemplate", null)
}
"""

SHARED_MODULE_ALERTS_MAIN_TF = """
terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}

locals {
  data = yamldecode(file(var.yaml_file))
}

resource "meraki_networks_alerts_settings" "this" {
  network_id           = var.network_id
  default_destinations = local.data.defaultDestinations
  alerts               = local.data.alerts
}
"""

SHARED_MODULE_VLANS_MX_MAIN_TF = """
terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}

locals {
  vlans = yamldecode(file(var.yaml_file))
}

resource "meraki_networks_appliance_vlans" "this" {
  for_each          = { for v in local.vlans : v.id => v }
  network_id        = var.network_id
  id                = each.value.id
  name              = each.value.name
  subnet            = each.value.subnet
  appliance_ip      = each.value.applianceIp
}
"""


NETWORK_MODULE_PROVIDER_TF = """terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }
  }
}

provider "meraki" {
  meraki_dashboard_api_key = var.meraki_api_key
}
"""

# Each network-specific module only calls shared modules (no "count" on modules).
MODULE_NETWORK_MAIN_TF_TEMPLATE = """
terraform {{
  required_providers {{
    meraki = {{
      source  = "cisco-open/meraki"
      version = "1.1.3-beta"
    }}
  }}
}}

provider "meraki" {{
  meraki_dashboard_api_key = var.meraki_api_key
}}

module "ssids" {{
  source     = "../../modules/shared_modules/ssids"
  network_id = var.network_id
  yaml_file  = "./data/{net_name}/ssids.yaml"
  meraki_api_key = var.meraki_api_key
}}

#module "firewall" {{
  #source     = "../../modules/shared_modules/firewall"
  #network_id = var.network_id
  #yaml_file  = "./data/{net_name}/firewall_rules.yaml"
  #meraki_api_key = var.meraki_api_key
#}}

module "webhooks" {{
  source     = "../../modules/shared_modules/webhooks"
  network_id = var.network_id
  yaml_file  = "./data/{net_name}/webhook_servers.yaml"
  meraki_api_key = var.meraki_api_key
}}

module "alerts" {{
  source     = "../../modules/shared_modules/alerts"
  network_id = var.network_id
  yaml_file  = "./data/{net_name}/alerts.yaml"
  meraki_api_key = var.meraki_api_key
}}

module "vlans_mx" {{
  source     = "../../modules/shared_modules/vlans_mx"
  network_id = var.network_id
  yaml_file  = "./data/{net_name}/vlans_mx.yaml"
  meraki_api_key = var.meraki_api_key
}}

"""

# ----------------------------- Main Script Logic ----------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Generate Terraform project from Meraki org using Python and Meraki SDK"
    )
    parser.add_argument(
        "--api_key", "-k", required=True, help="Meraki Dashboard API key"
    )
    parser.add_argument(
        "--org_name", "-n", required=True, help="Name of the Meraki Organization"
    )
    parser.add_argument(
        "--output_dir",
        "-d",
        default="meraki_tf_project",
        help="Directory to generate Terraform project in",
    )
    args = parser.parse_args()

    api_key = args.api_key
    org_name = args.org_name
    output_dir = Path(args.output_dir).resolve()
    data_root = output_dir / "data"
    modules_root = output_dir / "modules"
    shared_modules_root = modules_root / "shared_modules"

    print(f"Looking up organization '{org_name}' using provided API key...")
    dashboard = meraki.DashboardAPI(api_key, output_log=False, print_console=False)

    try:
        orgs = dashboard.organizations.getOrganizations()
    except Exception as e:
        print(f"Error fetching organizations: {e}", file=sys.stderr)
        sys.exit(1)

    org_id = None
    for org in orgs:
        if org.get("name", "").lower() == org_name.lower():
            org_id = org.get("id")
            break

    if not org_id:
        print(f"Organization '{org_name}' not found. Available organizations:", file=sys.stderr)
        for org in orgs:
            print(f"  - {org.get('name')} (ID: {org.get('id')})", file=sys.stderr)
        sys.exit(1)

    print(f"Matched organization '{org_name}' → ID: {org_id}")
    print(f"Generating Terraform project in: {output_dir}")

    # Create base folders
    ensure_directory(output_dir)
    ensure_directory(data_root)
    ensure_directory(shared_modules_root)

    print(f"Fetching networks for organization ID {org_id}...")
    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
    except Exception as e:
        print(f"Error fetching networks: {e}", file=sys.stderr)
        sys.exit(1)

    # Build mapping: sanitized network name → network ID
    network_map = {}
    for net in networks:
        net_name = net.get("name", "")
        net_id = net.get("id")
        if not net_id or not net_name:
            continue
        sanitized = sanitize_name(net_name)
        if sanitized in network_map:
            sanitized = f"{sanitized}_{net_id}"
        network_map[sanitized] = net_id

    # Fetch data and write YAML for each network
    for sanitized, net_id in network_map.items():
        print(f"Processing network '{sanitized}' (ID: {net_id})")
        network_data_dir = data_root / sanitized
        ensure_directory(network_data_dir)

        # 1. SSID data
        try:

            ssids = dashboard.wireless.getNetworkWirelessSsids(net_id)

        except Exception:
            ssids = []
        write_yaml(ssids, network_data_dir / "ssids.yaml")

        # 2. MX Firewall rules (L3)
        try:
            fw_rules = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(net_id)
            fw_rules_list = fw_rules.get("rules", []) if isinstance(fw_rules, dict) else fw_rules
        except Exception:
            fw_rules_list = []
        write_yaml(fw_rules_list, network_data_dir / "firewall_rules.yaml")

        # 3. Webhook servers
        try:
            webhook_servers = dashboard.networks.getNetworkWebhooksHttpServers(net_id)
        except Exception:
            webhook_servers = []
        write_yaml(webhook_servers, network_data_dir / "webhook_servers.yaml")

        # 4. Alert settings
        try:
            alerts = dashboard.networks.getNetworkAlertsSettings(net_id)
        except Exception:
            alerts = {}
        write_yaml(alerts, network_data_dir / "alerts.yaml")

        # 5. VLANs from MX firewall
        try:
            vlans_mx = dashboard.appliance.getNetworkApplianceVlans(net_id)
        except Exception:
            vlans_mx = []
        write_yaml(vlans_mx, network_data_dir / "vlans_mx.yaml")


    # ------------------- Create Shared Modules ------------------- #
    print("Scaffolding shared Terraform modules for services...")
    services = {
        "ssids": SHARED_MODULE_SSIDS_MAIN_TF,
        "firewall": SHARED_MODULE_FIREWALL_MAIN_TF,
        "webhooks": SHARED_MODULE_WEBHOOKS_MAIN_TF,
        "alerts": SHARED_MODULE_ALERTS_MAIN_TF,
        "vlans_mx": SHARED_MODULE_VLANS_MX_MAIN_TF,
    }

    for svc_name, main_tf_content in services.items():
        svc_dir = shared_modules_root / svc_name
        ensure_directory(svc_dir)

        # variables.tf inside shared module
        with open(svc_dir / "variables.tf", "w") as f:
            f.write(SHARED_MODULE_VARIABLES_TF)

        # main.tf inside shared module
        with open(svc_dir / "main.tf", "w") as f:
            f.write(main_tf_content)

    # ------------------- Create Network-specific Modules ------------------- #
    print("Scaffolding Terraform modules for each network...")
    for sanitized, net_id in network_map.items():
        net_module_dir = modules_root / sanitized
        ensure_directory(net_module_dir)

        # Declare only the "network_id" variable inside this module's variables.tf
        with open(net_module_dir / "variables.tf", "w") as f:
            f.write('variable "network_id" {\n  description = "Meraki network ID"\n  type        = string\n}\n')
            f.write('variable "meraki_api_key" {\n description = "Meraki API key"\n  type        = string\n}\n')

        # main.tf invokes shared modules (no count)
        main_tf_filled = MODULE_NETWORK_MAIN_TF_TEMPLATE.format(net_name=sanitized)
        with open(net_module_dir / "main.tf", "w") as f:
            f.write(main_tf_filled)

    # ------------------- Create Root Terraform Files ------------------- #
    print("Writing root Terraform files (variables.tf, terraform.tfvars, main.tf)...")

    with open(output_dir / "variables.tf", "w") as f:
        f.write(ROOT_VARIABLES_TF)

    # Build the map literal for terraform.tfvars
    network_id_map_literal = "{\n"
    for sanitized, net_id in network_map.items():
        network_id_map_literal += f'  "{sanitized}" = "{net_id}"\n'
    network_id_map_literal += "}"

    with open(output_dir / "terraform.tfvars", "w") as f:
        f.write(f'network_id_map = {network_id_map_literal}\n')

    # Root main.tf: instantiate each module without count
    main_tf_lines = []
    for sanitized in network_map.keys():
        block = [
            f'module "{sanitized}" {{',
            f'  source     = "./modules/{sanitized}"',
            f'  network_id = var.network_id_map["{sanitized}"]',
            f'  meraki_api_key = var.meraki_api_key',
            f'}}',
            ""
        ]
        main_tf_lines.extend(block)

    with open(output_dir / "main.tf", "w") as f:
        f.write("\n" + ROOT_PROVIDER_TF + "\n".join(main_tf_lines))

    # ------------------- Clean up old Terraform state and lock files ------------------- #
    lockfile = output_dir / ".terraform.lock.hcl"
    if lockfile.exists():
        print("Removing existing Terraform lock file to avoid inconsistencies...")
        lockfile.unlink()

    terraform_dir = output_dir / ".terraform"
    if terraform_dir.exists():
        print("Removing existing .terraform directory to avoid inconsistencies...")
        shutil.rmtree(terraform_dir)

    # ------------------- Initialize Terraform and Create Workspaces ------------------- #
    print("Initializing Terraform (with –upgrade to regenerate lock file)...")
    run_subprocess(["terraform", "init", "-upgrade", "-input=false"], cwd=str(output_dir))

    print("Creating Terraform workspaces for each network...")
    for sanitized in network_map.keys():
        print(f"  - Workspace: {sanitized}")
        run_subprocess(["terraform", "workspace", "new", sanitized], cwd=str(output_dir))

    print("All workspaces created. Project scaffold complete.")
    print(
        f"""
Next steps:
  1. cd {output_dir}
  2. terraform workspace select <sanitized_network_name>
  3. terraform apply -target=module.<sanitized_network_name>

Example:
  terraform workspace select mark_z4c_t
  terraform apply -target=module.mark_z4c_t

By targeting a single module after selecting its workspace, only that network’s resources are created.
"""
    )


if __name__ == "__main__":
    main()

