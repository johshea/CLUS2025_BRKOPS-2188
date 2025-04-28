
resource "meraki_networks_appliance_vlans" "vlan" {
  for_each = { for v in var.vlans : v.id => v }

  network_id   = var.network_id
  vlan_id      = each.value.id
  name         = each.value.name
  subnet       = each.value.subnet
  appliance_ip = each.value.appliance_ip
}
