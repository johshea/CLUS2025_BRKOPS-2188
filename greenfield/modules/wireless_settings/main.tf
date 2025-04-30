terraform {
  required_providers {
    meraki = {
      source = "cisco-open/meraki"
      version = "1.1.2-beta"
    }
  }
}

provider "meraki" {
  api_key = var.api_key
}

resource "meraki_networks_wireless_settings" "settings" {
  network_id                 = var.network_id
  meshing_enabled            = var.meshing_enabled
  ipv6_bridge_enabled        = var.ipv6_bridge_enabled
  location_analytics_enabled = var.location_analytics_enabled
  led_lights_on              = var.led_lights_on
  upgrade_strategy           = var.upgrade_strategy
}
