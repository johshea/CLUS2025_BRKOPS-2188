

resource "meraki_networks_wireless_ssids" "ssid" {
  for_each = { for s in var.ssids : s.number => s }

  network_id         = var.network_id
  number             = each.value.number
  name               = each.value.name
  enabled            = each.value.enabled
  auth_mode          = each.value.auth_mode
  ip_assignment_mode = each.value.ip_assignment_mode

  psk = each.value.auth_mode == "psk" ? each.value.psk : null
  default_vlan_id = each.value.ip_assignment_mode == "Bridge mode" ? each.value.default_vlan_id : null
  radius_servers = each.value.auth_mode == "8021x-radius" ? each.value.radius_servers : []
}
