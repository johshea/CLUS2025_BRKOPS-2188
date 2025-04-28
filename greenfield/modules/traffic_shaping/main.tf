resource "meraki_networks_appliance_traffic_shaping" "global" {
  network_id = var.network_id
  global_bandwidth_limits = {
    limit_up   = var.default_client_bw_up
    limit_down = var.default_client_bw_down
  }
}

resource "meraki_networks_appliance_traffic_shaping_rules" "rules" {
  network_id            = var.network_id
  default_rules_enabled = var.default_rules_enabled
  rules = [for rule in var.shaping_rules : {
    definitions = rule.definitions
    per_client_bandwidth_limits = {
      settings = "custom"
      bandwidth_limits = {
        limit_up   = rule.per_client_bandwidth_limits.limit_up
        limit_down = rule.per_client_bandwidth_limits.limit_down
      }
    }
    dscp_tag_value = lookup(rule, "dscp_tag_value", null)
    priority       = lookup(rule, "priority", null)
  }]
}
