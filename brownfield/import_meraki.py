import sys
import meraki
import yaml
import os
from datetime import datetime
import import_meraki_vars

API_KEY = '0d77b7587c8bd599209f01dbc2c89bdba00d6b96'
ORG_ID = '625437398251079063'
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

    networks = dashboard.organizations.getOrganizationNetworks(ORG_ID)
    print(f"🔍 Found {len(networks)} networks...")

    for net in networks:
        net_id = net["id"]
        net_name = net["name"]
        safe_name = net_name.replace(" ", "_").replace("/", "_")

        os.makedirs(YAML_DIR+'/'+safe_name, exist_ok=True)

        network_data = {
            "network": net,
            "devices": [],
            "vlans": [],
            "ssids": [],
            "firewallRules": [],
            "switchPorts": [],
            "wirelessSettings": {}
        }

        yaml_file = f"{YAML_DIR}/{safe_name}/{safe_name}_{net_id}_net_settings.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(net, f, sort_keys=False)

        #try:
            #network_data["devices"] = dashboard.networks.getNetworkDevices(net_id)
        #except: pass
        try:
            network_data["vlans"] = dashboard.appliance.getNetworkApplianceVlans(net_id)

            yaml_file = f"{YAML_DIR}/{safe_name}/{safe_name}_{net_id}_mx_vlans.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["vlans"], f, sort_keys=False)
        except: pass

        try:
            network_data["ssids"] = dashboard.wireless.getNetworkWirelessSsids(net_id)

            yaml_file = f"{YAML_DIR}/{safe_name}/{safe_name}_{net_id}_ssids.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["ssids"], f, sort_keys=False)
        except: pass

        try:
            fw = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(net_id)
            network_data["firewallRules"] = fw.get("rules", [])

            yaml_file = f"{YAML_DIR}/{safe_name}/{safe_name}_{net_id}_firewallrules.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["firewallRules"], f, sort_keys=False)
        except: pass

        try:
            for device in network_data["devices"]:
                if "switch" in device.get("model", "").lower():
                    ports = dashboard.switch.getDeviceSwitchPorts(device["serial"])
                    network_data["switchPorts"].append({
                        "serial": device["serial"],
                        "ports": ports
                    })

            yaml_file = f"{YAML_DIR}/{safe_name}/{safe_name}_{net_id}_switchPorts.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(network_data["switchPorts"], f, sort_keys=False)
        except: pass

        try:
            network_data["wirelessSettings"] = dashboard.wireless.getNetworkWirelessSettings(net_id)
        except: pass

        yaml_file = f"{YAML_DIR}/{safe_name}_{net_id}.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(network_data, f,  sort_keys=False)

        module_dir = os.path.join(MODULES_DIR, safe_name)
        os.makedirs(module_dir, exist_ok=True)

        with open(f"{module_dir}/main.tf", "w") as f:
            f.write(f'#module "{safe_name}" \n ')
            f.write(f'locals {{ \n network = yamldecode(file("../.{YAML_DIR}/{safe_name}_{net_id}.yaml"))\n')
            f.write(f' ssid = {{for ssid in local.network["ssids"] : ssid.number => ssid}}\n')
            f.write(f' mxvlan = {{for vlan in local.network["vlans"] : vlan.vlan_id => vlan}}\n}}')
            f.write(f'{import_meraki_vars.shared_module} \n ')

        with open(f"{module_dir}/provider.tf", "w") as f:
            f.write(import_meraki_vars.tf_provider)

        with open(f"{module_dir}/variables.tf", "w") as f:
            f.write(import_meraki_vars.tf_variables)

        with open(f"{module_dir}/locals.tf", "w") as f:
                    f.write(f'''locals {{ \n #network = yamldecode(file("{YAML_DIR}/{safe_name}_{net_id}.yaml"))
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

        print(f"✅ Generated: {safe_name} ({net_id})")

print("\n🔧 Running terraform init...")
os.system(f"terraform -chdir={BASE_DIR} init")

print("\n🔧 Running terraform fmt...")
os.system(f"terraform -chdir={BASE_DIR} fmt")

print("✅ Running terraform validate...")
os.system(f"terraform -chdir={BASE_DIR} validate || echo 'Validation completed with warnings/errors'")

