resource "meraki_device" "this" {
  serial          = var.device.serial
  network_id      = var.device.network_id
  address         = var.device.address
  notes           = var.device.notes
  move_map_marker = var.device.move_map_marker
  tags            = var.device.tags
  latitude        = var.device.latitude
  longitude       = var.device.longitude
  name            = var.device.name
}
