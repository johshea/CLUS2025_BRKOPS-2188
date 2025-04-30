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


resource "meraki_networks_appliance_firewall_l3_firewall_rules" "rules" {
  network_id           = var.network_id
  rules                = var.firewall_rules
  syslog_default_rule  = var.syslog_default_rule
}
