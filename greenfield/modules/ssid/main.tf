locals {
  wifissids  = yamldecode(file("./network_${var.network_name}/ssids.yaml"))

 ssids = local.wifissids["ssids"]
  wifi_ssids = flatten([for ssid in local.ssids :
    {
      "number"                 = ssid.number
      "name"                   = ssid.name
      "auth_mode"              = ssid.auth_mode
      "encryption_mode"        = ssid.encryption_mode
      "wpa_encryption_mode"    = ssid.wpa_encryption_mode
      "psk"                    = ssid.psk
      "ip_assignment_mode"     = ssid.ip_assignment_mode
      "default_vlan_id"        = ssid.default_vlan_id
      "adult_content_filtering_enabled" = ssid.adult_content_filtering_enabled
      "use_vlan_tagging" = ssid.use_vlan_tagging
      "enabled" =  ssid.enabled
      "lan_isolation_enabled" = ssid.lan_isolation_enabled
    }
    ])


}

//deploy SSIDs
resource "meraki_networks_wireless_ssids" "all_ssids" {
  for_each = {
    for ssid in local.wifi_ssids : ssid.number => ssid
  }
  provider                        = meraki
  network_id                      = var.network_id
  number                          = each.value.number
  name                            = each.value.name
  auth_mode                       = each.value.auth_mode
  encryption_mode                 = each.value.encryption_mode
  wpa_encryption_mode             = each.value.wpa_encryption_mode
  psk                             = each.value.psk
  ip_assignment_mode              = each.value.ip_assignment_mode
  default_vlan_id                 = each.value.default_vlan_id
  adult_content_filtering_enabled = each.value.adult_content_filtering_enabled
  use_vlan_tagging                = each.value.use_vlan_tagging
  enabled                         = each.value.enabled
  lan_isolation_enabled           = each.value.lan_isolation_enabled
}
