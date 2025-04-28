resource "meraki_organization" "this" {
  organization_id = var.org_id
}

data "meraki_organization_networks" "all" {
  organization_id = var.org_id
}

data "meraki_organization_devices" "all" {
  organization_id = var.org_id
}
