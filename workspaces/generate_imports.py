#!/usr/bin/env python3
"""
generate_imports.py

Reads terraform.tfvars to map each sanitized network name to its Meraki network ID,
then processes data/<network>/*.yaml and writes a separate import script for each network:
  import_<network_name>.sh

Each script contains `terraform import` commands for SSIDs, firewall rules, webhook servers,
alerts, MX VLANs, and switch VLANs for that specific network. The generated shell scripts
are marked executable via os.chmod(..., 0o755).
"""

import os
import re
import yaml
import sys

def parse_network_id_map(tfvars_path="terraform.tfvars"):
    """
    Parse terraform.tfvars and return a dict: {sanitized_network_name: network_id}.
    Expects lines like:
        "mark_z4c_t" = "L_123456789012345"
    """
    if not os.path.isfile(tfvars_path):
        print(f"Error: {tfvars_path} not found.", file=sys.stderr)
        sys.exit(1)

    mapping = {}
    content = open(tfvars_path).read()
    pattern = re.compile(r'"([^"]+)"\s*=\s*"([^"]+)"')
    for name, net_id in pattern.findall(content):
        mapping[name] = net_id
    return mapping

def generate_import_commands_for_network(net_name, net_id):
    """
    Generate a list of import commands for a single network:
      - SSIDs
      - Firewall rules
      - Webhook servers
      - Alerts
      - VLANs (MX)
    """
    commands = []
    base_module = f"module.{net_name}"
    data_dir = os.path.join("data", net_name)

    # 1. SSIDs
    ssid_file = os.path.join(data_dir, "ssids.yaml")
    if os.path.isfile(ssid_file):
        ssids = yaml.safe_load(open(ssid_file)) or []
        for s in ssids:
            number = s.get("number")
            if number is not None:
                addr = f"{base_module}.module.ssids.meraki_networks_wireless_ssids.this[\"{number}\"]"
                id_val = f"{net_id},{number}"
                commands.append(f"terraform import '{addr}' {id_val}")

    # 2. MX Firewall rules (L3)
    #fw_addr = f"{base_module}.module.firewall.meraki_networks_appliance_firewall_l3_firewall_rules.this"
    #commands.append(f"terraform import '{fw_addr}' {net_id}")

    # 3. Webhook servers
    webhook_file = os.path.join(data_dir, "webhook_servers.yaml")
    if os.path.isfile(webhook_file):
        webhooks = yaml.safe_load(open(webhook_file)) or []
        for w in webhooks:
            webhook_id = w.get("id")
            if webhook_id:
                addr = f"{base_module}.module.webhooks.meraki_networks_webhooks_http_servers.this[\"{webhook_id}\"]"
                id_val = f"{net_id},{webhook_id}"
                commands.append(f"terraform import '{addr}' {id_val}")

    # 4. Alert settings
    alert_addr = f"{base_module}.module.alerts.meraki_networks_alerts_settings.this"
    commands.append(f"terraform import '{alert_addr}' {net_id}")

    # 5. VLANs from MX firewall
    vlan_mx_file = os.path.join(data_dir, "vlans_mx.yaml")
    if os.path.isfile(vlan_mx_file):
        vlans_mx = yaml.safe_load(open(vlan_mx_file)) or []
        for v in vlans_mx:
            vid = v.get("id")
            if vid is not None:
                addr = f"{base_module}.module.vlans_mx.meraki_networks_appliance_vlans.this[\"{vid}\"]"
                id_val = f"{net_id},{vid}"
                commands.append(f"terraform import '{addr}' {id_val}")

    return commands

def write_import_script(net_name, commands):
    """
    Write a shell script named import_<net_name>.sh containing the import commands,
    then set the executable bit on the file.
    """
    filename = f"import_{net_name}.sh"
    with open(filename, "w") as f:
        f.write("#!/usr/bin/env bash\n")
        f.write(f"# Import script for network: {net_name}\n")
        f.write("set -euo pipefail\n\n")
        #f.write("# ← Export your Meraki API key once here\n")
        #f.write('export TF_VAR_meraki_api_key="YOUR API KEY HERE"\n\n')
        for cmd in commands:
            f.write(cmd + "\n")
    # set the executable bit:
    os.chmod(filename, 0o755)
    print(f"Generated import script: {filename}")

def main():
    network_id_map = parse_network_id_map()
    if not network_id_map:
        print("No networks found in terraform.tfvars.", file=sys.stderr)
        sys.exit(1)

    for net_name, net_id in network_id_map.items():
        commands = generate_import_commands_for_network(net_name, net_id)
        if commands:
            write_import_script(net_name, commands)
        else:
            print(f"No YAML data found for network '{net_name}'. Skipping import script generation.", file=sys.stderr)

if __name__ == "__main__":
    main()
