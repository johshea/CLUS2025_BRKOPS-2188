

resource "meraki_network" "this" {
  network_id       = var.network.id
  organization_id  = var.network.organization_id
  name             = var.network.name
  type             = join(",", var.network.product_types)
  timezone         = var.network.timezone
  tags             = var.network.tags
}
