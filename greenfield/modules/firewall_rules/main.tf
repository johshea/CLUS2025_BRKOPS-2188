resource "meraki_networks_appliance_firewall_l3_firewall_rules" "rules" {
  network_id           = var.network_id
  rules                = var.firewall_rules
  syslog_default_rule  = var.syslog_default_rule
}
