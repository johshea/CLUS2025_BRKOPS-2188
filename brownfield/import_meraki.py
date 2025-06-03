import sys, subprocess
import os
from datetime import datetime
import import_meraki_vars


def ensure_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing missing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

ensure_package("meraki")
ensure_package("argparse")
ensure_package("pyyaml")

import meraki
import argparse
import yaml

###### End Module Imports ######

def parse_args():
    parser = argparse.ArgumentParser(description="Meraki API Script")
    parser.add_argument("--api_key", "-k", required=True, help="Your Meraki API Key")
    #parser.add_argument("--org_id", "-o", required=True, help="Meraki Organization ID")
    parser.add_argument("--org_name", "-n", required=False, help="Meraki Organization Name")
    return parser.parse_args()


args = parse_args()

dashboard = meraki.DashboardAPI(args.api_key, print_console=False, suppress_logging=True)

orgs = dashboard.organizations.getOrganizations()

for org in orgs:
    if org.get("name", "").lower() == args.org_name.lower():
        org_id = org.get("id")
        break

org = next((o for o in orgs if o['name'] == args.org_name), None)
if not org:
    print(f"Organization {args.org_name} not found.")



API_KEY = args.api_key
ORG_ID = org['id']
ORG_NAME = args.org_name
BASE_DIR = "./"
MODULES_DIR = os.path.join(BASE_DIR, "modules")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
YAML_DIR = os.path.join(OUTPUT_DIR, "yaml")


dashboard = meraki.DashboardAPI(API_KEY, print_console=False, suppress_logging=True)

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(MODULES_DIR, exist_ok=True)
os.makedirs(YAML_DIR, exist_ok=True)


#with open(f"{MODULES_DIR}/network/main.tf", "w") as f:
    #f.write(shared_module)

with open(os.path.join(BASE_DIR, "provider.tf"), "w") as f:
    f.write(import_meraki_vars.tf_provider)

with open(os.path.join(BASE_DIR, "variables.tf"), "w") as f:
    f.write(import_meraki_vars.tf_variables)

with open(os.path.join(BASE_DIR, "terraform.tfvars"), "w") as f:
    f.write(f'#api_key = "<insert your API key if needed>"\n')
    f.write(f'org_id = "{ORG_ID}"\n')


