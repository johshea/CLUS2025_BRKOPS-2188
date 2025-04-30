
locals {
  network = yamldecode(file("./network_${var.network_name}/network.yaml"))
  device_serials = yamldecode(file("./network_${var.network_name}/devices.yaml"))

  serials_from_devices = [for s in local.device_serials.devices : s.serial]
  all_serials = distinct(concat(local.serials_from_devices))
}

// Create a new Network
resource "meraki_networks" "network" {
  organization_id = var.org_id
  product_types   = local.network["product_types"]
  tags            = local.network["tags"]
  name            = local.network["name"]
  time_zone        = local.network["timezone"]
  notes           = local.network["notes"]
}


// claim hardware into the network
resource "meraki_networks_devices_claim" "network_serials" {
  parameters = {serials = sensitive(local.all_serials)}
      #parameters = {serials = sensitive(local.network["serials"])}
  network_id = meraki_networks.network.id
}


