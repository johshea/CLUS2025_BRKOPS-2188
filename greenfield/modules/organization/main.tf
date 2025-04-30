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

resource "meraki_organization" "this" {
  organization_id = var.org_id
}

data "meraki_organization_networks" "all" {
  organization_id = var.org_id
}

data "meraki_organization_devices" "all" {
  organization_id = var.org_id
}
