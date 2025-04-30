import meraki
import yaml
import os
from datetime import datetime

API_KEY = '0d77b7587c8bd599209f01dbc2c89bdba00d6b96'
ORG_ID = '625437398251079063'
BASE_DIR = "./"
MODULES_DIR = os.path.join(BASE_DIR, "modules")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
YAML_DIR = os.path.join(OUTPUT_DIR, "yaml")

dashboard = meraki.DashboardAPI(API_KEY, print_console=False)

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(MODULES_DIR, exist_ok=True)
os.makedirs(YAML_DIR, exist_ok=True)

shared_module = '''
variable "config_file" { type = string }

locals {
  config = yamldecode(file(var.config_file))
}

resource "meraki_network" "this" {
  name            = local.config.network.name
  type            = local.config.network.type
  timezone        = local.config.network.timeZone
  tags            = try(local.config.network.tags, [])
  organization_id = local.config.network.organizationId
}
'''

#with open(f"{MODULES_DIR}/network/main.tf", "w") as f:
    #f.write(shared_module)

with open(os.path.join(BASE_DIR, "provider.tf"), "w") as f:
    f.write('''terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
       version = "1.1.2-beta"
    }
  }
}

provider "meraki" {
  api_key = var.api_key
}
''')

with open(os.path.join(BASE_DIR, "variables.tf"), "w") as f:
    f.write('''variable "api_key" {
  type        = string
  description = "Meraki Dashboard API key"
}
''')

with open(os.path.join(BASE_DIR, "terraform.tfvars"), "w") as f:
    f.write(f'api_key = "{API_KEY}"\n')
    f.write(f'org_id = "{ORG_ID}"\n')


main_tf_path = os.path.join(BASE_DIR, "main.tf")
with open(main_tf_path, "w") as main_tf:

    networks = dashboard.organizations.getOrganizationNetworks(ORG_ID)
    print(f"🔍 Found {len(networks)} networks...")

    for net in networks:
        net_id = net["id"]
        net_name = net["name"]
        safe_name = net_name.replace(" ", "_").replace("/", "_")

        network_data = {
            "network": net,
            "devices": [],
            "vlans": [],
            "ssids": [],
            "firewallRules": [],
            "switchPorts": [],
            "wirelessSettings": {}
        }

        try:
            network_data["devices"] = dashboard.networks.getNetworkDevices(net_id)
        except: pass
        try:
            network_data["vlans"] = dashboard.appliance.getNetworkApplianceVlans(net_id)
        except: pass
        try:
            network_data["ssids"] = dashboard.wireless.getNetworkWirelessSsids(net_id)
        except: pass
        try:
            fw = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(net_id)
            network_data["firewallRules"] = fw.get("rules", [])
        except: pass
        try:
            for device in network_data["devices"]:
                if "switch" in device.get("model", "").lower():
                    ports = dashboard.switch.getDeviceSwitchPorts(device["serial"])
                    network_data["switchPorts"].append({
                        "serial": device["serial"],
                        "ports": ports
                    })
        except: pass
        try:
            network_data["wirelessSettings"] = dashboard.wireless.getNetworkWirelessSettings(net_id)
        except: pass

        yaml_file = f"{YAML_DIR}/{safe_name}_{net_id}.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(network_data, f, sort_keys=False)

        module_dir = os.path.join(MODULES_DIR, safe_name)
        os.makedirs(module_dir, exist_ok=True)

        with open(f"{module_dir}/main.tf", "w") as f:
            f.write(f'''#module "{safe_name}" ''')

        with open(f"{module_dir}/provider.tf", "w") as f:
            f.write('''terraform {
  required_providers {
    meraki = {
      source  = "cisco-open/meraki"
       version = "1.1.2-beta"
    }
  }
}

provider "meraki" {
  api_key = var.api_key
}
''')

        with open(f"{module_dir}/variables.tf", "w") as f:
            f.write('''variable "api_key" {
  type        = string
  description = "API key for Meraki provider"
}
''')

        with open(f"{module_dir}/terraform.tfvars", "w") as f:
            f.write(f'api_key = {API_KEY}\n')
            f.write(f'org_id = {ORG_ID}\n')

        #main_tf.write(f'''module "{safe_name}" {{
  #source      = "./modules/{safe_name}"
  #api_key     = var.api_key
#}}

#''')

        print(f"✅ Generated: {safe_name} ({net_id})")

print("\n🔧 Running terraform init...")
os.system(f"terraform -chdir={BASE_DIR} init")

print("\n🔧 Running terraform fmt...")
os.system(f"terraform -chdir={BASE_DIR} fmt")

print("✅ Running terraform validate...")
os.system(f"terraform -chdir={BASE_DIR} validate || echo 'Validation completed with warnings/errors'")

