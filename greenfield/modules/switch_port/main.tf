resource "meraki_devices_switch_ports" "port" {
  for_each = { for p in var.ports : "${p.device_serial}:${p.port_id}" => p }

  device_serial    = each.value.device_serial
  port_id          = each.value.port_id
  name             = lookup(each.value, "name", null)
  tags             = lookup(each.value, "tags", null)
  enabled          = lookup(each.value, "enabled", true)
  type             = lookup(each.value, "type", "access")
  vlan             = lookup(each.value, "vlan", null)
  voice_vlan       = lookup(each.value, "voice_vlan", null)
  allowed_vlans    = lookup(each.value, "allowed_vlans", "all")
  poe_enabled      = lookup(each.value, "poe_enabled", true)
  isolation_enabled = lookup(each.value, "isolation_enabled", false)
  rstp_enabled     = lookup(each.value, "rstp_enabled", true)
  stp_guard        = lookup(each.value, "stp_guard", "disabled")
}
