

data "meraki_networks" "all" {
  organization_id = var.organization_id
}

resource "meraki_networks_wireless_ssids" "ssid" {
  network_id = data.meraki_networks.all.networks[0].id
  name       = "Enterprise WiFi"
  enabled    = true
  auth_mode  = "psk"
  psk        = "SuperSecurePass123!"
}