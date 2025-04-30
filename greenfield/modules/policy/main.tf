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

data "meraki_networks" "all" {
  organization_id = var.organization_id
}

resource "meraki_network_group_policy" "policy" {
  network_id = data.meraki_networks.all.networks[0].id
  name       = "Enterprise Policy"

  scheduling {
    enabled = false
  }
}