main_tf_path = os.path.join(BASE_DIR, "main.tf")
with open(main_tf_path, "w") as main_tf:

    #get org Level Data
    ORGS = dashboard.organizations.getOrganizations()

    # Find the org with the matching ID
    ORG_NAME = next((o for o in ORGS if o["id"] == ORG_ID), None)
    org_safe_name = ORG_NAME["name"].replace(" ", "_").replace("/", "_")
    org_data_path = os.path.join(org_safe_name, "Organization")

    org_data = {
        "name": ORG_NAME,
        "devices": [],
        "dns_profiles": [],
        "dns_assignments": [],
        "dns_splitprofiles": [],
        "dns_splitassignments": [],
        "dns_localrecords": [],
        "webhook_Receivers": []


    }

    os.makedirs(YAML_DIR + '/' + org_data_path, exist_ok=True)


    org_devices = dashboard.organizations.getOrganizationDevices(ORG_ID)

    yaml_file = f"{YAML_DIR}/{org_data_path}/Organization.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(org_devices, f, sort_keys=False)

    networks = dashboard.organizations.getOrganizationNetworks(ORG_ID)
    print(f"🔍 Found {len(networks)} networks...")

    for net in networks:
        net_id = net["id"]
        net_name = net["name"]
        net_safe_name = net_name.replace(" ", "_").replace("/", "_")

        os.makedirs(YAML_DIR + '/' + org_safe_name + '/' + net_safe_name, exist_ok=True)

        network_data = {
            "network": net,
            "devices": [],
            "vlans": [],
            "ssids": [],
            "firewallRules": [],
            "switchPorts": [],
            "wirelessSettings": [],
            "webhook_receivers": [],
            "alert_settings": []
        }

        yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_net_settings.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(net, f, sort_keys=False)

        try:
            for device in org_devices:
                if device["networkId"] == net["id"]:
                    network_data["devices"].append({
                        "networkId": device["networkId"],
                        "productType": device["productType"],
                        "model": device["model"],
                        "mac": device["mac"],
                        "serial": device["serial"],
                        "firmware": device["firmware"],
                        "address": device["address"]
                    })

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_devices.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["devices"], f, sort_keys=False)

        except: pass




        try:
            network_data["vlans"] = dashboard.appliance.getNetworkApplianceVlans(net_id)

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_mx_vlans.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["vlans"], f, sort_keys=False)
        except: pass

        try:
            network_data["webhook_receivers"] = dashboard.networks.getNetworkWebhooksHttpServers(net_id)

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_webhook_receivers.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["webhook_receivers"], f, sort_keys=False)
        except: pass

        try:
            network_data["alert_settings"] = dashboard.networks.getNetworkAlertsSettings(net_id)

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_alert_settings.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["alert_settings"], f, sort_keys=False)
        except: pass

        try:
            network_data["ssids"] = dashboard.wireless.getNetworkWirelessSsids(net_id)

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_ssids.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["ssids"], f, sort_keys=False)
        except: pass

        try:
            fw = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(net_id)
            network_data["firewallRules"] = fw.get("rules", [])

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_firewallrules.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["firewallRules"], f, sort_keys=False)
        except: pass

        try:
            for device in network_data["devices"]:
                if "switch" in device.get("productType", "").lower():
                    ports = dashboard.switch.getDeviceSwitchPorts(device["serial"])
                    network_data["switchPorts"].append({
                        "serial": device["serial"],
                        "ports": ports
                    })

            yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}/{net_safe_name}_{net_id}_switchPorts.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["switchPorts"], f, sort_keys=False)
        except: pass

        try:
            network_data["wirelessSettings"] = dashboard.wireless.getNetworkWirelessSettings(net_id)
        except: pass

        yaml_file = f"{YAML_DIR}/{org_safe_name}/{net_safe_name}_{net_id}.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(network_data, f,  sort_keys=False)

        module_dir = os.path.join(MODULES_DIR, net_safe_name)
        os.makedirs(module_dir, exist_ok=True)

        with open(f"{module_dir}/main.tf", "w") as f:
            f.write(f'#module "{net_safe_name}" \n ')
            f.write(f'locals {{ \n network = yamldecode(file("../.{YAML_DIR}/{org_safe_name}/{net_safe_name}_{net_id}.yaml"))\n')
            f.write(f' ssid = {{for ssid in local.network["ssids"] : ssid.number => ssid}}\n')
            f.write(f' mxvlan = {{for vlan in local.network["vlans"] : vlan.vlan_id => vlan}}\n}}')
            f.write(f'{import_meraki_vars.shared_module} \n ')

        with open(f"{module_dir}/provider.tf", "w") as f:
            f.write(import_meraki_vars.tf_provider)

        with open(f"{module_dir}/variables.tf", "w") as f:
            f.write(import_meraki_vars.tf_variables)

        with open(f"{module_dir}/locals.tf", "w") as f:
                    f.write(f'''locals {{ \n #network = yamldecode(file("{YAML_DIR}/{net_safe_name}_{net_id}.yaml"))
                    }}
            ''')

        with open(f"{module_dir}/terraform.tfvars", "w") as f:
            f.write(f'#api_key = "<insert API Key if needed>"\n')
            f.write(f'org_id = "{ORG_ID}"\n')

        #main_tf.write(f'''module "{safe_name}" {{
  #source      = "./modules/{safe_name}"
  #api_key     = var.api_key
#}}

#''')

        print(f"✅ Generated: {net_safe_name} ({net_id})")

try:
    print("\n🔧 Running terraform init...")
    os.system(f"terraform -chdir={BASE_DIR} init")

    print("\n🔧 Running terraform fmt...")
    os.system(f"terraform -chdir={BASE_DIR} fmt")

    print("✅ Running terraform validate...")
    os.system(f"terraform -chdir={BASE_DIR} validate || echo 'Validation completed with warnings/errors'")
except: pass
