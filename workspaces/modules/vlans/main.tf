

data "meraki_networks" "all" {
  organization_id = var.organization_id
}

resource "meraki_vlan" "vlan" {
  network_id   = data.meraki_networks.all.networks[0].id
  name         = "Enterprise VLAN"
  subnet       = "192.168.10.0/24"
  appliance_ip = "192.168.10.1"
}