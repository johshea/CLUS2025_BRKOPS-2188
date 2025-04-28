

data "meraki_networks" "all" {
  organization_id = var.organization_id
}

resource "meraki_network" "network" {
  name            = "Enterprise Network"
  organization_id = var.organization_id
  type            = ["appliance", "switch", "wireless"]
  timezone        = "America/Los_Angeles"
}